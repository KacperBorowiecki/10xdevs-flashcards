# Plan implementacji widoku Moje fiszki

## 1. Przegląd
Widok "Moje fiszki" to centralny panel zarządzania wszystkimi fiszkami użytkownika. Umożliwia przeglądanie, edycję, usuwanie i ręczne tworzenie fiszek. Widok wyświetla fiszki w układzie kart z możliwością filtrowania według źródła (ręczne/AI) oraz z paginacją dla dużych zbiorów danych. Dla fiszek pochodzących z AI wyświetlany jest subtelny znaczek robota.

## 2. Routing widoku
**Ścieżka**: `/my-flashcards`
**Metoda HTTP**: GET
**Template**: `templates/my_flashcards.html`
**Route handler**: `flashcards_view_router.py` w katalogu routerów

## 3. Struktura komponentów

### Hierarchia komponentów:
```
my_flashcards.html (main template)
├── partials/filter_controls.html
├── partials/empty_state.html (conditional)
├── partials/flashcard_grid.html
│   └── partials/flashcard_card.html (dla każdej fiszki)
│       ├── partials/ai_badge.html (conditional)
│       └── partials/flashcard_actions.html
├── partials/pagination.html
├── modals/create_flashcard_modal.html
├── modals/edit_flashcard_modal.html
└── modals/confirm_delete_modal.html
```

## 4. Szczegóły komponentów

### FlashcardsListView (my_flashcards.html)
- **Opis**: Główny template widoku zawierający layout strony, nagłówek z tytułem i przyciskiem dodawania fiszki
- **Główne elementy**: 
  - Header z tytułem "Moje fiszki" i przyciskiem "Dodaj fiszkę"
  - Kontener na filtry
  - Grid/lista fiszek lub stan pusty
  - Paginacja (jeśli dotyczy)
  - Wszystkie modale
- **Obsługiwane interakcje**: 
  - Kliknięcie "Dodaj fiszkę" - otwiera modal tworzenia
  - Inicjalizacja stanu strony
- **Obsługiwana walidacja**: Sprawdzenie czy użytkownik jest zalogowany
- **Typy**: FlashcardsPageData, FilterState, PaginationState
- **Propsy**: dane z backendu (lista fiszek, filtry, paginacja)

### FilterControls (partials/filter_controls.html)
- **Opis**: Kontrolki filtrowania pozwalające na wybór źródła fiszek (wszystkie/ręczne/AI)
- **Główne elementy**: 
  - Radio buttons lub select dla źródła
  - Opcjonalnie: sorting options
- **Obsługiwane interakcje**: 
  - Zmiana filtra źródła - przeładowanie strony z nowym filtrem
- **Obsługiwana walidacja**: Walidacja poprawnych wartości source enum
- **Typy**: FilterState
- **Propsy**: current_source_filter, available_sources

### FlashcardCard (partials/flashcard_card.html)
- **Opis**: Karta pojedynczej fiszki wyświetlająca front_content z opcjami zarządzania
- **Główne elementy**:
  - Card wrapper z odpowiednim padding i shadow
  - Front content (skrócony jeśli za długi)
  - AI badge (jeśli source = ai_suggestion)
  - Akcje: podgląd, edycja, usuwanie
- **Obsługiwane interakcje**:
  - Kliknięcie na kartę - rozwijanie do podglądu back_content
  - Hover effects dla lepszego UX
- **Obsługiwana walidacja**: Sprawdzenie czy fiszka należy do użytkownika
- **Typy**: FlashcardResponse
- **Propsy**: flashcard_data

### AIBadge (partials/ai_badge.html)
- **Opis**: Subtelny znaczek robota w prawym górnym rogu karty dla fiszek z AI
- **Główne elementy**: Ikona robota lub tekst "AI" z odpowiednim stylingiem
- **Obsługiwane interakcje**: Tooltip pokazujący "Wygenerowane przez AI"
- **Obsługiwana walidacja**: Wyświetlanie tylko dla source = ai_suggestion
- **Typy**: brak (renderowany warunkowo)
- **Propsy**: flashcard.source

