
<conversation_summary>
<decisions>
1.  Tabela `user_profiles` nie jest potrzebna; pole `last_sign_in_at` z `auth.users` (Supabase) jest wystarczające do śledzenia ostatniego logowania. Dodatkowe pola profilowe jak `created_at` są również w `auth.users`.
2.  Statusy fiszek i ich źródła będą zarządzane przez dwie osobne kolumny (`source` i `status`) w tabeli `flashcards`, z logiką `CHECK constraints` do walidacji ich kombinacji.
3.  Fiszki generowane przez AI będą miały bezpośrednie powiązanie z tabelą `source_texts` poprzez `flashcards.source_text_id`.
4.  Dla algorytmu powtórek (spaced repetition) zostaną zarezerwowane generyczne pola w tabeli `user_flashcard_spaced_repetition`: `due_date` (domyślnie `NOW()`), `current_interval` (domyślnie 1), `last_reviewed_at` (domyślnie `NULL`), oraz `data_extra` (JSONB) na przyszłe potrzeby.
5.  Statystyki generowania fiszek będą przechowywane w tabeli `ai_generation_events` jako logi poszczególnych operacji, w tym `generated_cards_count`, `accepted_cards_count`, `rejected_cards_count` i `cost`. Liczniki `accepted_cards_count` i `rejected_cards_count` będą aktualizowane po każdej akceptacji/odrzuceniu/edycji fiszki AI.
6.  Przyjęto strategię "hard delete" z wykorzystaniem `ON DELETE CASCADE` dla większości relacji z danymi użytkownika. Dla relacji `flashcards.source_text_id` do `source_texts.id` przyjęto `ON DELETE SET NULL`.
7.  Tekst wsadowy do generowania fiszek będzie zapisywany w tabeli `source_texts`. Metadane takie jak długość tekstu nie będą tam przechowywane, gdyż są w `ai_generation_events`.
8.  Nie ma potrzeby implementowania dodatkowych ról administracyjnych ani specjalnych scenariuszy RLS poza tym, że użytkownik ma dostęp tylko do swoich danych.
9.  Nie przewidziano limitów liczby fiszek na użytkownika w MVP.
10. Kolumny `created_at` i `updated_at` (z automatyczną aktualizacją przez trigger) będą dodane do większości tabel.
11. Rozróżnienie między fiszkami stworzonymi manualnie a tymi z AI będzie realizowane przez kolumnę `source` w tabeli `flashcards`.
12. Edycja fiszki AI (z `pending_review`) zmienia jej status na `active` i aktualizuje licznik `accepted_cards_count`.
13. Ograniczenia długości dla `front_content` (VARCHAR(500)) i `back_content` (VARCHAR(1000)) w tabeli `flashcards` są akceptowalne.
14. Koszt operacji AI (`cost` w `ai_generation_events`) będzie typu `NUMERIC(10,4)`.
15. Nie ma potrzeby tworzenia dedykowanych widoków (views) dla statystyk w MVP; surowa tabela `ai_generation_events` wystarczy.
</decisions>

<matched_recommendations>
1.  Wykorzystanie wbudowanej tabeli `auth.users` z Supabase do zarządzania użytkownikami i ich podstawowymi danymi (ID, email, `created_at`, `last_sign_in_at`).
2.  Stworzenie tabel: `source_texts` (na teksty wsadowe), `flashcards` (na fiszki), `ai_generation_events` (na logi generowania AI), `user_flashcard_spaced_repetition` (na dane do algorytmu powtórek).
3.  Użycie `UUID` jako kluczy głównych dla tabel.
4.  Zastosowanie typów `ENUM` dla statusów (`active`, `pending_review`, `rejected`) i źródeł (`manual`, `ai_suggestion`) fiszek.
5.  Implementacja `CHECK constraints` w tabeli `flashcards` w celu zapewnienia spójności danych dotyczących źródła, statusu i powiązania z tekstem źródłowym.
6.  Dodanie kolumn `created_at` (DEFAULT `NOW()`) i `updated_at` (aktualizowanej przez trigger) do kluczowych tabel.
7.  Implementacja Row Level Security (RLS) dla wszystkich tabel przechowujących dane użytkownika, zapewniając dostęp tylko właścicielowi danych (`auth.uid() = user_id`).
8.  Zdefiniowanie polityk `ON DELETE` (głównie `CASCADE` dla danych użytkownika, `SET NULL` dla `flashcards.source_text_id` przy usuwaniu `source_texts`).
9.  Dodanie indeksów na kluczach obcych oraz na kolumnach często używanych w zapytaniach (np. `user_flashcard_spaced_repetition.due_date`).
10. Zdefiniowanie kolumny `cost` (NUMERIC) w `ai_generation_events` oraz kolumn `accepted_cards_count` i `rejected_cards_count`.
11. Ustawienie domyślnych wartości dla pól w `user_flashcard_spaced_repetition` (`due_date` = `NOW()`, `current_interval` = 1, `last_reviewed_at` = `NULL`).
12. Ustalenie rozsądnych limitów długości (VARCHAR) dla treści fiszek.
</matched_recommendations>

