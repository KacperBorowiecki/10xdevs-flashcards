# Plan implementacji widoku Generowanie fiszek AI

## 1. Przegląd
Widok "Generowanie fiszek AI" jest główną funkcją aplikacji 10x-cards, umożliwiającą użytkownikom automatyczne generowanie fiszek edukacyjnych z tekstu przy użyciu AI. Użytkownik wprowadza tekst (1000-10000 znaków), aplikacja wysyła go do API LLM, a następnie prezentuje propozycje fiszek do zatwierdzenia, edycji lub odrzucenia. Widok obsługuje real-time walidację, loading states, obsługę błędów oraz optimistic updates dla lepszego UX.

## 2. Routing widoku
Widok dostępny pod ścieżką `/generate` w systemie routingu FastAPI z Jinja2. Wymaga uwierzytelnienia użytkownika (redirect do `/login` jeśli niezalogowany).

## 3. Struktura komponentów
```
GenerateFlashcardsView (main container)
├── PageHeader (title + breadcrumb)
├── TextInputForm (main form)
│   ├── TextareaWithCounter (input + validation)
│   └── GenerateButton (submit with loading)
├── LoadingSpinner (conditional, during generation)
├── FlashcardSuggestionsList (conditional, after generation)
│   └── FlashcardSuggestionCard[] (repeatable)
│       ├── CardPreview (front/back display)
│       └── ActionButtons (accept/edit/reject)
├── EditFlashcardModal (conditional, for editing)
│   ├── ModalHeader
│   ├── EditForm (front/back fields)
│   └── ModalActions (save/cancel)
└── ToastNotification (conditional, feedback)
```

## 4. Szczegóły komponentów

### GenerateFlashcardsView
- **Opis**: Główny kontener widoku, zarządza stanem całej strony i koordynuje komunikację między komponentami
- **Główne elementy**: PageContainer, grid layout, sidebar integration, conditional rendering
- **Obsługiwane interakcje**: Inicjalizacja widoku, obsługa błędów globalnych, nawigacja
- **Obsługiwana walidacja**: Weryfikacja uwierzytelnienia użytkownika
- **Typy**: GenerateFlashcardsViewModel, ToastMessage
- **Propsy**: Brak (root component)

### TextInputForm  
- **Opis**: Formularz zawierający pole tekstowe i przycisk generowania, obsługuje walidację input'u
- **Główne elementy**: `<form>`, TextareaWithCounter, GenerateButton, ValidationMessage
- **Obsługiwane interakcje**: Submit formularza, walidacja on-change, preventDefault
- **Obsługiwana walidacja**: Długość tekstu 1000-10000 znaków, wymagane pole, trim whitespace
- **Typy**: TextInputState, ValidationError[]
- **Propsy**: `{ onSubmit: (text: string) => void, isGenerating: boolean, initialText?: string }`

### TextareaWithCounter
- **Opis**: Textarea z live counter znaków i real-time walidacją, wizualna informacja o limicie
- **Główne elementy**: `<textarea>`, `<div>` counter, `<span>` validation states
- **Obsługiwane interakcje**: onChange, onBlur, onFocus, keyboard shortcuts
- **Obsługiwana walidacja**: Minimum 1000 znaków, maksimum 10000 znaków, real-time feedback
- **Typy**: TextareaState, CharacterCount
- **Propsy**: `{ value: string, onChange: (value: string) => void, minLength: number, maxLength: number, placeholder?: string, disabled?: boolean }`

### GenerateButton
- **Opis**: Przycisk submit z loading state i walidacją, disabled gdy kryteria nie spełnione
- **Główne elementy**: `<button>`, LoadingSpinner (inline), tekst dynamiczny
- **Obsługiwane interakcje**: onClick, hover states, focus states
- **Obsługiwana walidacja**: Wyłączenie gdy tekst nieprawidłowy lub generowanie w toku
- **Typy**: ButtonState
- **Propsy**: `{ isLoading: boolean, disabled: boolean, onClick: () => void, text?: string }`

### FlashcardSuggestionsList
- **Opis**: Kontener listy wygenerowanych propozycji fiszek, obsługuje empty state
- **Główne elementy**: Grid layout, FlashcardSuggestionCard components, EmptyState
- **Obsługiwane interakcje**: Renderowanie listy, scroll handling
- **Obsługiwana walidacja**: Brak
- **Typy**: FlashcardSuggestion[], ListState
- **Propsy**: `{ suggestions: FlashcardSuggestion[], onAccept: (id: string) => void, onEdit: (card: FlashcardSuggestion) => void, onReject: (id: string) => void }`

