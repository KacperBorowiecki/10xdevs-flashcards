# API Endpoint Implementation Plan: Generate Flashcards from Text

## 1. Przegląd punktu końcowego

Endpoint `/ai/generate-flashcards` umożliwia użytkownikom przesłanie tekstu (1000-10000 znaków) w celu wygenerowania sugestii fiszek przez AI. System tworzy rekordy w tabelach `source_texts`, `flashcards` (ze statusem `pending_review`) oraz `ai_generation_events`, a następnie zwraca listę wygenerowanych fiszek oczekujących na zatwierdzenie przez użytkownika.

## 2. Szczegóły żądania

- **Metoda HTTP**: POST
- **Struktura URL**: `/ai/generate-flashcards`
- **Parametry**:
  - **Wymagane**: `text_content` (string, 1000-10000 znaków)
  - **Opcjonalne**: Brak
- **Request Body**:
  ```json
  {
    "text_content": "Long text content (1000-10000 characters) to generate flashcards from..."
  }
  ```
- **Headers**: `Authorization: Bearer <supabase-jwt>`

## 3. Wykorzystywane typy

### DTOs (już istniejące w `src/dtos.py`):
- **Request**: `AIGenerateFlashcardsRequest`
- **Response**: `AIGenerateFlashcardsResponse`
- **Flashcard Response**: `FlashcardResponse`

### Command Modele (już istniejące w `src/db/schemas.py`):
- `SourceTextCreate`
- `FlashcardCreate` 
- `AiGenerationEventCreate`

### Nowe typy do utworzenia:
```python
# W src/dtos.py
class LLMFlashcardSuggestion(BaseModel):
    front_content: str
    back_content: str

class LLMGenerateResponse(BaseModel):
    flashcards: List[LLMFlashcardSuggestion]
    model_used: str
    cost: Optional[float] = None
```

## 4. Szczegóły odpowiedzi

### Sukces (200 OK):
```json
{
  "source_text_id": "uuid-of-created-source-text",
  "ai_generation_event_id": "uuid-of-created-event", 
  "suggested_flashcards": [
    {
      "id": "uuid-of-suggested-flashcard-1",
      "user_id": "uuid-of-user",
      "source_text_id": "uuid-of-created-source-text",
      "front_content": "AI generated question 1?",
      "back_content": "AI generated answer 1.",
      "source": "ai_suggestion",
      "status": "pending_review",
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
}
```

### Kody błędów:
- **400 Bad Request**: Brak `text_content`
- **401 Unauthorized**: Brak lub nieprawidłowy JWT
- **422 Unprocessable Entity**: `text_content` poza zakresem 1000-10000 znaków
- **503 Service Unavailable**: Błąd lub timeout LLM
- **500 Internal Server Error**: Błędy bazy danych

## 5. Przepływ danych

1. **Uwierzytelnienie**: Walidacja JWT i wyciągnięcie `user_id`
2. **Walidacja wejścia**: Sprawdzenie długości `text_content` (1000-10000 znaków)
3. **Utworzenie source_text**: Zapis tekstu źródłowego w bazie danych
4. **Wywołanie LLM**: Komunikacja z OpenRouter.ai
5. **Parsowanie odpowiedzi**: Przetworzenie sugestii fiszek z LLM
6. **Utworzenie fiszek**: Zapis fiszek ze statusem `pending_review`
7. **Utworzenie eventu**: Zapis statystyk generowania w `ai_generation_events`
8. **Zwrócenie odpowiedzi**: Przesłanie listy wygenerowanych fiszek

## 6. Względy bezpieczeństwa

### Uwierzytelnienie i autoryzacja:
- **JWT Validation**: Walidacja tokenu Supabase w middleware
- **RLS**: PostgreSQL Row Level Security zapewnia dostęp tylko do własnych danych
- **User Context**: `user_id` wyciągany z JWT i używany we wszystkich operacjach DB

### Walidacja danych:
- **Input Sanitization**: Walidacja długości i zawartości `text_content`
- **Rate Limiting**: Ograniczenie częstotliwości wywołań (kosztowne operacje AI)
- **Content Filtering**: Opcjonalne filtrowanie nieodpowiednich treści

### Ochrona przed atakami:
- **DoS Protection**: Limit długości tekstu (max 10000 znaków)
- **Timeout Protection**: Timeout dla wywołań LLM (np. 30s)
- **Error Information Leakage**: Ogólne komunikaty błędów dla użytkownika

## 7. Obsługa błędów

### Scenariusze błędów:

1. **400 Bad Request**:
   - Brak pola `text_content`
   - Nieprawidłowy format JSON
   - **Obsługa**: Walidacja Pydantic, zwrócenie szczegółów błędu

2. **401 Unauthorized**:
   - Brak tokenu JWT
   - Nieprawidłowy/wygasły token
   - **Obsługa**: Middleware uwierzytelnienia

3. **422 Unprocessable Entity**:
   - `text_content` < 1000 lub > 10000 znaków
   - **Obsługa**: Walidacja Pydantic z custom error messages

4. **503 Service Unavailable**:
   - Timeout LLM
   - Błąd API OpenRouter.ai
   - Brak dostępnych modeli
   - **Obsługa**: Try-catch z retry logic, fallback responses