<database_planning_summary>
**Główne wymagania dotyczące schematu bazy danych:**
Schemat bazy danych dla MVP aplikacji 10x-cards musi wspierać uwierzytelnianie użytkowników, przechowywanie fiszek (tworzonych ręcznie i generowanych przez AI), zarządzanie tekstami źródłowymi dla AI, śledzenie procesu generowania fiszek przez AI (w tym statystyki i koszty) oraz integrację z systemem powtórek (spaced repetition). Bezpieczeństwo danych i prywatność użytkownika są kluczowe.

**Kluczowe encje i ich relacje:**
1.  **`auth.users` (Supabase):** Przechowuje dane uwierzytelniające użytkowników (`id`, `email`, `created_at`, `last_sign_in_at`). Stanowi centralny punkt odniesienia dla danych użytkownika.
2.  **`source_texts`:** Przechowuje teksty wklejane przez użytkowników, które służą jako wsad do generowania fiszek przez AI. Każdy rekord jest powiązany z `user_id`.
    *   Relacja: Jeden użytkownik (`auth.users`) może mieć wiele tekstów źródłowych (`source_texts`).
3.  **`flashcards`:** Główna tabela przechowująca fiszki. Zawiera treść (`front_content`, `back_content`), źródło (`manual` lub `ai_suggestion`), status (`active`, `pending_review`, `rejected`) oraz powiązanie z użytkownikiem (`user_id`) i opcjonalnie z tekstem źródłowym (`source_text_id`).
    *   Relacje:
        *   Jeden użytkownik (`auth.users`) może mieć wiele fiszek.
        *   Jeden tekst źródłowy (`source_texts`) może być podstawą do wygenerowania wielu fiszek (dla `source='ai_suggestion'`).
4.  **`ai_generation_events`:** Loguje każde zdarzenie generowania fiszek przez AI. Przechowuje informacje o użytym tekście źródłowym (`source_text_id`), liczbie wygenerowanych, zaakceptowanych i odrzuconych fiszek, użytym modelu LLM oraz koszcie operacji. Powiązana z `user_id`.
    *   Relacje:
        *   Jeden użytkownik (`auth.users`) może mieć wiele zdarzeń generowania.
        *   Jeden tekst źródłowy (`source_texts`) może być powiązany z wieloma zdarzeniami generowania (choć typowo będzie to jedno zdarzenie per unikalny wsad tekstowy do AI).
5.  **`user_flashcard_spaced_repetition`:** Przechowuje dane potrzebne algorytmowi powtórek dla każdej fiszki danego użytkownika (np. `due_date`, `current_interval`, `last_reviewed_at`).
    *   Relacje: Stanowi tabelę łączącą użytkownika i fiszkę (`user_id`, `flashcard_id`) dla celów nauki. Jedna fiszka może mieć jeden wpis w tej tabeli per użytkownik.

**Ważne kwestie dotyczące bezpieczeństwa i skalowalności:**
*   **Bezpieczeństwo:**
    *   Wykorzystanie wbudowanego systemu uwierzytelniania Supabase.
    *   Implementacja Row Level Security (RLS) na wszystkich tabelach zawierających dane użytkowników, ograniczając dostęp tylko do właściciela danych (polityki oparte na `auth.uid()`).
    *   Polityki `ON DELETE` (głównie `CASCADE` dla danych powiązanych z użytkownikiem) zapewniają spójne usuwanie danych na żądanie użytkownika (hard delete).
*   **Skalowalność:**
    *   Użycie `UUID` jako kluczy głównych pomaga w dystrybucji danych i unikaniu kolizji w przyszłości.
    *   Indeksowanie kluczowych kolumn (klucze obce, kolumny używane w warunkach `WHERE` i `ORDER BY`) w celu optymalizacji zapytań.
    *   Oddzielenie logów zdarzeń AI (`ai_generation_events`) od głównych tabel operacyjnych.

**Wszelkie nierozwiązane kwestie lub obszary wymagające dalszego wyjaśnienia:**
Na tym etapie większość kluczowych decyzji dotyczących schematu bazy danych dla MVP została podjęta. Ostatnie decyzje zostały podjęte przez asystenta AI na prośbę użytkownika. Kluczowe będzie teraz zaimplementowanie tego schematu, w tym triggerów, funkcji i polityk RLS, oraz przetestowanie go pod kątem wymagań funkcjonalnych.

Potencjalne obszary do dalszego rozważenia *poza MVP* lub podczas implementacji:
*   Dokładna implementacja logiki aktualizacji liczników `accepted_cards_count` i `rejected_cards_count` w `ai_generation_events` w kodzie aplikacyjnym, aby zapewnić spójność przy różnych akcjach użytkownika (akceptacja, odrzucenie, edycja sugestii AI).
*   Szczegółowa integracja z wybraną biblioteką/algorytmem Spaced Repetition i ewentualne dostosowanie pól w `user_flashcard_spaced_repetition.data_extra`.
</database_planning_summary>

<unresolved_issues>
Brak jawnie nierozwiązanych kwestii zgłoszonych przez użytkownika w ostatniej interakcji. Asystent AI podjął ostateczne decyzje dotyczące otwartych punktów, aby przygotować finalne podsumowanie.
</unresolved_issues>
</conversation_summary>
