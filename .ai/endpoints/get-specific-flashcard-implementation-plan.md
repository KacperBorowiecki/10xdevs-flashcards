# API Endpoint Implementation Plan: Get Specific Flashcard

## 1. Przegląd punktu końcowego

Endpoint `GET /flashcards/{flashcard_id}` służy do pobierania szczegółowych informacji o konkretnej fiszce na podstawie jej unikalnego identyfikatora UUID. Endpoint implementuje pełną autoryzację użytkownika przy wykorzystaniu Row Level Security (RLS) w Supabase, zapewniając, że użytkownicy mogą uzyskać dostęp wyłącznie do swoich własnych fiszek.

## 2. Szczegóły żądania

- **Metoda HTTP:** GET
- **Struktura URL:** `/flashcards/{flashcard_id}`
- **Parametry:**
  - **Wymagane:** 
    - `flashcard_id` (path parameter, UUID) - Unikalny identyfikator fiszki
  - **Opcjonalne:** Brak
- **Request Body:** Brak (GET endpoint)
- **Headers wymagane:**
  - `Authorization: Bearer <token>` - Token uwierzytelniający Supabase

## 3. Wykorzystywane typy

```python
# Response Model
from src.db.schemas import Flashcard

# Dodatkowe modele do rozważenia:
class FlashcardResponse(BaseModel):
    """Dedykowany model odpowiedzi z dodatkowymi metadanymi"""
    id: uuid.UUID
    user_id: uuid.UUID
    source_text_id: Optional[uuid.UUID]
    front_content: str
    back_content: str
    source: FlashcardSourceEnum
    status: FlashcardStatusEnum
    created_at: datetime
    updated_at: datetime
```

## 4. Szczegóły odpowiedzi

**Success Response (200 OK):**
```json
{
    "id": "uuid-of-flashcard",
    "user_id": "uuid-of-user", 
    "source_text_id": "uuid-if-ai-generated-else-null",
    "front_content": "Front content",
    "back_content": "Back content",
    "source": "manual",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Nieprawidłowy format UUID
- `401 Unauthorized`: Brak uwierzytelniania
- `404 Not Found`: Fiszka nie została znaleziona lub brak dostępu
- `500 Internal Server Error`: Błędy serwera/bazy danych

## 5. Przepływ danych

1. **Request Processing:**
   - Walidacja formatu UUID w path parameter
   - Weryfikacja tokenu uwierzytelniającego Supabase
   - Wyodrębnienie user_id z tokenu

2. **Database Query:**
   - Async query do tabeli `flashcards` z RLS
   - Supabase automatycznie filtruje po `user_id` dzięki RLS policy
   - Single record fetch z optimized indexing

3. **Response Formation:**
   - Mapowanie database row do Pydantic model
   - JSON serialization z właściwymi typami danych
   - Return structured response

## 6. Względy bezpieczeństwa

**Uwierzytelnianie:**
- Supabase JWT token validation
- Integration z `auth.users` table
- Automatic user context extraction

**Autoryzacja:**
- Row Level Security policies na tabeli `flashcards`
- Policy: `auth.uid() = user_id` zapewnia dostęp tylko do własnych fiszek
- Automatic filtering bez dodatkowej logiki aplikacyjnej

**Zabezpieczenia:**
- UUID usage zapobiega enumeration attacks
- RLS prevents information disclosure
- Input sanitization dla path parameters
- Rate limiting considerations (implementacja na poziomie middleware)

## 7. Obsługa błędów

**Scenariusze błędów i obsługa:**

1. **Invalid UUID Format (400):**
   ```python
   raise HTTPException(
       status_code=400,
       detail="Invalid flashcard ID format. Must be a valid UUID."
   )
   ```

2. **Unauthorized Access (401):**
   ```python
   raise HTTPException(
       status_code=401,
       detail="Authentication required. Please provide a valid token."
   )
   ```

3. **Flashcard Not Found (404):**
   ```python
   raise HTTPException(
       status_code=404,
       detail="Flashcard not found or you don't have access to it."
   )
   ```

4. **Database Errors (500):**
   - Proper logging z stack traces
   - Generic error message dla security
   - Monitoring integration

**Error Logging Strategy:**
- Structured logging z context (user_id, flashcard_id, timestamp)
- Error severity levels
- Integration z monitoring tools

## 8. Rozważania dotyczące wydajności

**Database Optimization:**
- Wykorzystane indexes: `idx_flashcards_user_id`, primary key index
- Single query operation - minimal database load
- RLS policy optimized przez database engine

**Caching Strategy:**
- Consider Redis caching dla frequently accessed flashcards
- Cache invalidation przy updates
- User-specific cache keys

**Response Optimization:**
- Minimal data transfer - zwracamy tylko potrzebne fields
- JSON compression dla większych payloads
- Async operations nie blokują other requests

## 9. Etapy wdrożenia

### Krok 1: Database Service Layer
```python
# src/services/flashcard_service.py
async def get_flashcard_by_id(flashcard_id: UUID, user_context) -> Optional[Flashcard]:
    # Implementation z Supabase client i RLS
```

### Krok 2: Router Implementation  
```python
# src/routers/flashcards.py
@router.get("/flashcards/{flashcard_id}", response_model=Flashcard)
async def get_flashcard(flashcard_id: UUID, current_user: User = Depends(get_current_user)):
    # Route handler implementation
```

### Krok 3: Dependency Injection
- Setup authentication dependency (`get_current_user`)
- Supabase client dependency injection
- Error handling middleware integration

### Krok 4: Input Validation
- UUID path parameter validation
- Pydantic model validation
- Custom validators dla business rules

### Krok 5: Error Handling
- HTTPException handling
- Custom error responses
- Logging integration

### Krok 6: Security Implementation
- RLS policy verification
- Token validation testing
- Authorization test scenarios

### Krok 7: Testing
- Unit tests dla service layer
- Integration tests z database
- Security tests (unauthorized access scenarios)
- Performance tests z różnymi load patterns

### Krok 8: Documentation
- OpenAPI schema generation
- Endpoint documentation
- Error code documentation
- Authentication requirements documentation

### Krok 9: Monitoring & Logging
- Request/response logging
- Performance metrics
- Error rate monitoring
- Security event logging

### Krok 10: Deployment
- Environment configuration
- Database migration verification  
- Production testing
- Rollback strategy preparation 