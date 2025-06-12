# Plan implementacji widoku Sesja nauki

## 1. Przegląd
Widok Sesja nauki to kluczowa funkcjonalność aplikacji 10x-cards, umożliwiająca użytkownikom efektywną naukę z wykorzystaniem algorytmu spaced repetition. Widok prezentuje fiszki wymagające powtórki w kontrolowanej sekwencji, gdzie użytkownik najpierw widzi pytanie (przód fiszki), następnie może wyświetlić odpowiedź (tył fiszki), a na końcu ocenia swoje wykonanie w skali 1-5. Na podstawie oceny algorytm automatycznie planuje następną datę powtórki dla danej fiszki.

## 2. Routing widoku
**Ścieżka**: `/study-session`

## 3. Struktura komponentów
```
StudySessionView
├── ProgressIndicator
├── StudyCard
│   ├── CardFront
│   ├── CardBack
│   └── ShowAnswerButton
├── RatingScale
├── LoadingSpinner
└── EmptyState
```

## 4. Szczegóły komponentów

### StudySessionView
- **Opis komponentu**: Główny kontener widoku sesji nauki, odpowiedzialny za koordinację całego procesu uczenia się, zarządzanie stanem sesji oraz komunikację z API.
- **Główne elementy**: Container z wyśrodkowanym layoutem, zawiera wszystkie komponenty dzieci w logicznej kolejności.
- **Obsługiwane interakcje**: 
  - Inicjalizacja sesji (pobranie fiszek)
  - Nawigacja keyboard (Space, Enter, 1-5)
  - Restart sesji gdy została zakończona
- **Obsługiwana walidacja**: 
  - Sprawdzenie czy użytkownik jest zalogowany
  - Walidacja czy sesja może być rozpoczęta
  - Walidacja dostępności fiszek do powtórki
- **Typy**: StudySessionState, DueFlashcard[], LoadingState, ErrorState
- **Propsy**: Brak (root component)

### StudyCard
- **Opis komponentu**: Główny komponent wyświetlający fiszkę w stałych wymiarach 400x300px. Obsługuje przełączanie między przedem a tyłem fiszki z płynną animacją flip.
- **Główne elementy**: 
  - Div z fixed dimensions (400x300px)
  - Card container z flip animation
  - Content area dla tekstu fiszki
  - ShowAnswerButton (gdy pokazany przód)
- **Obsługiwane interakcje**:
  - Kliknięcie "Pokaż odpowiedź" → przełączenie na tył fiszki
  - Keyboard navigation (Space/Enter dla pokazania odpowiedzi)
- **Obsługiwana walidacja**:
  - Sprawdzenie czy flashcard ma wymagane pola (front_content, back_content)
  - Walidacja długości treści dla display
- **Typy**: FlashcardWithRepetition, CardSide (enum: front/back)
- **Propsy**: 
  - `flashcard: FlashcardWithRepetition`
  - `currentSide: CardSide`
  - `onShowAnswer: () => void`

### ProgressIndicator
- **Opis komponentu**: Wskaźnik postępu sesji w formacie "X/Y fiszek", pokazujący aktualną pozycję w sesji oraz całkowitą liczbę fiszek do powtórki.
- **Główne elementy**: 
  - Tekst z formatem "current/total fiszek"
  - Progress bar (opcjonalnie)
  - Styling zgodny z design system
- **Obsługiwane interakcje**: Brak (tylko display)
- **Obsługiwana walidacja**:
  - Sprawdzenie czy current <= total
  - Zabezpieczenie przed division by zero
- **Typy**: number (current), number (total)
- **Propsy**:
  - `current: number`
  - `total: number`

### RatingScale
- **Opis komponentu**: Interaktywna skala oceny od 1 do 5, umożliwiająca użytkownikowi ocenę swojego wykonania przy danej fiszce. Wyświetlana tylko gdy pokazany jest tył fiszki.
- **Główne elementy**:
  - 5 przycisków/elementów reprezentujących oceny 1-5
  - Clear visual hierarchy i hover states
  - Focus states dla keyboard navigation
- **Obsługiwane interakcje**:
  - Kliknięcie na ocenę 1-5 → wysłanie oceny i przejście do następnej fiszki
  - Keyboard navigation (1-5 keys, Tab navigation)
- **Obsługiwana walidacja**:
  - Walidacja czy rating jest w zakresie 1-5
  - Sprawdzenie czy można wysłać ocenę (nie jest już w trakcie wysyłania)
