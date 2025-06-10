# API Endpoint Implementation Plan: Get Due Flashcards for Review

## 1. Przegląd punktu końcowego

Endpoint `GET /spaced-repetition/due-cards` pobiera listę aktywnych flashcards, które są gotowe do powtórzenia w systemie spaced repetition dla uwierzytelnionego użytkownika. Endpoint zwraca pełne dane flashcard wraz z dodatkowymi informacjami o harmonogramie powtórzeń (due_date, current_interval, last_reviewed_at).

**Kluczowe cechy:**
- Filtrowanie tylko aktywnych kart z `due_date <= NOW()`
- Opcjonalne ograniczenie liczby zwracanych wyników
- Integracja danych z tabel `flashcards` i `user_flashcard_spaced_repetition`
- Uwierzytelnianie przez Supabase JWT + RLS

## 2. Szczegóły żądania

- **Metoda HTTP:** GET
- **Struktura URL:** `/spaced-repetition/due-cards`
- **Parametry:**
  - **Wymagane:** Brak
  - **Opcjonalne:** 
    - `limit` (int): Maksymalna liczba kart do zwrócenia (1-100, domyślnie 20)
- **Request Body:** Brak (metoda GET)
- **Headers:** 
  - `Authorization: Bearer <supabase_jwt_token>` (wymagany)

## 3. Wykorzystywane typy

### 3.1. Nowe modele do utworzenia:

```python
# src/api/models/spaced_repetition_models.py
class SpacedRepetitionQueryParams(BaseModel):
    limit: Optional[int] = Field(default=20, ge=1, le=100)

class RepetitionData(BaseModel):
    due_date: datetime
    current_interval: int
    last_reviewed_at: Optional[datetime] = None

class FlashcardWithRepetition(FlashcardBase):
    repetition_data: RepetitionData
```

### 3.2. Istniejące modele:
- `FlashcardBase` - podstawowe dane flashcard
- `UserFlashcardSpacedRepetitionBase` - dane spaced repetition

## 4. Szczegóły odpowiedzi

### 4.1. Pomyślna odpowiedź (200 OK):
```json
[
    {
        "id": "uuid-of-due-flashcard-1",
        "user_id": "uuid-of-user",
        "source_text_id": null,
        "front_content": "Due card 1 front",
        "back_content": "Due card 1 back",
        "source": "manual",
        "status": "active",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
        "repetition_data": {
            "due_date": "2024-01-20T10:00:00Z",
            "current_interval": 3,
            "last_reviewed_at": "2024-01-17T10:00:00Z"
        }
    }
]
```

### 4.2. Kody statusu:
- **200 OK**: Pomyślne pobranie listy (może być pusta)
- **400 Bad Request**: Nieprawidłowy parametr `limit`
- **401 Unauthorized**: Brak lub nieprawidłowy token JWT
- **500 Internal Server Error**: Błąd po stronie serwera

## 5. Przepływ danych

### 5.1. Sekwencja operacji:
1. **Walidacja JWT token** - middleware Supabase
2. **Walidacja parametrów** - FastAPI + Pydantic
3. **Zapytanie do bazy danych** - JOIN flashcards + user_flashcard_spaced_repetition
4. **Filtrowanie wyników** - due_date <= NOW() AND status = 'active'
5. **Mapowanie danych** - konwersja do FlashcardWithRepetition
6. **Zwrócenie odpowiedzi** - JSON lista obiektów

### 5.2. Zapytanie SQL (konceptualne):
```sql
SELECT 
    f.*,
    sr.due_date,
    sr.current_interval,
    sr.last_reviewed_at
FROM flashcards f
JOIN user_flashcard_spaced_repetition sr ON f.id = sr.flashcard_id
WHERE f.user_id = auth.uid()
    AND f.status = 'active'
    AND sr.due_date <= NOW()
ORDER BY sr.due_date ASC
LIMIT ?;
```

## 6. Względy bezpieczeństwa

### 6.1. Uwierzytelnianie i autoryzacja:
- **Supabase JWT validation** - middleware automatycznie weryfikuje token
- **RLS policies** - PostgreSQL automatycznie filtruje dane użytkownika
- **User context extraction** - `auth.uid()` z JWT token

### 6.2. Walidacja danych wejściowych:
- Parametr `limit` ograniczony do zakresu 1-100
- Sanityzacja wszystkich parametrów przez Pydantic
- Ochrona przed SQL injection przez parametryzowane zapytania

### 6.3. Rate limiting (opcjonalnie):
- Implementacja middleware do ograniczenia częstotliwości żądań
- Monitoring podejrzanej aktywności

## 7. Obsługa błędów

### 7.1. Scenariusze błędów:

