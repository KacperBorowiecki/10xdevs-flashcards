# API Endpoint Implementation Plan: Submit Flashcard Review Result

## 1. Przegląd punktu końcowego

Endpoint `POST /spaced-repetition/reviews` służy do przyjmowania oceny wykonania użytkownika za przegląd flashcardy w systemie spaced repetition. Na podstawie otrzymanej oceny (performance_rating) algorytm spaced repetition oblicza następną datę przeglądu i aktualizuje interwał powtórzenia. Endpoint zwraca zaktualizowane dane spaced repetition dla danej flashcardy.

## 2. Szczegóły żądania

- **Metoda HTTP:** POST
- **Struktura URL:** `/spaced-repetition/reviews`
- **Content-Type:** application/json
- **Uwierzytelnianie:** Bearer token (Supabase JWT)

### Parametry:
- **Wymagane:**
  - `flashcard_id` (UUID): Identyfikator flashcardy poddawanej przeglądowi
  - `performance_rating` (integer): Ocena wykonania w skali 1-5
- **Opcjonalne:** brak

### Request Body:
```json
{
    "flashcard_id": "uuid-of-reviewed-flashcard",
    "performance_rating": 5
}
```

## 3. Wykorzystywane typy

### Request DTO:
```python
class SpacedRepetitionReviewRequest(BaseModel):
    flashcard_id: uuid.UUID
    performance_rating: int = Field(ge=1, le=5, description="Performance rating (1-5)")
```

### Response DTO:
```python
class SpacedRepetitionReviewResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    flashcard_id: uuid.UUID
    due_date: datetime
    current_interval: int
    last_reviewed_at: datetime
    data_extra: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
```

### Command Model:
```python
class ReviewFlashcardCommand(BaseModel):
    user_id: uuid.UUID
    flashcard_id: uuid.UUID
    performance_rating: int
```

## 4. Szczegóły odpowiedzi

### Sukces (200 OK):
```json
{
    "id": "uuid-of-repetition-record",
    "user_id": "uuid-of-user",
    "flashcard_id": "uuid-of-reviewed-flashcard",
    "due_date": "2024-01-15T10:00:00Z",
    "current_interval": 5,
    "last_reviewed_at": "2024-01-10T10:00:00Z",
    "data_extra": {},
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-10T10:00:00Z"
}
```

### Kody błędów:
- **400 Bad Request:** Nieprawidłowy format żądania, brakujące pola
- **401 Unauthorized:** Brak lub nieprawidłowy token uwierzytelniający
- **404 Not Found:** Flashcard nie istnieje, nie należy do użytkownika lub nie jest aktywna
- **422 Unprocessable Entity:** Nieprawidłowa wartość performance_rating

## 5. Przepływ danych

1. **Walidacja żądania:** Sprawdzenie formatu i wymaganych pól
2. **Uwierzytelnianie:** Weryfikacja JWT token i wyciągnięcie user_id
3. **Walidacja flashcard:** Sprawdzenie czy flashcard istnieje, należy do użytkownika i jest aktywna
4. **Algorytm spaced repetition:** Obliczenie nowej due_date i current_interval na podstawie performance_rating
5. **Aktualizacja bazy danych:** Upsert rekordu user_flashcard_spaced_repetition
6. **Zwrócenie odpowiedzi:** Zaktualizowane dane spaced repetition

### Interakcje z bazą danych:
- **SELECT:** Weryfikacja flashcard z tabeli `flashcards`
- **SELECT:** Pobranie obecnych danych z `user_flashcard_spaced_repetition`
- **INSERT/UPDATE:** Upsert w tabeli `user_flashcard_spaced_repetition`

## 6. Względy bezpieczeństwa

### Uwierzytelnianie:
- Wymagany prawidłowy Supabase JWT token w nagłówku Authorization
- Wyciągnięcie user_id z validated token payload

### Autoryzacja:
- RLS policies na poziomie PostgreSQL zapewniają dostęp tylko do własnych danych
- Dodatkowa weryfikacja w aplikacji, że flashcard należy do uwierzytelnionego użytkownika

### Walidacja danych:
- Pydantic models dla walidacji typu i formatu danych
- Sprawdzenie zakresu performance_rating (1-5)
- UUID format validation dla flashcard_id

## 7. Obsługa błędów

### 400 Bad Request:
- Brakujące wymagane pola (flashcard_id, performance_rating)
- Nieprawidłowy format UUID dla flashcard_id
- Nieprawidłowy typ danych w request body

### 401 Unauthorized:
- Brak nagłówka Authorization
- Nieprawidłowy lub wygasły JWT token
- Błąd walidacji token przez Supabase

### 404 Not Found:  
- Flashcard o podanym ID nie istnieje
- Flashcard nie należy do uwierzytelnionego użytkownika
- Flashcard ma status inny niż 'active'

### 422 Unprocessable Entity:
- performance_rating poza zakresem 1-5
- Błędy związane z ograniczeniami algorytmu spaced repetition

### 500 Internal Server Error:
- Błędy połączenia z bazą danych
- Nieobsłużone wyjątki w algorytmie spaced repetition

## 8. Rozważania dotyczące wydajności

### Optymalizacje:
- Index na kolumnach `user_id` i `flashcard_id` w tabeli `user_flashcard_spaced_repetition`
- Użycie async/await dla operacji bazodanowych
- Connection pooling dla bazy danych

### Potencjalne wąskie gardła:
- Operacje bazodanowe (SELECT + UPSERT)
- Obliczenia algorytmu spaced repetition
- Walidacja JWT token

### Monitoring:
- Logowanie czasu odpowiedzi
- Monitoring błędów i wyjątków
- Metryki użycia endpoint

## 9. Etapy wdrożenia

1. **Stworzenie modeli Pydantic:**
   - SpacedRepetitionReviewRequest
   - SpacedRepetitionReviewResponse
   - ReviewFlashcardCommand

2. **Implementacja SpacedRepetitionService:**
   - Funkcja walidacji flashcard
   - Algorytm spaced repetition (SM-2 lub podobny)
   - Funkcje CRUD dla user_flashcard_spaced_repetition

3. **Stworzenie dependency dla uwierzytelniania:**
   - Funkcja do walidacji Supabase JWT
   - Wyciągnięcie user_id z token payload

4. **Implementacja route handler:**
   - Walidacja request body
   - Wywołanie SpacedRepetitionService
   - Obsługa błędów i zwrócenie odpowiedzi

5. **Konfiguracja router:**
   - Dodanie route do FastAPI router
   - Ustawienie dependencies (authentication)

6. **Testowanie:**
   - Unit testy dla service layer
   - Integration testy dla endpoint
   - Testy bezpieczeństwa (unauthorized access)

7. **Dokumentacja i deployment:**
   - OpenAPI/Swagger documentation
   - Aktualizacja API documentation
   - Deployment i monitoring 