# API Endpoint Implementation Plan: Update Flashcard

## 1. Przegląd punktu końcowego

Endpoint umożliwia aktualizację zawartości flashcard (front/back content) lub zmiany statusu dla AI-suggested flashcards. Obsługuje częściowe aktualizacje zgodnie z semantyką PATCH, zapewniając elastyczną modyfikację zasobów przy zachowaniu bezpieczeństwa na poziomie użytkownika.

**Główne funkcjonalności:**
- Aktualizacja treści flashcard (front_content, back_content)
- Zmiana statusu AI-suggested flashcards (pending_review → active/rejected)  
- Walidacja uprawnień użytkownika (tylko własne flashcards)
- Automatyczna aktualizacja timestamp updated_at

## 2. Szczegóły żądania

- **Metoda HTTP:** PATCH
- **Struktura URL:** `/flashcards/{flashcard_id}`
- **Parametry:**
  - **Wymagane:** 
    - `flashcard_id` (UUID) - identyfikator flashcard w ścieżce URL
  - **Opcjonalne w Request Body:**
    - `front_content` (string, max 500 znaków) - treść przodu karty
    - `back_content` (string, max 1000 znaków) - treść tyłu karty  
    - `status` (enum: "active", "rejected") - tylko dla AI-suggested flashcards z statusem "pending_review"

- **Request Body Examples:**
  ```json
  // Aktualizacja treści
  {
    "front_content": "Updated front content",
    "back_content": "Updated back content"
  }
  
  // Zmiana statusu AI-suggested flashcard
  {
    "status": "active"
  }
  
  // Kombinowana aktualizacja  
  {
    "front_content": "New front",
    "status": "active"
  }
  ```

## 3. Wykorzystywane typy

**DTO Models (z src/db/schemas.py):**
- `FlashcardUpdate` - model walidacji request body
- `Flashcard` - model response 
- `FlashcardStatusEnum` - enum dla statusów
- `FlashcardSourceEnum` - enum dla źródeł

**Command Models (nowe, do utworzenia):**
```python
class UpdateFlashcardCommand:
    flashcard_id: uuid.UUID
    user_id: uuid.UUID
    updates: FlashcardUpdate
```

## 4. Szczegóły odpowiedzi

**Success Response (200 OK):**
```json
{
  "id": "uuid-of-flashcard",
  "user_id": "uuid-of-user", 
  "source_text_id": "uuid-if-ai-generated-else-null",
  "front_content": "Updated front content",
  "back_content": "Updated back content",
  "source": "manual",
  "status": "active",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T11:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Nieprawidłowe przejście statusu, brak pól do aktualizacji
- `401 Unauthorized`: Brak uwierzytelnienia
- `404 Not Found`: Flashcard nie istnieje lub brak dostępu  
- `422 Unprocessable Entity`: Błąd walidacji (długość treści, nieprawidłowy status)

## 5. Przepływ danych

```
1. Request Validation
   ├── Walidacja UUID flashcard_id
   ├── Walidacja request body (FlashcardUpdate)
   └── Sprawdzenie czy przynajmniej jedno pole do aktualizacji

2. Authentication & Authorization  
   ├── Pobranie user_id z Supabase auth
   ├── Sprawdzenie istnienia flashcard
   └── Walidacja właściciela (flashcard.user_id == current_user.id)

3. Business Logic Validation
   ├── Walidacja przejść statusu (jeśli status w updates)
   ├── Walidacja długości treści  
   └── Przygotowanie danych do aktualizacji

4. Database Update
   ├── Wykonanie UPDATE na tabeli flashcards  
   ├── Wykorzystanie RLS policies
   └── Automatyczna aktualizacja updated_at

5. Response Preparation
   ├── Pobranie zaktualizowanego flashcard
   ├── Mapowanie na model Flashcard
   └── Zwrócenie response 200 OK