- **Typy**: number (rating 1-5), loading state
- **Propsy**:
  - `onRatingSubmit: (rating: number) => Promise<void>`
  - `isSubmitting: boolean`

### LoadingSpinner
- **Opis komponentu**: Wskaźnik ładowania wyświetlany podczas komunikacji z API (pobieranie fiszek, wysyłanie ocen).
- **Główne elementy**:
  - Spinner animation
  - Opcjonalny tekst opisujący aktualną operację
- **Obsługiwane interakcje**: Brak
- **Obsługiwana walidacja**: Brak
- **Typy**: string (loading message)
- **Propsy**:
  - `message?: string`

### EmptyState
- **Opis komponentu**: Komunikat wyświetlany gdy użytkownik nie ma fiszek do powtórki, z gratulacjami i sugestią powrotu następnego dnia.
- **Główne elementy**:
  - Ikona lub ilustracja
  - Komunikat "Dobra robota, wróć jutro!"
  - Przycisk powrotu do dashboard
- **Obsługiwane interakcje**:
  - Kliknięcie przycisku powrotu → navigation do dashboard
- **Obsługiwana walidacja**: Brak
- **Typy**: Brak (static content)
- **Propsy**:
  - `onNavigateToDashboard: () => void`

## 5. Typy

### FlashcardWithRepetition
```typescript
interface FlashcardWithRepetition {
  id: string;
  user_id: string;
  source_text_id?: string;
  front_content: string;
  back_content: string;
  source: 'manual' | 'ai_suggestion';
  status: 'active';
  created_at: string;
  updated_at: string;
  repetition_data: RepetitionData;
}
```

### RepetitionData
```typescript
interface RepetitionData {
  due_date: string;
  current_interval: number;
  last_reviewed_at?: string;
}
```

### StudySessionState
```typescript
interface StudySessionState {
  flashcards: FlashcardWithRepetition[];
  currentIndex: number;
  currentSide: CardSide;
  isLoading: boolean;
  isSubmittingRating: boolean;
  error?: string;
  sessionCompleted: boolean;
}
```

### CardSide
```typescript
enum CardSide {
  FRONT = 'front',
  BACK = 'back'
}
```

### SubmitReviewRequest
```typescript
interface SubmitReviewRequest {
  flashcard_id: string;
  performance_rating: number; // 1-5
}
```

## 6. Zarządzanie stanem
Widok wymaga niestandardowego hooka `useStudySession` do zarządzania kompleksowym stanem sesji nauki:

### useStudySession Hook
- **Inicjalizacja**: Pobiera fiszki do powtórki z API przy załadowaniu
- **Navigation**: Zarządza przechodzeniem między fiszkami i stanami (front/back)
- **Rating submission**: Obsługuje wysyłanie ocen z optimistic updates
- **Error handling**: Centralizuje obsługę błędów API
- **State persistence**: Opcjonalnie zachowuje stan sesji przy odświeżeniu

### Kluczowe zmienne stanu:
- `flashcards: FlashcardWithRepetition[]` - lista fiszek do powtórki
- `currentIndex: number` - indeks aktualnej fiszki
- `currentSide: CardSide` - aktualnie wyświetlana strona fiszki
- `isLoading: boolean` - stan ładowania
- `isSubmittingRating: boolean` - stan wysyłania oceny
- `error: string | null` - komunikat błędu
- `sessionCompleted: boolean` - czy sesja została ukończona

## 7. Integracja API

### Inicjalizacja sesji
- **Endpoint**: `GET /api/v1/spaced-repetition/due-cards?limit=20`
- **Request type**: Brak body (query params)
- **Response type**: `FlashcardWithRepetition[]`
- **Error handling**: 401 (redirect to login), 500 (error message)

### Wysyłanie oceny
- **Endpoint**: `POST /api/v1/spaced-repetition/reviews`
- **Request type**: `SubmitReviewRequest`
- **Response type**: `SpacedRepetitionReviewResponse`
- **Error handling**: 404 (fiszka nie istnieje), 422 (nieprawidłowa ocena), 500 (błąd serwera)

## 8. Interakcje użytkownika

### 1. Rozpoczęcie sesji
- Wejście na `/study-session` → automatyczne pobranie fiszek do powtórki
- Loading state podczas pobierania
- Jeśli brak fiszek → EmptyState
- Jeśli są fiszki → wyświetlenie pierwszej fiszki (front)

