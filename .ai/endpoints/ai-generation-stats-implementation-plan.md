# API Endpoint Implementation Plan: Get AI Generation Statistics

## 1. Przegląd punktu końcowego

Endpoint `GET /ai/generation-stats` służy do pobierania statystyk wydarzeń generowania fiszek AI dla uwierzytelnionego użytkownika. Endpoint zwraca paginowane dane z tabeli `ai_generation_events`, zawierające szczegółowe informacje o procesach generowania fiszek przez AI, w tym koszty, liczbę wygenerowanych, zaakceptowanych i odrzuconych kart.

## 2. Szczegóły żądania

- **Metoda HTTP:** GET
- **Struktura URL:** `/ai/generation-stats`
- **Parametry:**
  - **Opcjonalne:**
    - `page` (int): Numer strony dla paginacji (domyślnie: 1, minimum: 1)
    - `size` (int): Liczba elementów na stronę (domyślnie: 20, maksimum: 100)
- **Request Body:** Brak (GET request)
- **Wymagane nagłówki:** Authorization header z tokenem Supabase

## 3. Wykorzystywane typy

### Query Parameters Model
```python
class AiGenerationStatsQueryParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
```

### Response Models
```python
class PaginatedAiGenerationStatsResponse(BaseModel):
    items: List[AiGenerationEvent]
    total: int
    page: int
    size: int
    pages: int
```

### Existing Models (z schemas.py)
- `AiGenerationEvent` - dla odpowiedzi API
- `AiGenerationEventBase` - dla reprezentacji bazy danych

## 4. Szczegóły odpowiedzi

### Success Response (200 OK)
```json
{
    "items": [
        {
            "id": "uuid-of-event",
            "user_id": "uuid-of-user",
            "source_text_id": "uuid-of-source-text",
            "llm_model_used": "gpt-3.5-turbo",
            "generated_cards_count": 10,
            "accepted_cards_count": 7,
            "rejected_cards_count": 2,
            "cost": 0.0015,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total": 5,
    "page": 1,
    "size": 20,
    "pages": 1
}
```

### Error Responses
- **401 Unauthorized:** Brak lub nieprawidłowy token uwierzytelniania
- **400 Bad Request:** Nieprawidłowe parametry paginacji
- **500 Internal Server Error:** Błąd serwera lub bazy danych

## 5. Przepływ danych

1. **Walidacja żądania:**
   - Walidacja parametrów query (page, size)
   - Ekstrakcja i walidacja tokena uwierzytelniania
   - Pobranie user_id z tokena Supabase

2. **Zapytanie do bazy danych:**
   - Wykorzystanie RLS policies do automatycznej filtracji danych użytkownika
   - Zapytanie z OFFSET/LIMIT dla paginacji
   - Zliczenie całkowitej liczby rekordów dla paginacji

3. **Przetwarzanie odpowiedzi:**
   - Konwersja wyników bazy danych na modele Pydantic
   - Obliczenie liczby stron na podstawie total/size
   - Zwrócenie paginated response

## 6. Względy bezpieczeństwa

### Uwierzytelnianie i autoryzacja
- **Wymagane uwierzytelnianie:** Każde żądanie musi zawierać prawidłowy token Supabase
- **Row Level Security (RLS):** Automatyczne filtrowanie danych przez user_id
- **Walidacja tokenów:** Weryfikacja tokenów przez Supabase auth

### Ochrona przed nadużyciami
- **Limit rozmiaru strony:** Maksymalnie 100 elementów na stronę
- **Walidacja parametrów:** Sprawdzanie poprawności page/size
- **Rate limiting:** Rozważenie implementacji w middleware

## 7. Obsługa błędów

### Scenariusze błędów i kody statusu

1. **401 Unauthorized:**
   - Brak tokenu uwierzytelniania
   - Nieprawidłowy lub wygasły token
   - Błąd weryfikacji tokena Supabase