### FlashcardActions (partials/flashcard_actions.html)
- **Opis**: Dropdown lub przyciski akcji dla pojedynczej fiszki
- **Główne elementy**:
  - Przycisk/ikona menu
  - Lista akcji: Edytuj, Usuń
- **Obsługiwane interakcje**:
  - Kliknięcie Edytuj - otwiera modal edycji z danymi fiszki
  - Kliknięcie Usuń - otwiera modal potwierdzenia
- **Obsługiwana walidacja**: Sprawdzenie uprawnień użytkownika
- **Typy**: brak (operuje na ID fiszki)
- **Propsy**: flashcard_id

### EmptyState (partials/empty_state.html)
- **Opis**: Stan pusty wyświetlany gdy użytkownik nie ma jeszcze żadnych fiszek
- **Główne elementy**:
  - Ikona/ilustracja
  - Tekst zachęcający "Nie masz jeszcze żadnych fiszek"
  - Przycisk CTA "Wygeneruj fiszki z AI"
  - Opcjonalnie: link do ręcznego tworzenia
- **Obsługiwane interakcje**:
  - Kliknięcie "Wygeneruj fiszki z AI" - przekierowanie do /generate
  - Kliknięcie "Utwórz ręcznie" - otwiera modal tworzenia
- **Obsługiwana walidacja**: Wyświetlanie tylko gdy brak fiszek
- **Typy**: brak
- **Propsy**: brak

### Pagination (partials/pagination.html)
- **Opis**: Nawigacja między stronami dla dużych zbiorów fiszek
- **Główne elementy**:
  - Numery stron
  - Przyciski Previous/Next
  - Informacja o aktualnej stronie i łącznej liczbie
- **Obsługiwane interakcje**:
  - Kliknięcie numeru strony - przejście do strony
  - Previous/Next navigation
- **Obsługiwana walidacja**: Sprawdzenie czy strona jest w prawidłowym zakresie
- **Typy**: PaginationData
- **Propsy**: current_page, total_pages, has_next, has_previous

### CreateFlashcardModal (modals/create_flashcard_modal.html)
- **Opis**: Modal do ręcznego tworzenia nowej fiszki
- **Główne elementy**:
  - Formularz z polami front_content i back_content
  - Textarea z licznikami znaków
  - Przyciski Zapisz i Anuluj
- **Obsługiwane interakcje**:
  - Walidacja na bieżąco podczas wpisywania
  - Submit - wysłanie POST /flashcards
  - Anuluj/ESC - zamknięcie modala
- **Obsługiwana walidacja**:
  - front_content: wymagane, max 500 znaków
  - back_content: wymagane, max 1000 znaków
- **Typy**: FlashcardManualCreateRequest
- **Propsy**: brak (czysty formularz)

### EditFlashcardModal (modals/edit_flashcard_modal.html)
- **Opis**: Modal do edycji istniejącej fiszki
- **Główne elementy**:
  - Formularz ze wstępnie wypełnionymi danymi fiszki
  - Textarea z licznikami znaków
  - Przyciski Zapisz i Anuluj
- **Obsługiwane interakcje**:
  - Walidacja na bieżąco podczas edycji
  - Submit - wysłanie PATCH /flashcards/{id}
  - Anuluj/ESC - zamknięcie modala
- **Obsługiwana walidacja**:
  - front_content: wymagane, max 500 znaków
  - back_content: wymagane, max 1000 znaków
- **Typy**: FlashcardPatchRequest, FlashcardResponse
- **Propsy**: flashcard_data (do wypełnienia formularza)

### ConfirmDeleteModal (modals/confirm_delete_modal.html)
- **Opis**: Modal potwierdzenia usunięcia fiszki
- **Główne elementy**:
  - Tytuł i opis operacji
  - Podgląd fiszki do usunięcia (front_content)
  - Przyciski Usuń i Anuluj
- **Obsługiwane interakcje**:
  - Potwierdzenie - wysłanie DELETE /flashcards/{id}
  - Anuluj/ESC - zamknięcie modala
- **Obsługiwana walidacja**: Sprawdzenie czy fiszka istnieje
- **Typy**: FlashcardResponse (do wyświetlenia podglądu)
- **Propsy**: flashcard_data

## 5. Typy