### FlashcardSuggestionCard
- **Opis**: Pojedyncza karta propozycji z preview treści i akcjami, hover effects
- **Główne elementy**: Card container, CardPreview, ActionButtons, status indicators
- **Obsługiwane interakcje**: Hover, click actions, keyboard navigation
- **Obsługiwana walidacja**: Weryfikacja czy akcje są dostępne
- **Typy**: FlashcardSuggestion, CardActions
- **Propsy**: `{ suggestion: FlashcardSuggestion, onAccept: () => void, onEdit: () => void, onReject: () => void, isProcessing?: boolean }`

### EditFlashcardModal
- **Opis**: Modal do edycji treści fiszki przed akceptacją, pełna walidacja formularza
- **Główne elementy**: Modal overlay, modal dialog, form fields, action buttons
- **Obsługiwane interakcje**: Otwieranie/zamykanie, walidacja pól, submit, ESC key
- **Obsługiwana walidacja**: front_content (max 500 znaków), back_content (max 1000 znaków), required fields
- **Typy**: EditFlashcardData, ModalState, ValidationErrors
- **Propsy**: `{ isOpen: boolean, flashcard: FlashcardSuggestion | null, onSave: (data: EditFlashcardData) => void, onCancel: () => void }`

### ToastNotification
- **Opis**: Komponent powiadomień dla feedback operacji, auto-dismiss funkcjonalność
- **Główne elementy**: Toast container, message text, close button, progress bar
- **Obsługiwane interakcje**: Auto-dismiss, manual dismiss, click actions
- **Obsługiwana walidacja**: Brak
- **Typy**: ToastMessage, ToastType
- **Propsy**: `{ message: ToastMessage | null, onDismiss: () => void, duration?: number }`

## 5. Typy

### GenerateFlashcardsViewModel
```typescript
interface GenerateFlashcardsViewModel {
  textContent: string;
  isGenerating: boolean;
  suggestions: FlashcardSuggestion[];
  editingCard: FlashcardSuggestion | null;
  toastMessage: ToastMessage | null;
  errors: ValidationError[];
  hasGeneratedResults: boolean;
}
```

### FlashcardSuggestion
```typescript
interface FlashcardSuggestion {
  id: string;
  user_id: string;
  source_text_id: string;
  front_content: string;
  back_content: string;
  source: 'ai_suggestion';
  status: 'pending_review' | 'active' | 'rejected';
  created_at: string;
  updated_at: string;
  isProcessing?: boolean; // local state dla optimistic updates
}
```

### TextInputState
```typescript
interface TextInputState {
  value: string;
  characterCount: number;
  isValid: boolean;
  errors: string[];
  isDirty: boolean;
}
```

### EditFlashcardData
```typescript
interface EditFlashcardData {
  front_content: string;
  back_content: string;
  validation: {
    front_content: ValidationResult;
    back_content: ValidationResult;
  };
}
```

### ToastMessage
```typescript
interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  action?: {
    text: string;
    onClick: () => void;
  };
}
```

### ValidationError
```typescript
interface ValidationError {
  field: string;
  message: string;
  code: string;
}
```

## 6. Zarządzanie stanem

### Custom Hook: useGenerateFlashcards
```typescript
const useGenerateFlashcards = () => {
  const [state, setState] = useState<GenerateFlashcardsViewModel>({
    textContent: '',
    isGenerating: false,
    suggestions: [],
    editingCard: null,
    toastMessage: null,
    errors: [],
    hasGeneratedResults: false
  });

  // Funkcje zarządzania stanem
  const generateFlashcards = async (textContent: string) => { ... };
  const acceptSuggestion = async (suggestionId: string) => { ... };
  const rejectSuggestion = async (suggestionId: string) => { ... };
  const editSuggestion = (suggestion: FlashcardSuggestion) => { ... };
  const saveEditedCard = async (data: EditFlashcardData) => { ... };
  const showToast = (message: ToastMessage) => { ... };
  const dismissToast = () => { ... };

  return {
    ...state,
    generateFlashcards,
    acceptSuggestion,
    rejectSuggestion,
    editSuggestion,
    saveEditedCard,
    showToast,
    dismissToast
  };
};
```

Stan zarządzany jest w jednym miejscu za pomocą custom hook'a, który enkapsuluje całą logikę biznesową i komunikację z API. Wykorzystuje useReducer wewnętrznie dla complex state updates.

