# Architektura UI dla 10x-cards

## 1. Przegląd struktury UI

Aplikacja 10x-cards to desktop-first aplikacja webowa wykorzystująca FastAPI z Jinja2 i Tailwind CSS. Architektura UI koncentruje się na prostocie i efektywności, umożliwiając użytkownikom szybkie tworzenie i zarządzanie fiszkami edukacyjnymi z wykorzystaniem AI oraz efektywną naukę poprzez algorytm spaced repetition.

### Kluczowe założenia architektoniczne:
- **Desktop-only**: Brak responsywności mobilnej, skupienie na wersji desktop
- **Fixed layout**: Maksymalna szerokość 1200px, wyśrodkowany na ekranie
- **Sidebar navigation**: Stały sidebar 230px z główną nawigacją
- **Minimalistyczny design**: Skupienie na funkcjonalności, nowoczesna paleta kolorów
- **Card-based layout**: Wykorzystanie kart dla lepszej separacji wizualnej
- **State management**: Lokalny stan dla każdego widoku, optimistic updates

## 2. Lista widoków

### 2.1. Strona logowania/rejestracji
- **Ścieżka widoku**: `/login`, `/register`
- **Główny cel**: Uwierzytelnienie użytkownika w systemie
- **Kluczowe informacje**: Formularz logowania z polami email/hasło, opcja rejestracji
- **Kluczowe komponenty**:
  - Formularz logowania z walidacją
  - Przycisk przełączania między logowaniem a rejestracją
  - Komunikaty błędów uwierzytelniania
  - Loading state podczas autoryzacji
- **UX/Dostępność/Bezpieczeństwo**:
  - Minimalistyczny design zgodny z notatkami sesji
  - Semantic HTML z odpowiednimi labels
  - Walidacja po stronie klienta z immediate feedback
  - Bezpieczne przesyłanie danych z integracją Supabase JWT

### 2.2. Dashboard (widok główny)
- **Ścieżka widoku**: `/dashboard`
- **Główny cel**: Centralny punkt kontrolny z podsumowaniem aktywności użytkownika
- **Kluczowe informacje**: Statystyki użytkownika, szybki dostęp do głównych funkcji
- **Kluczowe komponenty**:
  - Karty statystyk (łączna liczba fiszek, fiszki do powtórki dziś, statystyki AI w formacie x/y)
  - Przyciski CTA do głównych funkcji (Generuj fiszki, Moje fiszki, Sesja nauki)
  - Komunikat powitalny i orientacja użytkownika
- **UX/Dostępność/Bezpieczeństwo**:
  - Clear visual hierarchy z podstawowymi liczbami
  - Keyboard navigation dla głównych akcji
  - Auto-refresh statystyk przy powrocie do widoku
  - Tylko dane użytkownika dzięki RLS

### 2.3. Generowanie fiszek AI
- **Ścieżka widoku**: `/generate`
- **Główny cel**: Główna funkcja aplikacji - automatyczne generowanie fiszek z tekstu
- **Kluczowe informacje**: Formularz wprowadzania tekstu, wygenerowane propozycje, opcje zarządzania
- **Kluczowe komponenty**:
  - Textarea z licznikiem znaków (x/10000) i live validation
  - Przycisk generowania z loading state ("Generuję fiszki...")
  - Prezentacja propozycji pojedynczo z opcjami: Akceptuj, Edytuj, Odrzuć
  - Modal edycji fiszki przed akceptacją
  - Toast notifications dla feedback operacji
- **UX/Dostępność/Bezpieczeństwo**:
  - Real-time walidacja długości tekstu (1000-10000 znaków)
  - Loading spinner podczas komunikacji z LLM API
  - Error handling dla błędów 503/timeout z user-friendly komunikatami
  - Optimistic updates dla szybkich operacji akceptacji/odrzucenia

### 2.4. Moje fiszki
- **Ścieżka widoku**: `/my-flashcards`
- **Główny cel**: Zarządzanie wszystkimi fiszkami użytkownika (ręczne i z AI)
- **Kluczowe informacje**: Lista wszystkich fiszek z opcjami zarządzania
- **Kluczowe komponenty**:
  - Card layout pokazujący front content fiszki
  - Znaczek robota dla fiszek pochodzących z AI (subtle badge w prawym górnym rogu)
  - Akcje dla każdej fiszki: podgląd, edycja, usuwanie
  - Przycisk "Dodaj nową fiszkę" dla ręcznego tworzenia
  - Modal edycji fiszki
  - Opcjonalne lokalne filtrowanie (manual/AI)
  - Stan pusty z przyciskiem "Wygeneruj fiszki z AI"
- **UX/Dostępność/Bezpieczeństwo**:
  - Pagination dla dużych zbiorów fiszek
  - Confirmation dialog przed usunięciem
  - Keyboard shortcuts dla częstych akcji
  - Lazy loading z debouncing dla filtrowania

### 2.5. Sesja nauki
- **Ścieżka widoku**: `/study-session`
- **Główny cel**: Nauka z wykorzystaniem algorytmu spaced repetition
- **Kluczowe informacje**: Aktualna fiszka do powtórki, progress sesji, opcje oceny
- **Kluczowe komponenty**:
  - Fiszka wyśrodkowana o wymiarach 400x300px
  - Progress indicator (format "5/20 fiszek")
  - Przycisk "Pokaż odpowiedź"
  - Skala oceny 1-5 po obejrzeniu odpowiedzi
  - Komunikat "Dobra robota, wróć jutro!" gdy brak fiszek do powtórki