```

## 6. Względy bezpieczeństwa

**Uwierzytelnienie:**
- Wymagany token Supabase JWT w header Authorization
- Automatyczne pobranie user_id z auth context

**Autoryzacja:**
- RLS policies na poziomie PostgreSQL (user_id = auth.uid())
- Dodatkowa weryfikacja na poziomie aplikacji
- Brak możliwości aktualizacji cudzych flashcards

**Walidacja danych:**  
- Sanityzacja input data (escape HTML/special characters w treści)
- Walidacja długości pól zgodnie z ograniczeniami DB
- Walidacja enum values dla status

**Bezpieczeństwo zapytań:**
- Parametryzowane zapytania SQL (ochrona przed SQL injection)
- Walidacja UUID format dla flashcard_id

## 7. Obsługa błędów

**Scenariusze błędów:**

| Kod | Scenariusz | Obsługa |
|-----|------------|---------|
| 400 | Nieprawidłowe przejście statusu (np. manual flashcard → status change) | Zwróć error z opisem dozwolonych operacji |
| 400 | Brak pól do aktualizacji | Zwróć error "At least one field must be provided" |
| 401 | Brak/nieprawidłowy token uwierzytelnienia | Zwróć error "Authentication required" |
| 404 | Flashcard nie istnieje | Zwróć error "Flashcard not found" |
| 404 | Flashcard istnieje ale należy do innego użytkownika | Zwróć error "Flashcard not found" (bez ujawniania istnienia) |
| 422 | front_content > 500 znaków | Zwróć error z limitem znaków |
| 422 | back_content > 1000 znaków | Zwróć error z limitem znaków |
| 422 | Nieprawidłowy format flashcard_id | Zwróć error "Invalid flashcard ID format" |

**Error Response Format:**
```json
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR", 
  "field_errors": {
    "front_content": ["Content too long (max 500 characters)"]
  }
}
```

## 8. Rozważania dotyczące wydajności

**Optymalizacje:**
- Pojedyncze zapytanie UPDATE z WHERE clause (user_id + flashcard_id)
- Wykorzystanie indeksów na (user_id, id) dla szybkiego lookup
- Minimalne SELECT po UPDATE (tylko potrzebne pola)

**Monitoring:**
- Logowanie czasu response dla slow queries (>100ms)
- Metryki ilości błędów 404 vs 422 (indikator bezpieczeństwa)
- Monitoring częstości aktualizacji per user (rate limiting)

**Caching:**
- Brak cache na poziomie endpoint (dane często się zmieniają)
- Możliwy cache na poziomie connection pool do DB

## 9. Etapy wdrożenia

### Krok 1: Utworzenie Service Layer
```python
# src/services/flashcard_service.py
async def update_flashcard(
    flashcard_id: uuid.UUID,
    user_id: uuid.UUID, 
    updates: FlashcardUpdate
) -> Flashcard:
    # Business logic implementation
```

### Krok 2: Walidacja i modele biznesowe
```python
def validate_status_transition(current_flashcard: Flashcard, new_status: str) -> bool:
    # Implementacja logiki walidacji przejść statusu
    
def validate_content_length(front: str = None, back: str = None) -> List[str]:
    # Walidacja długości treści
```

### Krok 3: Implementacja endpointu w routerze
```python  
# src/routers/flashcard_routes.py
@router.patch("/{flashcard_id}", response_model=Flashcard)
async def update_flashcard(
    flashcard_id: uuid.UUID,
    updates: FlashcardUpdate,
    current_user: User = Depends(get_current_user)
):
    # Implementacja endpoint logic
```

### Krok 4: Testy jednostkowe i integracyjne
- Testy happy path dla aktualizacji treści i statusu
- Testy scenariuszy błędów (401, 404, 422, 400)
- Testy bezpieczeństwa (cross-user access)
- Testy walidacji przejść statusu

### Krok 5: Database operations
```python
# src/db/flashcard_repository.py  
async def update_flashcard_by_id(
    flashcard_id: uuid.UUID,
    user_id: uuid.UUID,
    updates: dict
) -> Optional[Flashcard]:
    # Implementacja zapytania UPDATE z RLS
```

### Krok 6: Error handling i middleware
- Implementacja custom exception handlers
- Logowanie błędów i performance metrics
- Rate limiting per user (opcjonalnie)

### Krok 7: Dokumentacja OpenAPI
- Aktualizacja schema OpenAPI z przykładami request/response
- Dokumentacja error codes i scenariuszy użycia
- Przykłady dla różnych przypadków aktualizacji 