| Błąd | Kod | Opis | Obsługa |
|------|-----|------|---------|
| Brak token | 401 | Authorization header missing | Middleware zwraca 401 |
| Nieprawidłowy token | 401 | Invalid JWT | Middleware zwraca 401 |
| Nieprawidłowy limit | 400 | limit < 1 or limit > 100 | Pydantic validation error |
| Błąd bazy danych | 500 | Database connection/query error | Logging + generic error response |
| Timeout | 500 | Query timeout | Logging + retry logic |

### 7.2. Error handling strategy:
- **Early returns** dla warunków błędu
- **Structured logging** wszystkich błędów
- **User-friendly error messages** bez ujawniania szczegółów technicznych
- **Fallback responses** dla błędów bazy danych

## 8. Rozważania dotyczące wydajności

### 8.1. Optymalizacje bazy danych:
- **Index na due_date** - `CREATE INDEX idx_due_date ON user_flashcard_spaced_repetition(due_date)`
- **Composite index** - `(user_id, due_date)` dla lepszej wydajności
- **LIMIT clause** - ograniczenie liczby zwracanych rekordów

### 8.2. Caching (opcjonalnie):
- **Application-level cache** dla często żądanych danych
- **Redis cache** z TTL dla wyników zapytań
- **Cache invalidation** przy aktualizacji danych repetition

### 8.3. Monitoring:
- **Query execution time** tracking
- **Response time** monitoring
- **Error rate** tracking

## 9. Etapy wdrożenia

### Krok 1: Utworzenie modeli Pydantic
- Stworzenie `src/api/models/spaced_repetition_models.py`
- Definicja `SpacedRepetitionQueryParams`, `RepetitionData`, `FlashcardWithRepetition`
- Testy jednostkowe dla modeli

### Krok 2: Implementacja serwisu
- Stworzenie `src/services/spaced_repetition_service.py`
- Implementacja `get_due_flashcards(user_id: UUID, limit: int)`
- Logika zapytania z JOIN i filtrowania
- Testy jednostkowe serwisu

### Krok 3: Stworzenie routera
- Stworzenie `src/routers/spaced_repetition_router.py`
- Definicja endpoint'u `GET /due-cards`
- Integracja z serwisem i middleware uwierzytelniania
- Walidacja parametrów przez Pydantic

### Krok 4: Konfiguracja middleware i bezpieczeństwa
- Konfiguracja Supabase JWT middleware
- Weryfikacja RLS policies w bazie danych
- Dodanie rate limiting (opcjonalnie)

### Krok 5: Optymalizacja bazy danych
- Utworzenie niezbędnych indeksów
- Optymalizacja zapytań SQL
- Testowanie wydajności z większymi zbiorami danych

### Krok 6: Testy integracyjne
- Testy endpoint'u z prawdziwymi danymi
- Testy scenariuszy błędów (401, 400, 500)
- Testy wydajnościowe z różnymi wartościami `limit`

### Krok 7: Monitoring i logging
- Implementacja structured logging
- Konfiguracja metryk wydajności
- Dashboardy do monitorowania stanu aplikacji

### Krok 8: Dokumentacja
- Aktualizacja dokumentacji API (OpenAPI/Swagger)
- Dokumentacja kodu i komentarze
- Instrukcje dla zespołu QA

## 10. Struktura plików

```
src/
├── api/
│   └── models/
│       └── spaced_repetition_models.py    # Nowe modele Pydantic
├── routers/
│   └── spaced_repetition_router.py        # Router endpoint'u
├── services/
│   └── spaced_repetition_service.py       # Logika biznesowa
└── db/
    └── schemas.py                         # Istniejące modele (bez zmian)
```

## 11. Przykład implementacji

```python
# src/routers/spaced_repetition_router.py
from fastapi import APIRouter, Depends, Query
from typing import List
import uuid

router = APIRouter(prefix="/spaced-repetition", tags=["spaced-repetition"])

@router.get("/due-cards", response_model=List[FlashcardWithRepetition])
async def get_due_flashcards(
    limit: int = Query(default=20, ge=1, le=100),
    current_user_id: uuid.UUID = Depends(get_current_user_id)
) -> List[FlashcardWithRepetition]:
    """Pobiera listę flashcards gotowych do powtórzenia."""
    
    service = SpacedRepetitionService()
    due_cards = await service.get_due_flashcards(
        user_id=current_user_id,
        limit=limit
    )
    
    return due_cards
```

Ten plan implementacji zapewnia kompleksowe wskazówki dla zespołu programistów, uwzględniając wszystkie aspekty bezpieczeństwa, wydajności i jakości kodu zgodnie z zasadami FastAPI i Python. 