- **UX/Dostępność/Bezpieczeństwo**:
  - Stałe wymiary fiszek dla konsistentnego doświadczenia
  - Brak opcji wcześniejszego zakończenia sesji
  - Clear focus states dla keyboard navigation
  - Automatyczne przejście do następnej fiszki po ocenie

## 3. Mapa podróży użytkownika

### 3.1. Onboarding nowego użytkownika
1. **Logowanie/Rejestracja** → **Dashboard**
2. **Dashboard** → **Generowanie AI** (zgodnie z decyzją: onboarding zaczyna od AI)
3. **Generowanie AI**: Wprowadzenie tekstu → Loading → Przegląd propozycji → Akceptacja/Edycja/Odrzucenie
4. **Po zapisaniu fiszek** → **Moje fiszki** (potwierdzenie zapisanych fiszek)
5. **Moje fiszki** → **Sesja nauki** (pierwszy raz, gdy ma fiszki do nauki)

### 3.2. Typowa sesja użytkownika powracającego
1. **Logowanie** → **Dashboard** (przegląd statystyk)
2. **Dashboard** → **Sesja nauki** (jeśli ma fiszki do powtórki)
3. **Sesja nauki** → **Dashboard** (po zakończeniu sesji)
4. **Dashboard** → **Generowanie AI** lub **Moje fiszki** (zarządzanie treścią)

### 3.3. Ścieżki alternatywne
- **Zarządzanie fiszkami**: Dashboard → Moje fiszki → Edycja/Usuwanie (modal)
- **Ręczne tworzenie**: Moje fiszki → "Dodaj nową fiszkę" → Modal tworzenia
- **Generowanie z listy**: Moje fiszki → "Wygeneruj fiszki z AI" → Generowanie AI

## 4. Układ i struktura nawigacji

### 4.1. Layout główny
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Logo | Nazwa użytkownika | Logout                   │
├──────────────┬──────────────────────────────────────────────┤
│   Sidebar    │                                              │
│   (230px)    │            Content Area                      │
│              │                                              │
│  • Dashboard │                                              │
│  • Generuj   │                                              │
│  • Moje      │                                              │
│  • Sesja     │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### 4.2. Sidebar nawigacji (fixed, 230px)
- **Dashboard** (ikona home) - widok główny z statystykami
- **Generuj fiszki** (ikona magic-wand) - AI generation
- **Moje fiszki** (ikona cards) - zarządzanie fiszkami
- **Sesja nauki** (ikona brain) - spaced repetition

### 4.3. Header
- Logo/nazwa aplikacji (po lewej)
- Nazwa użytkownika (po prawej)
- Przycisk logout (po prawej)

### 4.4. Zasady nawigacji
- Sidebar zawsze widoczny (nie zwijany na desktop)
- Active state dla aktualnej sekcji
- Smooth transitions między widokami
- Breadcrumbs nie są implementowane (zgodnie z decyzją)

## 5. Kluczowe komponenty

### 5.1. FlashcardComponent
- **Zastosowanie**: Wyświetlanie fiszek w różnych kontekstach
- **Warianty**: Card view (lista), Study view (sesja nauki), Preview (modal)
- **Funkcjonalność**: Flip animation, różne rozmiary, akcje kontekstowe

### 5.2. Modal dialogs
- **EditFlashcardModal**: Edycja treści fiszki (przód/tył)
- **CreateFlashcardModal**: Ręczne tworzenie nowej fiszki
- **ConfirmDeleteModal**: Potwierdzenie usunięcia fiszki
- **Charakterystyka**: Overlay design, focus trap, ESC to close

### 5.3. Form components
- **TextareaWithCounter**: Pole tekstowe z licznikiem znaków i validacją
- **FormField**: Standardowe pole formularza z labelem i błędami
- **SubmitButton**: Przycisk z loading state i walidacją

### 5.4. Feedback components
- **ToastNotification**: Komunikaty o statusie operacji
- **LoadingSpinner**: Indykator ładowania z tekstem
- **EmptyState**: Komponenty dla pustych stanów z CTA
- **ProgressIndicator**: Wskaźnik postępu w sesji nauki

### 5.5. Navigation components
- **Sidebar**: Główna nawigacja z ikonkami i active states
- **Header**: Nagłówek z branding i user controls
- **AIBadge**: Znaczek robota dla fiszek z AI

### 5.6. Layout components
- **PageContainer**: Wrapper dla content area z consistent spacing
- **CardGrid**: Layout dla list fiszek
- **StatCard**: Karty statystyk na dashboardzie
- **StudyCard**: Specjalizowany komponent dla sesji nauki (400x300px)

### 5.7. Specialized components
- **AIGenerationInterface**: Kompleksowy komponent do generowania AI
- **SpacedRepetitionEngine**: UI dla algorytmu spaced repetition
- **FlashcardActions**: Grouped actions (podgląd, edycja, usuwanie)
- **RatingScale**: Skala 1-5 dla oceny w sesji nauki 