### FlashcardsPageData
```python
class FlashcardsPageData(BaseModel):
    flashcards: PaginatedFlashcardsResponse
    current_filter: FilterState
    page_meta: Dict[str, Any]
```

### FilterState
```python
class FilterState(BaseModel):
    source: Optional[FlashcardSourceEnum] = None
    page: int = 1
    size: int = 20
```

### PaginationData
```python
class PaginationData(BaseModel):
    current_page: int
    total_pages: int
    has_previous: bool
    has_next: bool
    total_items: int
```

### FlashcardCardViewModel
```python
class FlashcardCardViewModel(BaseModel):
    id: uuid.UUID
    front_content: str
    back_content: str
    source: FlashcardSourceEnum
    is_ai_generated: bool
    created_at: datetime
    truncated_front: str  # dla długich treści
```

## 6. Zarządzanie stanem

Stan zarządzany jest głównie po stronie serwera z wykorzystaniem:
- **Query parameters** dla filtrów i paginacji (source, page, size)
- **Session storage** dla zachowania preferowanych filtrów między wizytami
- **JavaScript state** dla modalów (otwarte/zamknięte, loading states)
- **HTMX** dla dynamicznych aktualizacji bez pełnego przeładowania (opcjonalnie)

### Lokalny stan JavaScript:
```javascript
const pageState = {
    modals: {
        create: false,
        edit: false,
        delete: false
    },
    loading: {
        delete: false,
        create: false,
        edit: false
    },
    currentFlashcard: null // dla modalów edycji/usuwania
};
```

## 7. Integracja API

### Endpointy używane przez widok:
- **GET /api/v1/flashcards** - pobieranie listy fiszek z filtrami
  - Query params: status=active, source?, page, size
  - Response: PaginatedFlashcardsResponse
- **POST /api/v1/flashcards** - tworzenie nowej fiszki
  - Request: FlashcardManualCreateRequest
  - Response: FlashcardResponse
- **PATCH /api/v1/flashcards/{id}** - edycja fiszki
  - Request: FlashcardPatchRequest
  - Response: FlashcardResponse
- **DELETE /api/v1/flashcards/{id}** - usuwanie fiszki  
  - Response: 204 No Content

### Integracja w template:
```python
# W route handlerze
@router.get("/my-flashcards")
async def my_flashcards_view(
    request: Request,
    source: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user_id: UUID = Depends(get_current_user_id)
):
    # Wywołanie API dla pobrania fiszek
    flashcards_response = await api_client.get_flashcards(
        status="active", 
        source=source, 
        page=page, 
        size=size
    )
    
    return templates.TemplateResponse("my_flashcards.html", {
        "request": request,
        "flashcards": flashcards_response,
        "current_filter": {"source": source, "page": page, "size": size}
    })
```

## 8. Interakcje użytkownika

### Główne przepływy interakcji:

1. **Przeglądanie fiszek**:
   - Użytkownik wchodzi na /my-flashcards
   - System pobiera fiszki z API z domyślnymi filtrami
   - Wyświetlana jest lista/grid fiszek lub stan pusty

2. **Filtrowanie**:
   - Użytkownik wybiera filtr źródła (wszystkie/ręczne/AI)
   - Strona przeładowuje się z nowym parametrem source
   - Lista aktualizuje się zgodnie z filtrem

3. **Paginacja**:
   - Użytkownik klika numer strony lub Next/Previous
   - Strona przeładowuje się z nowym parametrem page
   - Lista wyświetla fiszki z wybranej strony

4. **Tworzenie fiszki**:
   - Kliknięcie "Dodaj fiszkę" → otwiera CreateFlashcardModal
   - Wypełnienie formularza → walidacja na żywo
   - Submit → POST /flashcards → zamknięcie modala → odświeżenie listy

5. **Edycja fiszki**:
   - Kliknięcie "Edytuj" → otwiera EditFlashcardModal z danymi fiszki
   - Modyfikacja treści → walidacja na żywo
   - Submit → PATCH /flashcards/{id} → zamknięcie modala → odświeżenie listy

6. **Usuwanie fiszki**:
   - Kliknięcie "Usuń" → otwiera ConfirmDeleteModal z podglądem fiszki
   - Potwierdzenie → DELETE /flashcards/{id} → zamknięcie modala → odświeżenie listy

