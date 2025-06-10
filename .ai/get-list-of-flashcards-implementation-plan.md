# API Endpoint Implementation Plan: List User's Flashcards (`GET /flashcards`)

## 1. Przegląd punktu końcowego
Celem tego punktu końcowego jest umożliwienie uwierzytelnionym użytkownikom pobierania listy ich fiszek. Użytkownicy mogą filtrować wyniki według statusu i źródła fiszki oraz korzystać z paginacji do przeglądania dużych zbiorów danych.

## 2. Szczegóły żądania
- **Metoda HTTP:** `GET`
- **Struktura URL:** `/flashcards`
- **Parametry zapytania:**
    - `status: Optional[str]` (Filtruje fiszki według statusu. Dozwolone wartości: 'active', 'pending_review', 'rejected'. Domyślnie 'active'.)
    - `source: Optional[str]` (Filtruje fiszki według źródła. Dozwolone wartości: 'manual', 'ai_suggestion'.)
    - `page: Optional[int]` (Numer strony dla paginacji. Domyślnie 1. Minimalna wartość: 1.)
    - `size: Optional[int]` (Liczba fiszek na stronę. Domyślnie 20. Minimalna wartość: 1, Maksymalna wartość: 100.)
- **Request Body:** Brak (dla metody GET)

## 3. Wykorzystywane typy

### Modele DTO (Data Transfer Objects) i Walidacji Parametrów:

1.  **`ListFlashcardsQueryParams(BaseModel)`:**
    Model Pydantic do walidacji i parsowania parametrów zapytania.
    ```python
    from typing import Optional
    from pydantic import BaseModel, Field
    from enum import Enum

    # Zakładając, że te enumy są zdefiniowane w src.db.schemas lub podobnym module
    # from src.db.schemas import FlashcardStatusEnum, FlashcardSourceEnum

    class FlashcardStatusEnum(str, Enum): # Przykładowa definicja, jeśli nie importowana
        ACTIVE = "active"
        PENDING_REVIEW = "pending_review"
        REJECTED = "rejected"

    class FlashcardSourceEnum(str, Enum): # Przykładowa definicja, jeśli nie importowana
        MANUAL = "manual"
        AI_SUGGESTION = "ai_suggestion"

    class ListFlashcardsQueryParams(BaseModel):
        status: Optional[FlashcardStatusEnum] = Field(default=FlashcardStatusEnum.ACTIVE, description="Filter by flashcard status")
        source: Optional[FlashcardSourceEnum] = Field(default=None, description="Filter by flashcard source")
        page: int = Field(default=1, ge=1, description="Page number for pagination")
        size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    ```

### Modele Odpowiedzi:

1.  **`FlashcardResponse(schemas.Flashcard)`:**
    Model Pydantic reprezentujący pojedynczą fiszkę w odpowiedzi. Zakłada się, że `schemas.Flashcard` jest już zdefiniowany (zgodnie z `src/db/schemas.py`).
    ```python
    # Z src.db.schemas.Flashcard
    # class Flashcard(BaseModel):
    #     id: uuid.UUID
    #     user_id: uuid.UUID
    #     source_text_id: Optional[uuid.UUID]
    #     front_content: str
    #     back_content: str
    #     source: FlashcardSourceEnum
    #     status: FlashcardStatusEnum
    #     created_at: datetime
    #     updated_at: datetime
    #
    #     class Config:
    #         orm_mode = True
    ```

2.  **`PaginatedFlashcardsResponse(BaseModel)`:**
    Model Pydantic dla paginowanej odpowiedzi.
    ```python
    from typing import List
    from pydantic import BaseModel
    # from .schemas import Flashcard # Lub odpowiednia ścieżka importu

    class PaginatedFlashcardsResponse(BaseModel):
        items: List[Flashcard] # Zastąpić Flashcard odpowiednim typem odpowiedzi
        total: int
        page: int
        size: int
        pages: int
    ```

## 4. Szczegóły odpowiedzi
- **Odpowiedź sukcesu (200 OK):**
    ```json
    {
        "items": [
            {
                "id": "uuid-of-flashcard-1",
                "user_id": "uuid-of-user",
                "source_text_id": "uuid-if-ai-generated-else-null",
                "front_content": "Front of card 1",
                "back_content": "Back of card 1",
                "source": "manual", // lub "ai_suggestion"
                "status": "active", // lub "pending_review", "rejected"
                "created_at": "timestamp",
                "updated_at": "timestamp"
            }
            // ... więcej fiszek
        ],
        "total": 25,    // Całkowita liczba fiszek pasujących do kryteriów
        "page": 1,      // Aktualny numer strony
        "size": 20,     // Liczba fiszek na stronie
        "pages": 2      // Całkowita liczba stron
    }
    ```
