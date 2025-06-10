# API Endpoint Implementation Plan: Delete Flashcard

## 1. Przegląd punktu końcowego

Endpoint służy do usuwania konkretnej karty pamięciowej przez użytkownika. Operacja jest nieodwracalna i usuwa kartę wraz z powiązanymi danymi spaced repetition. Endpoint wykorzystuje autoryzację JWT oraz polityki RLS w bazie danych PostgreSQL do zapewnienia bezpieczeństwa.

## 2. Szczegóły żądania

- **Metoda HTTP:** DELETE
- **Struktura URL:** `/flashcards/{flashcard_id}`
- **Parametry:**
  - **Wymagane:** 
    - `flashcard_id` (path parameter) - UUID identyfikujący kartę do usunięcia
  - **Opcjonalne:** Brak
- **Request Body:** Brak (DELETE nie wymaga ciała żądania)
- **Headers:**
  - `Authorization: Bearer <jwt_token>` (wymagany)

## 3. Wykorzystywane typy

```python
# Path parameter validation
from pydantic import BaseModel
import uuid

class FlashcardDeletePath(BaseModel):
    flashcard_id: uuid.UUID

# No request/response body models needed for DELETE operation
# Success response is empty with 204 status code
```

## 4. Szczegóły odpowiedzi

- **Sukces (204 No Content):**
  - Status Code: 204
  - Body: Pusty
  - Headers: Standardowe
  
- **Błędy:**
  - `401 Unauthorized`: Brak lub nieprawidłowy token JWT
  - `404 Not Found`: Karta nie istnieje lub użytkownik nie ma dostępu
  - `422 Unprocessable Entity`: Nieprawidłowy format UUID w parametrze
  - `500 Internal Server Error`: Błąd serwera/bazy danych

## 5. Przepływ danych

1. **Uwierzytelnienie:**
   - Walidacja JWT token z nagłówka Authorization
   - Wyciągnięcie user_id z token payload

2. **Walidacja parametrów:**
   - Walidacja formatu UUID dla `flashcard_id`
   - FastAPI automatycznie zwaliduje typ UUID

3. **Operacja bazodanowa:**
   - Połączenie z bazą PostgreSQL (async)
   - Wykonanie DELETE query z warunkami:
     - `id = flashcard_id`
     - `user_id = current_user_id` (przez RLS)
   - Sprawdzenie liczby usuniętych wierszy

4. **Obsługa związanych danych:**
   - Database CASCADE policies automatycznie usuną powiązane dane z `user_flashcard_spaced_repetition`
   - `source_text_id` zostanie ustawione na NULL jeśli flashcard był AI-generated

5. **Odpowiedź:**
   - 204 No Content przy sukcesie
   - Odpowiedni kod błędu przy niepowodzeniu

## 6. Względy bezpieczeństwa

- **Uwierzytelnienie:** 
  - Wymagany prawidłowy JWT token z Supabase
  - Walidacja podpisu i czasu wygaśnięcia tokenu

- **Autoryzacja:**
  - RLS policies w PostgreSQL zapewniają dostęp tylko do własnych kart
  - Brak możliwości usunięcia kart innych użytkowników

- **Walidacja danych:**
  - UUID format zapobiega atakom injection
  - Pydantic automatycznie waliduje format UUID

- **Rate limiting:**
  - Rozważyć implementację rate limiting dla operacji DELETE

## 7. Obsługa błędów

| Scenariusz | Status Code | Opis | Logowanie |
|------------|-------------|------|-----------|
| Sukces | 204 | Karta została usunięta | Info level |
| Brak tokenu | 401 | Authorization header nie istnieje | Warning level |
| Nieprawidłowy token | 401 | JWT token jest nieprawidłowy lub wygasł | Warning level |
| Nieprawidłowy UUID | 422 | flashcard_id nie jest prawidłowym UUID | Info level |
| Karta nie istnieje | 404 | Karta nie została znaleziona lub brak dostępu | Info level |
| Błąd bazy danych | 500 | Błąd połączenia lub zapytania do bazy | Error level |
| Błąd serwera | 500 | Nieoczekiwany błąd aplikacji | Error level |

## 8. Rozważania dotyczące wydajności

- **Optymalizacja bazy danych:**
  - Indeks na `user_id` i `id` już istnieje (primary key + foreign key)
  - DELETE z WHERE klauzulą jest efektywna
  - CASCADE operations są automatyczne i zoptymalizowane

- **Połączenie z bazą:**
  - Użycie async/await dla nieblokujących operacji
  - Connection pooling przez async database driver

- **Caching:**
  - Brak potrzeby cache'owania dla operacji DELETE
  - Rozważyć invalidację cache jeśli jest używany gdzie indziej

- **Monitoring:**
  - Śledzenie czasu wykonania operacji DELETE
  - Monitoring częstotliwości usuwania kart

## 9. Etapy wdrożenia

### Krok 1: Przygotowanie infrastruktury serwisowej
- Utworzenie `src/services/flashcard_service.py`
- Implementacja funkcji `delete_flashcard_by_id(user_id: UUID, flashcard_id: UUID)`
- Obsługa połączenia z bazą danych (async)

### Krok 2: Implementacja endpointu
- Utworzenie route w `src/routers/flashcard_routes.py`
- Implementacja funkcji `delete_flashcard(flashcard_id: UUID, current_user: User)`
- Walidacja parametrów przez Pydantic

### Krok 3: Integracja uwierzytelnienia
- Import i użycie dependency dla JWT validation
- Integracja z Supabase auth system
- Wyciągnięcie user_id z JWT token

### Krok 4: Obsługa błędów
- Implementacja HTTPException handling
- Dodanie odpowiednich kodów statusu
- Logowanie błędów z odpowiednim poziomem

### Krok 5: Testy
- Unit testy dla service layer
- Integration testy dla API endpoint
- Testy scenariuszy błędów

### Krok 6: Rejestracja route
- Dodanie router do głównej aplikacji FastAPI
- Konfiguracja middleware dla logowania
- Dokumentacja OpenAPI (automatyczna przez FastAPI)

### Krok 7: Monitoring i logging
- Dodanie metrics dla operacji DELETE
- Error tracking i alerting
- Performance monitoring

### Krok 8: Deployment i walidacja
- Deploy do środowiska testowego
- Walidacja funkcjonalności
- Load testing dla operacji DELETE 