## 9. Warunki i walidacja

### Walidacja po stronie klienta:
- **front_content**: wymagane, 1-500 znaków, trim whitespace
- **back_content**: wymagane, 1-1000 znaków, trim whitespace
- **source filter**: enum validation (manual, ai_suggestion)
- **page**: integer ≥ 1
- **size**: integer 1-100

### Warunki wyświetlania:
- **AI Badge**: tylko gdy flashcard.source === "ai_suggestion"
- **Empty State**: gdy flashcards.items.length === 0
- **Pagination**: gdy flashcards.pages > 1
- **Loading states**: podczas wywołań API

### Walidacja bezpieczeństwa:
- JWT token wymagany dla wszystkich operacji
- CSRF protection w formularzach
- Rate limiting na operacjach (zaimplementowane w API)
- Input sanitization przed wysłaniem

## 10. Obsługa błędów

### Scenariusze błędów i obsługa:

1. **Błąd sieci/timeout**:
   - Toast notification: "Problemy z połączeniem. Spróbuj ponownie."
   - Retry button w przypadku krytycznych operacji

2. **401 Unauthorized**:
   - Przekierowanie do strony logowania
   - Zachowanie aktualnego URL dla powrotu po logowaniu

3. **404 Not Found** (fiszka nie istnieje):
   - Toast notification: "Fiszka nie została znaleziona"
   - Odświeżenie listy (usunięcie nieistniejącej fiszki z UI)

4. **422 Validation Error**:
   - Wyświetlenie błędów walidacji pod odpowiednimi polami formularza
   - Highlight niepoprawnych pól

5. **429 Rate Limit**:
   - Toast notification z informacją o limitach
   - Tymczasowe wyłączenie przycisków akcji

6. **500 Server Error**:
   - Toast notification: "Wystąpił błąd serwera. Spróbuj ponownie później."
   - Log error details dla debugowania

### Implementacja obsługi błędów:
```javascript
async function handleApiCall(apiCall, successMessage) {
    try {
        showLoading(true);
        const result = await apiCall();
        showToast(successMessage, 'success');
        return result;
    } catch (error) {
        const errorMessage = getErrorMessage(error.status);
        showToast(errorMessage, 'error');
        
        if (error.status === 401) {
            window.location.href = '/login';
        }
    } finally {
        showLoading(false);
    }
}
```

## 11. Kroki implementacji

1. **Przygotowanie struktury**:
   - Utworzenie routera widoku w `routers/flashcards_view_router.py`
   - Utworzenie głównego template `templates/my_flashcards.html`
   - Struktury katalogów dla partials i modals

2. **Implementacja głównego widoku**:
   - Route handler z integracją API flashcards
   - Logika filtrowania i paginacji
   - Template z podstawową strukturą HTML

3. **Komponenty bazowe**:
   - FlashcardCard partial z wyświetlaniem podstawowych danych
   - FilterControls dla wyboru źródła
   - Pagination component

4. **Stany specjalne**:
   - EmptyState dla braku fiszek
   - Loading states
   - Error states

5. **Modale i formularze**:
   - CreateFlashcardModal z walidacją
   - EditFlashcardModal z prefill danych
   - ConfirmDeleteModal

6. **JavaScript i interaktywność**:
   - Event handlers dla modalów
   - AJAX calls dla operacji CRUD
   - Client-side validation
   - Toast notifications

7. **Stylowanie i UX**:
   - Tailwind CSS classes dla layoutu i komponentów
   - Responsive design (desktop-first zgodnie z wymaganiami)
   - Hover states i animacje
   - Accessibility (focus states, ARIA labels)

8. **Integracja i testowanie**:
   - Połączenie z istniejącymi API endpoints
   - Testowanie wszystkich przepływów użytkownika
   - Error handling scenarios
   - Performance optimization

9. **Polishing**:
   - Keyboard shortcuts (ESC dla modalów)
   - Tooltips i help texts
   - Loading states optimization
   - Final UX review

10. **Dokumentacja**:
    - Komentarze w kodzie
    - Dokumentacja dla przyszłych deweloperów
    - README z instrukcjami uruchomienia 