## 7. Integracja API

### Generate Flashcards API Call
- **Endpoint**: `POST /ai/generate-flashcards`
- **Request Type**: `AIGenerateFlashcardsRequest`
```typescript
interface AIGenerateFlashcardsRequest {
  text_content: string; // 1000-10000 znaków
}
```
- **Response Type**: `AIGenerateFlashcardsResponse`
```typescript
interface AIGenerateFlashcardsResponse {
  source_text_id: string;
  ai_generation_event_id: string;
  suggested_flashcards: FlashcardSuggestion[];
}
```

### Update Flashcard Status API Call
- **Endpoint**: `PATCH /flashcards/{flashcard_id}`
- **Request Type**: `FlashcardPatchRequest`
```typescript
interface FlashcardPatchRequest {
  front_content?: string;
  back_content?: string;
  status?: 'active' | 'rejected';
}
```
- **Response Type**: `FlashcardResponse`

### Error Handling dla API
- **400 Bad Request**: Nieprawidłowe dane wejściowe
- **401 Unauthorized**: Brak uwierzytelnienia
- **422 Unprocessable Entity**: Błąd walidacji (tekst poza zakresem 1000-10000 znaków)
- **503 Service Unavailable**: LLM service niedostępny/timeout
- **500 Internal Server Error**: Błąd serwera

## 8. Interakcje użytkownika

### Scenariusz 1: Wprowadzanie tekstu
1. Użytkownik klika w textarea
2. Zaczyna wpisywać tekst
3. Real-time licznik pokazuje aktualną liczbę znaków
4. Walidacja uruchamia się po 500ms debounce
5. Komunikaty walidacji aktualizują się na bieżąco
6. Przycisk "Generuj" staje się aktywny gdy tekst ma 1000-10000 znaków

### Scenariusz 2: Generowanie fiszek
1. Użytkownik klika przycisk "Generuj fiszki"
2. Przycisk zmienia się na "Generuję fiszki..." z spinner'em
3. Textarea zostaje zablokowana
4. Loading spinner pojawia się pod formularzem
5. Po otrzymaniu odpowiedzi loading znika
6. Lista propozycji pojawia się z animacją
7. Toast notification "Wygenerowano X fiszek" pojawia się na 3 sekundy

### Scenariusz 3: Zarządzanie propozycjami
1. Użytkownik widzi listę wygenerowanych fiszek
2. Każda fiszka ma preview treści (przód/tył)
3. Kliknięcie "Akceptuj" → optimistic update → fiszka znika z listy → toast "Fiszka zaakceptowana"
4. Kliknięcie "Odrzuć" → optimistic update → fiszka znika z listy → toast "Fiszka odrzucona"
5. Kliknięcie "Edytuj" → modal się otwiera z treścią fiszki

### Scenariusz 4: Edycja w modalu
1. Modal otwiera się z focus na pierwszym polu
2. Użytkownik może edytować przód i tył fiszki
3. Real-time walidacja długości pól
4. Kliknięcie "Zapisz" → walidacja → jeśli OK to zapis → zamknięcie modal → toast "Fiszka zapisana"
5. Kliknięcie "Anuluj" lub ESC → zamknięcie bez zapisywania
6. Kliknięcie poza modal → confirmation dialog → zamknięcie

## 9. Warunki i walidacja

### Walidacja pola tekstowego (TextareaWithCounter)
- **Minimum 1000 znaków**: Komunikat "Tekst musi mieć co najmniej 1000 znaków"
- **Maksimum 10000 znaków**: Komunikat "Tekst nie może przekraczać 10000 znaków" + blokada wpisywania
- **Puste pole**: Komunikat "To pole jest wymagane"
- **Tylko białe znaki**: Komunikat "Tekst nie może składać się tylko z białych znaków"

### Walidacja modalu edycji (EditFlashcardModal)
- **front_content**: Wymagane, max 500 znaków, min 1 znak
- **back_content**: Wymagane, max 1000 znaków, min 1 znak
- **Walidacja na onChange**: Debounce 300ms, immediate feedback
- **Walidacja na submit**: Blokada zapisywania jeśli błędy

### Walidacja stanu aplikacji
- **Generowanie**: Blokada UI podczas komunikacji z API
- **Rate limiting**: Max 10 generowań na godzinę (info w error message)
- **Timeout**: 30 sekund timeout dla API call

