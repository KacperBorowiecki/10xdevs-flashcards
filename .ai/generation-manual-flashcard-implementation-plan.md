# API Endpoint Implementation Plan: Create Manual Flashcard

## 1. Przegląd punktu końcowego
Ten punkt końcowy umożliwia uwierzytelnionym użytkownikom ręczne tworzenie nowych fiszek. Po utworzeniu, fiszka jest automatycznie oznaczana jako 'manual' (źródło) i 'active' (status). Dodatkowo, inicjowany jest dla niej rekord w systemie powtórek (spaced repetition), ustawiając ją jako gotową do pierwszej powtórki.

## 2. Szczegóły żądania
-   **Metoda HTTP:** `POST`
-   **Struktura URL:** `/flashcards`
-   **Nagłówki:**
    -   `Authorization: Bearer <JWT>` (wymagany)
    -   `Content-Type: application/json` (wymagany)
-   **Ciało żądania (Request Body):**
    Struktura JSON opisana przez model Pydantic `FlashcardManualCreateRequest`:
    ```json
    {
        "front_content": "What is the capital of France?",
        "back_content": "Paris"
    }
    ```
    **Model Pydantic (`FlashcardManualCreateRequest`):**
    ```python
    from pydantic import BaseModel, Field

    class FlashcardManualCreateRequest(BaseModel):
        front_content: str = Field(..., description="Front content of the flashcard.", min_length=1, max_length=500)
        back_content: str = Field(..., description="Back content of the flashcard.", min_length=1, max_length=1000)
    ```
    *   Pola `front_content` i `back_content` są wymagane.
    *   Walidacja długości: `front_content` (1-500 znaków), `back_content` (1-1000 znaków).

## 3. Szczegóły odpowiedzi
-   **Odpowiedź sukcesu (201 Created):**
    Zwraca obiekt JSON reprezentujący nowo utworzoną fiszkę, zgodny z modelem Pydantic `Flashcard` (z `src/db/schemas.py`).
    ```json
    {
        "id": "uuid-of-new-flashcard",
        "user_id": "uuid-of-user",
        "source_text_id": null,
        "front_content": "What is the capital of France?",
        "back_content": "Paris",
        "source": "manual",
        "status": "active",
        "created_at": "timestamp",
        "updated_at": "timestamp"
    }
    ```
-   **Odpowiedzi błędów:**
    *   `401 Unauthorized`: Problem z uwierzytelnieniem (np. brak/nieprawidłowy token JWT).
    *   `422 Unprocessable Entity`: Błąd walidacji danych wejściowych (np. brakujące pola, przekroczona długość, nieprawidłowy typ danych).
    *   `500 Internal Server Error`: Nieoczekiwany błąd po stronie serwera.

## 4. Przepływ danych
1.  Klient wysyła żądanie `POST /flashcards` z tokenem JWT w nagłówku `Authorization` i danymi fiszki (`front_content`, `back_content`) w ciele JSON.
2.  Middleware/zależność FastAPI weryfikuje token JWT. Jeśli jest nieprawidłowy, zwraca `401 Unauthorized`. W przeciwnym razie wyodrębnia `user_id`.
3.  FastAPI parsuje i waliduje ciało żądania przy użyciu modelu `FlashcardManualCreateRequest`. W przypadku błędów walidacji zwraca `422 Unprocessable Entity`.
4.  Router przekazuje `user_id` i zwalidowane dane do odpowiedniej funkcji w warstwie serwisowej (np. `FlashcardService.create_manual_flashcard`).
5.  Warstwa serwisowa wykonuje następujące operacje w ramach **transakcji bazodanowej**:
    a.  Konstruuje obiekt fiszki do zapisu:
        *   `user_id` = wyodrębniony `user_id`.
        *   `front_content`, `back_content` = z danych żądania.
        *   `source` = `FlashcardSourceEnum.MANUAL`.
        *   `status` = `FlashcardStatusEnum.ACTIVE`.
        *   `source_text_id` = `None`.
    b.  Zapisuje nową fiszkę w tabeli `flashcards` (operacja asynchroniczna).
    c.  Pobiera ID nowo utworzonej fiszki.
    d.  Konstruuje obiekt rekordu spaced repetition:
        *   `user_id` = wyodrębniony `user_id`.
        *   `flashcard_id` = ID nowej fiszki.
        *   `due_date` = aktualny czas UTC (`datetime.utcnow()`).
        *   `current_interval` = 1 (zgodnie z definicją tabeli `user_flashcard_spaced_repetition` w `db-plan.md`).
        *   `last_reviewed_at` = `None`.
    e.  Zapisuje nowy rekord w tabeli `user_flashcard_spaced_repetition` (operacja asynchroniczna).