### 2. Wyświetlenie odpowiedzi
- Kliknięcie "Pokaż odpowiedź" → flip animation do back side
- Keyboard: Space/Enter → to samo działanie
- Wyświetlenie RatingScale po pokazaniu odpowiedzi

### 3. Ocena fiszki
- Kliknięcie oceny 1-5 → wysłanie do API
- Keyboard: klawisze 1-5 → to samo działanie
- Loading state podczas wysyłania oceny
- Po sukcesie → automatic przejście do następnej fiszki (front)

### 4. Zakończenie sesji
- Po ostatniej fiszce → wyświetlenie EmptyState z gratulacjami
- Przycisk powrotu do dashboard

## 9. Warunki i walidacja

### Warunki inicjalizacji
- **Komponent**: StudySessionView
- **Warunek**: Użytkownik musi być zalogowany (sprawdzenie JWT token)
- **Wpływ na UI**: Jeśli nie zalogowany → redirect do `/login`

### Walidacja fiszek
- **Komponent**: StudyCard
- **Warunek**: Fiszka musi mieć niepuste `front_content` i `back_content`
- **Wpływ na UI**: Jeśli brak treści → wyświetlenie placeholder lub skip

### Walidacja oceny
- **Komponent**: RatingScale
- **Warunek**: Ocena musi być w zakresie 1-5 (integer)
- **Wpływ na UI**: Tylko przyciski 1-5 są clickable, keyboard accepts tylko 1-5

### Walidacja sesji
- **Komponent**: StudySessionView
- **Warunek**: Musi być przynajmniej jedna fiszka do powtórki
- **Wpływ na UI**: Jeśli brak fiszek → EmptyState zamiast StudyCard

## 10. Obsługa błędów

### Błędy inicjalizacji
- **401 Unauthorized**: Redirect do strony logowania
- **500 Server Error**: Wyświetlenie komunikatu błędu z opcją retry
- **Network Error**: Wyświetlenie komunikatu o problemach z połączeniem

### Błędy wysyłania oceny
- **404 Not Found**: Przejście do następnej fiszki z komunikatem warning
- **422 Validation Error**: Wyświetlenie komunikatu o nieprawidłowej ocenie
- **500 Server Error**: Retry mechanism z exponential backoff
- **Network Error**: Offline mode z queue mechanism

### Fallback states
- **Brak fiszek**: EmptyState z pozytywnym komunikatem
- **Błąd ładowania**: Error state z przyciskiem retry
- **Błąd oceny**: Możliwość ponownego wysłania oceny

## 11. Kroki implementacji

### Krok 1: Przygotowanie typów i interfejsów
- Zdefiniowanie wszystkich TypeScript interfaces
- Utworzenie enum dla CardSide
- Przygotowanie API types zgodnych z backend DTOs

### Krok 2: Implementacja useStudySession hook
- Logika pobierania fiszek z API
- Stan management dla sesji
- Error handling i loading states
- Navigation logic między fiszkami

### Krok 3: Utworzenie podstawowych komponentów
- LoadingSpinner (reusable)
- EmptyState z komunikatem i CTA
- ProgressIndicator z progress calculation

### Krok 4: Implementacja StudyCard
- Layout 400x300px z responsive content
- Flip animation między front/back
- ShowAnswerButton integration
- Keyboard navigation support

### Krok 5: Implementacja RatingScale
- 5 przycisków z clear visual hierarchy
- Keyboard navigation (1-5 keys)
- Loading state podczas submission
- Accessibility (ARIA labels, focus management)

### Krok 6: Integracja StudySessionView
- Layout z wszystkimi komponentami
- State management przez useStudySession
- Conditional rendering na podstawie stanu
- Error boundaries dla crash protection

### Krok 7: Stylowanie z Tailwind CSS
- Consistent design zgodny z design system
- Focus states dla accessibility
- Smooth animations i transitions
- Responsive text sizing dla różnych treści

### Krok 8: Keyboard accessibility
- Tab navigation przez wszystkie interaktywne elementy
- Keyboard shortcuts (Space, Enter, 1-5)
- Focus trapping w aktywnym komponencie
- ARIA labels i roles

### Krok 9: Testing i optimization
- Unit tests dla useStudySession hook
- Integration tests dla API calls
- E2E tests dla complete user flow
- Performance optimization dla smooth animations

### Krok 10: Error handling i edge cases
- Network connectivity issues
- API timeout handling
- Invalid data scenarios
- Browser compatibility testing 