- **Odpowiedzi błędów:**
    - `401 Unauthorized`: Problem z uwierzytelnieniem (np. brak tokenu, nieprawidłowy token).
    - `422 Unprocessable Entity`: Nieprawidłowe parametry zapytania (np. `page < 1`, `size > 100`, nieprawidłowa wartość `status` lub `source`).
    - `500 Internal Server Error`: Ogólny błąd serwera.

## 5. Przepływ danych
1.  Żądanie `GET /flashcards` dociera do serwera FastAPI.
2.  **Uwierzytelnianie:**
    -   Middleware/zależność FastAPI weryfikuje token JWT z nagłówka `Authorization`.
    -   Jeśli token jest nieprawidłowy lub go brakuje, zwracane jest `401 Unauthorized`.
    -   Jeśli token jest prawidłowy, `user_id` jest wyodrębniany.
3.  **Walidacja parametrów zapytania:**
    -   Parametry `status`, `source`, `page`, `size` są parsowane i walidowane przez model `ListFlashcardsQueryParams`.
    -   Jeśli walidacja się nie powiedzie, FastAPI automatycznie zwraca `422 Unprocessable Entity`.
4.  **Logika biznesowa (w `FlashcardService.get_flashcards_for_user`):**
    -   Serwis otrzymuje `user_id` oraz zwalidowane parametry (`params: ListFlashcardsQueryParams`).
    -   Serwis konstruuje zapytanie do bazy danych (np. używając SQLAlchemy) w celu pobrania fiszek:
        -   Filtrowanie po `user_id`.
        -   Filtrowanie po `status`, jeśli podano.
        -   Filtrowanie po `source`, jeśli podano.
    -   Serwis wykonuje dwa zapytania:
        1.  Zapytanie o pobranie fiszek z uwzględnieniem paginacji (`LIMIT params.size`, `OFFSET (params.page - 1) * params.size`).
        2.  Zapytanie o całkowitą liczbę fiszek (`COUNT(*)`) pasujących do kryteriów filtrowania (bez paginacji), aby obliczyć `total` i `pages`.
    -   Zapytania są wykonywane asynchronicznie.
5.  **Formatowanie odpowiedzi:**
    -   Serwis przekształca wyniki z bazy danych na listę obiektów `FlashcardResponse`.
    -   Serwis tworzy obiekt `PaginatedFlashcardsResponse`, wypełniając `items`, `total`, `page`, `size` oraz obliczając `pages = ceil(total / size)`.
6.  **Odpowiedź HTTP:**
    -   FastAPI zwraca obiekt `PaginatedFlashcardsResponse` jako JSON z kodem statusu `200 OK`.

## 6. Względy bezpieczeństwa
- **Uwierzytelnianie:** Wszystkie żądania muszą być uwierzytelnione za pomocą tokenu JWT (Bearer token) dostarczonego przez Supabase. Endpoint musi być chroniony, a dostęp bez ważnego tokenu powinien skutkować odpowiedzią `401 Unauthorized`.
- **Autoryzacja:** Logika pobierania danych musi ściśle filtrować fiszki na podstawie `user_id` uzyskanego z tokenu JWT. PostgreSQL Row Level Security (RLS) powinno być skonfigurowane na tabeli `flashcards`, aby zapewnić, że użytkownicy mogą uzyskać dostęp tylko do własnych danych, nawet w przypadku błędu w logice aplikacji.
- **Walidacja danych wejściowych:** Parametry `page` i `size` muszą być walidowane, aby zapobiec nadmiernemu obciążeniu bazy danych (np. `size` ograniczony do maksymalnie 100). Parametry `status` i `source` powinny być walidowane względem predefiniowanych wartości (enumy), aby zapobiec nieoczekiwanemu zachowaniu lub potencjalnym atakom injection, jeśli byłyby używane bezpośrednio w surowych zapytaniach (choć ORM powinien temu zapobiegać).
- **Zapobieganie SQL Injection:** Użycie ORM (np. SQLAlchemy zgodnie z `database-interaction-rules`) z parametryzowanymi zapytaniami jest kluczowe.
- **Ochrona przed wyliczeniem (Enumeration):** Użycie UUID jako identyfikatorów (`id` fiszki) pomaga chronić przed atakami polegającymi na odgadywaniu sekwencyjnych ID.