6.  Jeśli transakcja zakończy się pomyślnie, warstwa serwisowa zwraca pełny obiekt utworzonej fiszki.
7.  FastAPI serializuje obiekt fiszki do JSON i wysyła odpowiedź `201 Created` do klienta.
8.  W przypadku błędu podczas operacji bazodanowych (np. naruszenie ograniczeń, problem z połączeniem) lub innego nieoczekiwanego wyjątku w serwisie, transakcja jest wycofywana, błąd jest logowany, a do klienta zwracany jest `500 Internal Server Error`.

## 5. Względy bezpieczeństwa
-   **Uwierzytelnianie:** Punkt końcowy musi być chroniony. Dostęp do niego mają wyłącznie uwierzytelnieni użytkownicy. Uwierzytelnianie odbywa się za pomocą tokenów JWT wydawanych przez Supabase i weryfikowanych przez FastAPI.
-   **Autoryzacja:** Logika aplikacji musi zapewnić, że fiszka jest tworzona dla uwierzytelnionego użytkownika (`user_id` z tokenu JWT). Mechanizmy Row Level Security (RLS) w PostgreSQL dodatkowo zabezpieczają dane na poziomie bazy, gwarantując, że operacje zapisu są wykonywane w kontekście prawidłowego `user_id`.
-   **Walidacja danych wejściowych:** Rygorystyczna walidacja `front_content` i `back_content` (typ, wymagana obecność, minimalna/maksymalna długość) przez Pydantic jest kluczowa dla zapobiegania błędom i potencjalnym atakom (np. nadmierna ilość danych).
-   **Ochrona przed SQL Injection:** Użycie ORM (np. SQLAlchemy, jeśli będzie wykorzystywane z Supabase Python client) lub bibliotek bazodanowych, które parametryzują zapytania, jest standardem i chroni przed atakami SQL Injection. Należy unikać ręcznego tworzenia zapytań SQL z danymi od użytkownika.
-   **Zasada najmniejszych uprawnień:** Proces FastAPI powinien działać z minimalnymi uprawnieniami wymaganymi do jego funkcjonowania.

## 6. Obsługa błędów
-   **Błędy walidacji (422 Unprocessable Entity):**
    *   Obsługiwane automatycznie przez FastAPI podczas walidacji modelu Pydantic `FlashcardManualCreateRequest`.
    *   Przykłady: brakujące `front_content` lub `back_content`, przekroczenie `max_length`, niespełnienie `min_length`, nieprawidłowy typ danych.
    *   Odpowiedź powinna zawierać szczegóły dotyczące pól, które nie przeszły walidacji.
-   **Brak uwierzytelnienia (401 Unauthorized):**
    *   Obsługiwane przez zależność FastAPI odpowiedzialną za weryfikację JWT.
    *   Przykłady: brak nagłówka `Authorization`, nieprawidłowy lub wygasły token.
-   **Błędy serwera (500 Internal Server Error):**
    *   Wszelkie nieoczekiwane błędy podczas przetwarzania żądania, np.:
        *   Błąd połączenia z bazą danych.
        *   Niepowodzenie zapisu do tabeli `flashcards` lub `user_flashcard_spaced_repetition` pomimo przejścia walidacji (np. naruszenie unikalnego klucza, jeśli dotyczy, lub inny błąd DB).
        *   Nieoczekiwany wyjątek w logice serwisu.
    *   Takie błędy powinny być logowane po stronie serwera z odpowiednią ilością szczegółów (stack trace) w celu debugowania. Klient otrzymuje generyczną odpowiedź 500.
    *   Zgodnie z `error-handling-rules.mdc`, należy używać `HTTPException` dla oczekiwanych błędów biznesowych, które nie są pokrywane przez standardową walidację Pydantic, oraz middleware do globalnej obsługi nieoczekiwanych wyjątków.