2. **400 Bad Request:**
   - page < 1
   - size < 1 lub size > 100
   - Nieprawidłowy format parametrów

3. **500 Internal Server Error:**
   - Błąd połączenia z bazą danych
   - Błąd zapytania SQL
   - Nieoczekiwane błędy serwera

### Logging strategia
- Błędy uwierzytelniania (poziom WARNING)
- Błędy walidacji parametrów (poziom INFO)
- Błędy bazy danych (poziom ERROR)
- Wszystkie 500 errors (poziom CRITICAL)

## 8. Rozważania dotyczące wydajności

### Optymalizacje bazy danych
- **Indeksy:** Wykorzystanie istniejących indeksów na `user_id` i `created_at`
- **Paginacja:** Efektywne OFFSET/LIMIT queries
- **Count queries:** Optymalizacja zapytań zliczających

### Caching strategia
- Rozważenie cache'owania wyników dla często pobieranych stron
- Cache invalidation przy aktualizacji danych

### Monitoring
- Śledzenie czasów odpowiedzi
- Monitoring wykorzystania bazy danych
- Alerting dla długich zapytań

## 9. Etapy wdrożenia

### Krok 1: Utworzenie modeli Pydantic
- Stworzenie `AiGenerationStatsQueryParams`
- Stworzenie `PaginatedAiGenerationStatsResponse`
- Dodanie walidacji parametrów

### Krok 2: Implementacja serwisu
- Utworzenie `AiGenerationService` w `src/services/ai_generation_service.py`
- Implementacja metody `get_user_generation_stats(user_id, page, size)`
- Dodanie obsługi paginacji i zliczania rekordów

### Krok 3: Utworzenie dependency dla uwierzytelniania
- Implementacja `get_current_user_id()` dependency
- Integracja z Supabase auth
- Obsługa błędów uwierzytelniania

### Krok 4: Implementacja endpointu
- Utworzenie router w `src/routers/ai_routes.py`
- Implementacja funkcji route `get_generation_stats()`
- Integracja z serwisem i dependency

### Krok 5: Obsługa błędów
- Implementacja middleware obsługi błędów
- Dodanie logowania
- Standardizacja odpowiedzi błędów

### Krok 6: Testy
- Unit testy dla serwisu
- Integration testy dla endpointu
- Testy uwierzytelniania i autoryzacji

### Krok 7: Dokumentacja
- Aktualizacja OpenAPI schemas
- Dodanie przykładów użycia
- Dokumentacja konfiguracji

### Krok 8: Deployment i monitoring
- Konfiguracja environment variables
- Setup monitoringu i alertów
- Deployment verification

## 10. Przykładowy kod implementacji

### Router Definition
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from src.services.ai_generation_service import AiGenerationService
from src.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/ai", tags=["AI Generation"])

@router.get("/generation-stats", response_model=PaginatedAiGenerationStatsResponse)
async def get_generation_stats(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: str = Depends(get_current_user_id),
    service: AiGenerationService = Depends()
):
    """Get AI generation statistics for the authenticated user."""
    try:
        return await service.get_user_generation_stats(user_id, page, size)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Service Implementation
```python
from src.db.database import get_db_connection
from src.db.schemas import AiGenerationEvent

class AiGenerationService:
    async def get_user_generation_stats(
        self, user_id: str, page: int, size: int
    ) -> PaginatedAiGenerationStatsResponse:
        offset = (page - 1) * size
        
        # Count total records
        count_query = """
            SELECT COUNT(*) FROM ai_generation_events 
            WHERE user_id = $1
        """
        
        # Fetch paginated records
        data_query = """
            SELECT * FROM ai_generation_events 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
        """
        
        async with get_db_connection() as conn:
            total = await conn.fetchval(count_query, user_id)
            records = await conn.fetch(data_query, user_id, size, offset)
            
        items = [AiGenerationEvent.from_orm(record) for record in records]
        pages = (total + size - 1) // size  # Ceiling division
        
        return PaginatedAiGenerationStatsResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
``` 