5. **500 Internal Server Error**:
   - Błędy bazy danych
   - Błędy parsowania odpowiedzi LLM
   - **Obsługa**: Logging, rollback transakcji, generic error response

### Strategia logowania:
```python
import logging
logger = logging.getLogger(__name__)

# Błędy krytyczne (500)
logger.error(f"Database error for user {user_id}: {str(e)}")

# Błędy LLM (503) 
logger.warning(f"LLM service error for user {user_id}: {str(e)}")

# Błędy walidacji (422)
logger.info(f"Validation error for user {user_id}: {str(e)}")
```

## 8. Rozważania dotyczące wydajności

### Potencjalne wąskie gardła:
1. **Wywołania LLM**: Najwolniejsza część procesu (2-10s)
2. **Operacje DB**: Multiple INSERTs w transakcji
3. **Parsowanie odpowiedzi**: Przetwarzanie JSON z LLM

### Strategie optymalizacji:

1. **Asynchroniczne operacje**:
   ```python
   async def generate_flashcards(text_content: str, user_id: uuid.UUID):
       # Wszystkie operacje async/await
   ```

2. **Database transactions**:
   ```python
   async with supabase.transaction():
       # Wszystkie operacje DB w jednej transakcji
   ```

3. **Connection pooling**: Wykorzystanie connection pool Supabase

4. **Caching**: 
   - Cache dla podobnych tekstów (opcjonalne)
   - Cache dla konfiguracji LLM

5. **Timeout management**:
   ```python
   async with asyncio.timeout(30):  # 30s timeout dla LLM
       llm_response = await call_llm_api(text_content)
   ```

## 9. Etapy wdrożenia

### Krok 1: Utworzenie serwisu AI
```python
# src/services/ai_service.py
class AIService:
    async def generate_flashcards_from_text(
        self, 
        text_content: str, 
        user_id: uuid.UUID
    ) -> AIGenerateFlashcardsResponse:
        # Implementacja logiki
```

### Krok 2: Konfiguracja OpenRouter.ai
```python
# src/core/config.py
class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "anthropic/claude-3-haiku"
    LLM_TIMEOUT: int = 30
```

### Krok 3: Implementacja klienta LLM
```python
# src/services/llm_client.py
class LLMClient:
    async def generate_flashcards(
        self, 
        text_content: str
    ) -> LLMGenerateResponse:
        # Komunikacja z OpenRouter.ai
```

### Krok 4: Implementacja operacji bazodanowych
```python
# src/services/database_service.py
class DatabaseService:
    async def create_source_text(self, data: SourceTextCreate) -> SourceText
    async def create_flashcards(self, flashcards: List[FlashcardCreate]) -> List[Flashcard]
    async def create_ai_generation_event(self, data: AiGenerationEventCreate) -> AiGenerationEvent
```

### Krok 5: Implementacja endpointu
```python
# src/routers/ai_router.py
@router.post("/generate-flashcards", response_model=AIGenerateFlashcardsResponse)
async def generate_flashcards(
    request: AIGenerateFlashcardsRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    # Implementacja endpointu
```

### Krok 6: Middleware uwierzytelnienia
```python
# src/middleware/auth_middleware.py
async def get_current_user(
    authorization: str = Header(None)
) -> User:
    # Walidacja JWT Supabase
```

### Krok 7: Obsługa błędów i logowanie
```python
# src/middleware/error_middleware.py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Globalna obsługa błędów
```

### Krok 8: Testy jednostkowe
```python
# tests/test_ai_generate_flashcards.py
class TestAIGenerateFlashcards:
    async def test_successful_generation(self):
        # Test pozytywny
    
    async def test_invalid_text_length(self):
        # Test walidacji
    
    async def test_llm_service_error(self):
        # Test błędu LLM
```

### Krok 9: Testy integracyjne
```python
# tests/integration/test_ai_endpoint.py
async def test_full_flashcard_generation_flow():
    # Test pełnego przepływu
```

### Krok 10: Dokumentacja i deployment
- Aktualizacja dokumentacji API
- Konfiguracja zmiennych środowiskowych
- Deploy i monitoring

## 10. Dodatkowe uwagi implementacyjne

### Struktura plików:
```
src/
├── routers/
│   └── ai_router.py          # Endpoint definition
├── services/
│   ├── ai_service.py         # Business logic
│   ├── llm_client.py         # LLM communication
│   └── database_service.py   # DB operations
├── middleware/
│   ├── auth_middleware.py    # Authentication
│   └── error_middleware.py   # Error handling
└── dtos.py                   # Request/Response models
```

### Dependency Injection:
```python
# src/dependencies.py
def get_ai_service() -> AIService:
    return AIService()

def get_llm_client() -> LLMClient:
    return LLMClient()
```

### Konfiguracja prompta LLM:
```python
FLASHCARD_GENERATION_PROMPT = """
Based on the following text, generate educational flashcards.
Each flashcard should have a clear question (front) and answer (back).
Generate 5-10 flashcards that cover the most important concepts.

Text: {text_content}

Return JSON format:
{
  "flashcards": [
    {"front_content": "Question?", "back_content": "Answer"}
  ]
}
"""
``` 