### Wpływ walidacji na stan UI
- **Nieprawidłowy tekst**: Przycisk "Generuj" wyłączony + czerwony border textarea
- **Błędy API**: Error toast + przywrócenie poprzedniego stanu
- **Validacja modal**: Wyłączenie przycisku "Zapisz" gdy błędy

## 10. Obsługa błędów

### Błędy walidacji klienta
- **Nieprawidłowa długość tekstu**: Toast warning + highlight problematycznego pola
- **Puste wymagane pola**: Inline error messages + focus na pierwsze błędne pole
- **Przekroczenie limitu znaków**: Automatyczne przycinanie + toast info

### Błędy API
- **503 Service Unavailable**: Toast error "AI jest tymczasowo niedostępne. Spróbuj ponownie za chwilę."
- **422 Validation Error**: Toast error z konkretnym komunikatem z serwera
- **429 Rate Limit**: Toast warning "Osiągnąłeś limit generowań. Spróbuj ponownie za godzinę."
- **500 Server Error**: Toast error "Wystąpił błąd serwera. Spróbuj ponownie."
- **Network Error**: Toast error "Brak połączenia. Sprawdź internet i spróbuj ponownie."

### Błędy optimistic updates
- **Rollback na błąd**: Przywrócenie poprzedniego stanu + error toast
- **Retry mechanism**: Przycisk "Spróbuj ponownie" w error toast
- **Conflict resolution**: Sprawdzenie czy fiszka nadal istnieje przed akcją

### Scenariusze brzegowe
- **Timeout generowania**: Loading spinner + "Generowanie trwa dłużej niż zwykle..." + opcja anulowania
- **Brak propozycji**: Empty state "AI nie wygenerowało żadnych propozycji. Spróbuj z innym tekstem."
- **Częściowe powodzenie**: Info toast "Wygenerowano tylko X z Y propozycji"

## 11. Kroki implementacji

### Krok 1: Podstawowa struktura
1. Stworzenie template Jinja2 dla widoku `/generate`
2. Implementacja GenerateFlashcardsView jako głównego kontenera
3. Dodanie podstawowego routingu w FastAPI
4. Integracja z sidebar navigation (active state)

### Krok 2: Formularz wprowadzania tekstu
1. Implementacja TextInputForm z podstawową walidacją
2. Stworzenie TextareaWithCounter z licznikiem znaków
3. Dodanie GenerateButton z podstawowymi stanami
4. Implementacja real-time walidacji z debouncing

### Krok 3: Zarządzanie stanem
1. Stworzenie custom hook useGenerateFlashcards
2. Implementacja state management dla wszystkich komponentów
3. Dodanie error handling i loading states
4. Testowanie przepływu danych między komponentami

### Krok 4: Integracja z API
1. Implementacja funkcji generateFlashcards (POST /ai/generate-flashcards)
2. Dodanie error handling dla wszystkich scenariuszy API
3. Implementacja retry logic i timeout handling
4. Testowanie z rzeczywistym API

### Krok 5: Lista propozycji
1. Implementacja FlashcardSuggestionsList i FlashcardSuggestionCard
2. Dodanie CardPreview do wyświetlania treści fiszek
3. Implementacja ActionButtons z podstawowymi akcjami
4. Dodanie animacji i hover effects

### Krok 6: Operacje na propozycjach
1. Implementacja funkcji acceptSuggestion (PATCH /flashcards/{id})
2. Implementacja funkcji rejectSuggestion
3. Dodanie optimistic updates z rollback
4. Testowanie wszystkich scenariuszy akcji

### Krok 7: Modal edycji
1. Stworzenie EditFlashcardModal z pełną funkcjonalnością
2. Implementacja form handling z walidacją
3. Dodanie keyboard shortcuts (ESC, Enter)
4. Implementacja focus management i accessibility

### Krok 8: System powiadomień
1. Implementacja ToastNotification z różnymi typami
2. Dodanie auto-dismiss i manual dismiss
3. Integracja toastów z wszystkimi operacjami
4. Dodanie action buttons w toastach gdzie potrzebne

### Krok 9: Stylowanie i UX
1. Implementacja responsywnych stylów Tailwind CSS
2. Dodanie loading states i skeleton screens
3. Implementacja error states i empty states
4. Testowanie accessibility (focus, keyboard navigation)

### Krok 10: Testowanie i optymalizacja
1. Testowanie wszystkich user flows
2. Testowanie scenariuszy błędów
3. Optymalizacja performance (debouncing, memoization)
4. Finalne testy integracyjne z pełnym systemem 