## 7. Wydajność
-   **Operacje asynchroniczne:** Wszystkie interakcje z bazą danych (zapis fiszki, zapis rekordu spaced repetition) muszą być wykonane asynchronicznie (`async/await`) zgodnie z `database-interaction-rules` i `performance-optimization-rules`, aby nie blokować pętli zdarzeń FastAPI.
-   **Połączenia z bazą danych:** Należy efektywnie zarządzać pulą połączeń do bazy danych, aby uniknąć narzutu związanego z częstym otwieraniem/zamykaniem połączeń. Supabase Python client lub SQLAlchemy (jeśli używane) zazwyczaj zarządzają tym.
-   **Transakcje bazodanowe:** Użycie transakcji dla operacji zapisu do wielu tabel (`flashcards` i `user_flashcard_spaced_repetition`) zapewnia spójność danych, ale może mieć minimalny wpływ na wydajność. Należy to zrównoważyć z korzyściami integralności.
-   **Walidacja:** Walidacja Pydantic jest szybka, ale dla bardzo złożonych reguł lub dużej liczby pól mogłaby stać się wąskim gardłem (tutaj nie dotyczy).

## 8. Etapy wdrożenia
1.  **Definicja modeli Pydantic:**
    *   Utworzyć lub zweryfikować model `FlashcardManualCreateRequest` w `src/api/v1/schemas/flashcard_schemas.py` (lub odpowiednim module), uwzględniając walidację długości pól.
    *   Zweryfikować istnienie i poprawność modelu odpowiedzi `Flashcard` oraz modeli `FlashcardCreate` i `UserFlashcardSpacedRepetitionCreate` w `src/db/schemas.py`.
2.  **Implementacja logiki serwisowej:**
    *   Utworzyć (jeśli nie istnieje) `FlashcardService` w `src/services/flashcard_service.py`.
    *   Zaimplementować asynchroniczną metodę `create_manual_flashcard(user_id: uuid.UUID, data: FlashcardManualCreateRequest) -> Flashcard` w serwisie.
    *   Wewnątrz metody:
        *   Przygotować dane dla `FlashcardCreate` (ustawić `source='manual'`, `status='active'`, `source_text_id=None`).
        *   Przygotować dane dla `UserFlashcardSpacedRepetitionCreate` (ustawić `due_date=datetime.utcnow()`, `current_interval=1`).
        *   Zaimplementować logikę zapisu do bazy danych (tabel `flashcards` i `user_flashcard_spaced_repetition`) z użyciem asynchronicznych operacji i transakcji. Można to zrobić poprzez dedykowane repozytoria (np. `FlashcardRepository`, `SpacedRepetitionRepository`) lub bezpośrednio, jeśli projekt nie stosuje wzorca repozytorium.
3.  **Implementacja punktu końcowego API (Router):**
    *   W odpowiednim pliku routera (np. `src/api/v1/routers/flashcards.py`):
        *   Dodać nowy endpoint `POST /flashcards`.
        *   Zastosować zależność do uwierzytelniania i ekstrakcji `user_id`.
        *   Wstrzyknąć `FlashcardService` jako zależność.
        *   Wywołać metodę serwisową `create_manual_flashcard`.
        *   Ustawić kod statusu odpowiedzi na `201 Created`.
        *   Określić model odpowiedzi jako `schemas.Flashcard`.
4.  **Obsługa zależności i konfiguracja:**
    *   Upewnić się, że zależności (Supabase client, FastAPI, Pydantic) są poprawnie skonfigurowane.
    *   Skonfigurować mechanizm transakcji dla operacji bazodanowych, jeśli używana biblioteka tego wymaga (np. przez context manager).
5.  **Testowanie:**
    *   **Testy jednostkowe:** dla logiki w `FlashcardService` (mockując interakcje z bazą danych).
    *   **Testy integracyjne/API:** dla punktu końcowego `/flashcards`, sprawdzające:
        *   Poprawne tworzenie fiszki i rekordu spaced repetition przy prawidłowych danych.
        *   Zwracanie statusu `201` i poprawnego obiektu fiszki.
        *   Obsługę błędów walidacji (`422`).
        *   Obsługę braku uwierzytelnienia (`401`).
        *   Poprawność danych zapisanych w bazie (opcjonalnie, weryfikacja stanu bazy).
6.  **Dokumentacja:**
    *   Automatycznie generowana dokumentacja OpenAPI/Swagger przez FastAPI powinna odzwierciedlać nowy endpoint, jego parametry i odpowiedzi.
    *   W razie potrzeby zaktualizować zewnętrzną dokumentację API.
7.  **Logowanie:**
    *   Upewnić się, że odpowiednie logi są generowane, szczególnie w przypadku błędów 500.

Stosując się do `python-general-principles.mdc`, kod powinien być modularny, z preferencją dla funkcji i unikania niepotrzebnych klas. Interakcje z bazą danych powinny być zgodne z `database-interaction-rules.mdc` (asynchroniczne). Obsługa błędów powinna być zgodna z `error-handling-rules.mdc`. 