## 7. Rozważania dotyczące wydajności
- **Indeksowanie bazy danych:** Kluczowe kolumny używane do filtrowania i sortowania powinny być zindeksowane. Zgodnie z `db-plan.md`, indeksy na `flashcards(user_id)`, `flashcards(status)` i `flashcards(source)` są istotne. Należy również rozważyć złożone indeksy, jeśli często występują kombinacje filtrów, np. `(user_id, status)` lub `(user_id, source)`.
- **Paginacja:** Paginacja jest obowiązkowa, aby uniknąć pobierania zbyt wielu danych naraz. Należy unikać paginacji opartej na offsecie dla bardzo dużych zbiorów danych (offset staje się wolny). Jeśli to stanie się problemem, można rozważyć paginację opartą na kursorze (keyset pagination). Na razie standardowa paginacja `LIMIT/OFFSET` powinna być wystarczająca.
- **Asynchroniczne operacje:** Wszystkie operacje I/O, w tym zapytania do bazy danych, muszą być asynchroniczne (`async/await`), zgodnie z `performance-optimization-rules` i `database-interaction-rules`.
- **Liczba zapytań:** Minimalizuj liczbę zapytań do bazy danych. W tym przypadku dwa zapytania (jedno dla danych, jedno dla `COUNT`) są akceptowalne dla paginacji.
- **Optymalizacja ORM:** Upewnij się, że ORM generuje wydajne zapytania SQL. W razie potrzeby analizuj generowane zapytania.

## 8. Etapy wdrożenia

1.  **Definicja modeli Pydantic:**
    *   Zaimplementuj `ListFlashcardsQueryParams` w odpowiednim module (np. `src/api/v1/endpoints/flashcard_models.py` lub `src/api/v1/dependencies/query_params.py`).
    *   Zaimplementuj `PaginatedFlashcardsResponse` (oraz upewnij się, że `FlashcardResponse` lub jego odpowiednik jest dostępny z `src.db.schemas`) w tym samym module co modele parametrów lub w dedykowanym module modeli odpowiedzi.
2.  **Utworzenie/aktualizacja serwisu (`FlashcardService`):**
    *   Zdefiniuj plik serwisu, np. `src/services/flashcard_service.py`.
    *   Dodaj metodę `async def get_flashcards_for_user(self, db: AsyncSession, user_id: uuid.UUID, params: ListFlashcardsQueryParams) -> PaginatedFlashcardsResponse:`.
    *   W metodzie zaimplementuj logikę pobierania danych z bazy (filtrowanie, paginacja) przy użyciu SQLAlchemy i `AsyncSession`.
    *   Oblicz `total` i `pages`.
    *   Zwróć obiekt `PaginatedFlashcardsResponse`.
3.  **Implementacja endpointu FastAPI:**
    *   W module routera fiszek (np. `src/api/v1/endpoints/flashcards.py`):
        *   Dodaj funkcję endpointu `async def list_user_flashcards(...)`.
        *   Użyj `Depends` do wstrzyknięcia `ListFlashcardsQueryParams`.
        *   Użyj `Depends` do wstrzyknięcia zależności uwierzytelniania (np. `get_current_user`), która dostarczy `user_id`.
        *   Użyj `Depends` do wstrzyknięcia sesji `AsyncSession` do bazy danych.
        *   Wywołaj metodę serwisową `flashcard_service.get_flashcards_for_user(...)`.
        *   Określ `response_model=PaginatedFlashcardsResponse` i `status_code=status.HTTP_200_OK`.
4.  **Konfiguracja zależności uwierzytelniania:**
    *   Upewnij się, że zależność FastAPI do weryfikacji JWT i ekstrakcji `user_id` jest poprawnie skonfigurowana i używana w definicji endpointu.
5.  **Testy:**
    *   **Testy jednostkowe:** Przetestuj logikę serwisu `FlashcardService.get_flashcards_for_user` (np. mockując bazę danych), sprawdzając poprawność filtrowania, paginacji i obliczeń.
    *   **Testy integracyjne/E2E:** Przetestuj endpoint API:
        *   Różne kombinacje parametrów `status`, `source`, `page`, `size`.
        *   Przypadki brzegowe (np. pusta lista fiszek, jedna strona, wiele stron).
        *   Przypadki błędów (np. brak tokenu, nieprawidłowy token - `401`; nieprawidłowe parametry - `422`).
        *   Sprawdzenie, czy użytkownik A nie widzi fiszek użytkownika B.
6.  **Dokumentacja API:**
    *   Upewnij się, że endpoint jest poprawnie udokumentowany przez OpenAPI (automatycznie przez FastAPI), w tym parametry, odpowiedzi i kody błędów. Dodaj opisy (`description`) do parametrów w modelu Pydantic.
7.  **Logowanie:**
    *   Skonfiguruj logowanie w FastAPI, aby rejestrować żądania, odpowiedzi i błędy zgodnie z `error-handling-rules`.
8.  **Przegląd kodu i wdrożenie:**
    *   Przeprowadź przegląd kodu pod kątem zgodności z planem, zasadami implementacji i najlepszymi praktykami.
    *   Wdróż zmiany na odpowiednie środowisko. 