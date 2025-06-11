# Plan implementacji widoku Dashboard

## 1. Przegląd

Dashboard to centralny punkt kontrolny aplikacji 10x-cards, który prezentuje użytkownikowi podsumowanie jego aktywności edukacyjnej oraz zapewnia szybki dostęp do głównych funkcji aplikacji. Widok wyświetla kluczowe statystyki (łączna liczba fiszek, fiszki do powtórki dziś, statystyki AI w formacie x/y) oraz oferuje przyciski CTA do generowania fiszek, zarządzania fiszkami i sesji nauki. Dashboard wykorzystuje server-side rendering z Jinja2 templates, Tailwind CSS do stylowania oraz JavaScript dla funkcji auto-refresh.

## 2. Routing widoku

**Ścieżka widoku**: `/dashboard`

Dashboard jest domyślnym widokiem docelowym po pomyślnym zalogowaniu użytkownika (zgodnie z US-002). Route handler będzie zaimplementowany w FastAPI jako endpoint GET zwracający wyrenderowany template HTML.

## 3. Struktura komponentów

```
DashboardView (main Jinja2 template)
├── BaseLayout (extends)
├── DashboardHeader (include macro)
├── StatsSection (include macro)
│   ├── FlashcardStatsCard (macro)
│   ├── DueCardsStatsCard (macro) 
│   └── AIStatsCard (macro)
└── ActionButtonsSection (include macro)
    ├── GenerateFlashcardsButton (macro)
    ├── MyFlashcardsButton (macro)
    └── StudySessionButton (macro)
```

## 4. Szczegóły komponentów

### DashboardView (główny template)
- **Opis komponentu**: Główny kontener widoku Dashboard, rozszerzający base layout aplikacji z sidebar nawigacją
- **Główne elementy**: `<main>` element z klasami Tailwind CSS, sekcje dla header, stats i action buttons
- **Obsługiwane interakcje**: 
  - Auto-refresh statystyk co 5 minut via JavaScript
  - Keyboard navigation (Tab, Enter) dla przycisków CTA
  - Responsive behavior na różnych rozmiarach ekranu
- **Obsługiwana walidacja**: 
  - Walidacja obecności danych statystyk przed renderowaniem
  - Fallback values dla brakujących danych (0 dla liczników)
  - Error state display przy błędach ładowania danych
- **Typy**: `DashboardContext`, `DashboardStats`
- **Propsy**: Dane przekazywane z FastAPI route handler jako template context

### DashboardHeader (macro)
- **Opis komponentu**: Sekcja powitalna z komunikatem orientacyjnym dla użytkownika
- **Główne elementy**: `<header>` z tytułem "Dashboard", komunikatem powitalnym z nazwą użytkownika
- **Obsługiwane interakcje**: Brak (statyczny komponent)
- **Obsługiwana walidacja**: Walidacja obecności user_email w kontekście
- **Typy**: `str` dla user_email
- **Propsy**: `user_email` - email zalogowanego użytkownika

### StatsSection (sekcja kart statystyk)
- **Opis komponentu**: Kontener dla trzech kart statystyk wyświetlanych w układzie grid
- **Główne elementy**: `<section>` z grid layout (3 kolumny na desktop), każda karta w `<div>` z tłem i shadowem
- **Obsługiwane interakcje**: Hover effects na kartach, loading states podczas odświeżania
- **Obsługiwana walidacja**: 
  - Sprawdzenie kompletności danych statystyk
  - Wyświetlanie loading spinnerów podczas fetch
  - Error states dla każdej karty osobno
- **Typy**: `DashboardStats`
- **Propsy**: `stats` - obiekt z wszystkimi statystykami

### FlashcardStatsCard (karta statystyk fiszek)
- **Opis komponentu**: Karta wyświetlająca łączną liczbę aktywnych fiszek użytkownika
- **Główne elementy**: Ikona fiszki, liczba (duża czcionka), label "Wszystkie fiszki"
- **Obsługiwane interakcje**: Hover effect, kliknięcie prowadzi do `/flashcards`
- **Obsługiwana walidacja**: Walidacja czy `total_flashcards` jest liczbą >= 0
- **Typy**: `int` dla total_flashcards
- **Propsy**: `total_flashcards` - liczba aktywnych fiszek

### DueCardsStatsCard (karta fiszek do powtórki)
- **Opis komponentu**: Karta pokazująca liczbę fiszek gotowych do powtórki dziś
- **Główne elementy**: Ikona zegara, liczba (duża czcionka), label "Do powtórki dziś"
- **Obsługiwane interakcje**: Hover effect, kliknięcie prowadzi do `/study-session`
- **Obsługiwana walidacja**: Walidacja czy `due_cards_today` jest liczbą >= 0
- **Typy**: `int` dla due_cards_today
- **Propsy**: `due_cards_today` - liczba fiszek do powtórki

### AIStatsCard (karta statystyk AI)
- **Opis komponentu**: Karta wyświetlająca statystyki AI w formacie "x/y" (zaakceptowane/wygenerowane)
- **Główne elementy**: Ikona AI, ratio "x/y" (duża czcionka), label "Statystyki AI"
- **Obsługiwane interakcje**: Hover effect, kliknięcie prowadzi do `/ai/generation-stats`
- **Obsługiwana walidacja**: 
  - Walidacja czy `total_generated` i `total_accepted` są liczbami >= 0
  - Obsługa przypadku gdy `total_generated` = 0 (wyświetl "0/0")
- **Typy**: `AIGenerationSummary` zawierający `total_generated` i `total_accepted`
- **Propsy**: `ai_stats` - obiekt z statystykami AI

### ActionButtonsSection (sekcja przycisków CTA)
- **Opis komponentu**: Sekcja z trzema głównymi przyciskami działania (CTA)
- **Główne elementy**: `<section>` z flexbox layout, trzy przyciski z ikonami i opisami
- **Obsługiwane interakcje**: 
  - Hover/focus states
  - Keyboard navigation (Tab/Enter)
  - Click handling prowadzący do odpowiednich routes
- **Obsługiwana walidacja**: Sprawdzenie czy wszystkie routes są dostępne
- **Typy**: Brak (statyczne przyciski)
- **Propsy**: Brak

### GenerateFlashcardsButton (przycisk generowania AI)
- **Opis komponentu**: Główny przycisk CTA do generowania fiszek z wykorzystaniem AI
- **Główne elementy**: `<a>` lub `<button>` z ikoną "magic-wand", tekst "Generuj fiszki"
- **Obsługiwane interakcje**: Click → navigate to `/ai/generate-flashcards`
- **Obsługiwana walidacja**: Brak (nawigacja)
- **Typy**: Brak
- **Propsy**: Brak

### MyFlashcardsButton (przycisk moich fiszek)
- **Opis komponentu**: Przycisk CTA do zarządzania istniejącymi fiszkami
- **Główne elementy**: `<a>` z ikoną "cards", tekst "Moje fiszki"
- **Obsługiwane interakcje**: Click → navigate to `/flashcards`
- **Obsługiwana walidacja**: Brak (nawigacja)
- **Typy**: Brak
- **Propsy**: Brak

### StudySessionButton (przycisk sesji nauki)
- **Opis komponentu**: Przycisk CTA do rozpoczęcia sesji nauki z spaced repetition
- **Główne elementy**: `<a>` z ikoną "brain", tekst "Sesja nauki"
- **Obsługiwane interakcje**: Click → navigate to `/study-session`
- **Obsługiwana walidacja**: Opcjonalne sprawdzenie czy użytkownik ma fiszki do nauki
- **Typy**: Brak
- **Propsy**: Brak

## 5. Typy

### DashboardContext
```python
class DashboardContext(BaseModel):
    """Główny kontekst przekazywany do template Dashboard."""
    user_email: str = Field(..., description="Email zalogowanego użytkownika")
    stats: DashboardStats = Field(..., description="Statystyki użytkownika")
    error_message: Optional[str] = Field(None, description="Komunikat błędu jeśli wystąpił")
```

### DashboardStats
```python
class DashboardStats(BaseModel):
    """Zagregowane statystyki dla Dashboard."""
    total_flashcards: int = Field(..., ge=0, description="Łączna liczba aktywnych fiszek")
    due_cards_today: int = Field(..., ge=0, description="Liczba fiszek do powtórki dziś")
    ai_stats: AIGenerationSummary = Field(..., description="Podsumowanie statystyk AI")
```

### AIGenerationSummary
```python
class AIGenerationSummary(BaseModel):
    """Podsumowanie statystyk generowania AI."""
    total_generated: int = Field(..., ge=0, description="Łączna liczba wygenerowanych fiszek")
    total_accepted: int = Field(..., ge=0, description="Łączna liczba zaakceptowanych fiszek")
    
    @property
    def acceptance_ratio(self) -> str:
        """Zwraca ratio w formacie 'x/y' dla wyświetlenia."""
        return f"{self.total_accepted}/{self.total_generated}"
```

## 6. Zarządzanie stanem

Dashboard wykorzystuje **server-side state management** z auto-refresh funkcjonalnością:

### Stan serwera
- Dane są pobierane i agregowane w FastAPI route handler
- `DashboardService` odpowiada za agregację danych z różnych endpointów
- Context z danymi przekazywany do Jinja2 template przy każdym request

### Stan klienta (JavaScript)
- **Auto-refresh timer**: `setInterval()` co 5 minut wywołuje refresh statystyk
- **Loading states**: Lokalne flagi dla każdej karty statystyk podczas odświeżania
- **Error handling**: Lokalne error states dla failed requests

### Custom hook (DashboardService)
```python
class DashboardService:
    async def get_dashboard_stats(self, user_id: UUID) -> DashboardStats:
        """Agreguje dane z różnych endpointów dla Dashboard."""
        # Równoległe calls do różnych endpoints
        # Agregacja wyników
        # Zwraca DashboardStats
```

## 7. Integracja API

Dashboard integruje się z trzema endpointami API:

### Request/Response typy:

**1. GET /api/v1/flashcards?status=active&page=1&size=1**
- **Request**: Query params dla filtrowania aktywnych fiszek
- **Response**: `PaginatedFlashcardsResponse` - potrzebujemy tylko `total` field
- **Cel**: Pobranie łącznej liczby aktywnych fiszek użytkownika

**2. GET /api/v1/spaced-repetition/due-cards?limit=1**
- **Request**: Query param `limit=1` (potrzebujemy tylko count)
- **Response**: `List[FlashcardWithRepetition]` - potrzebujemy `len()` wyniku
- **Cel**: Liczba fiszek gotowych do powtórki dziś

**3. GET /api/v1/ai/generation-stats?page=1&size=100**
- **Request**: Query params dla paginacji (większy size dla agregacji)
- **Response**: `PaginatedAiGenerationStatsResponse` - agregujemy `generated_cards_count` i `accepted_cards_count`
- **Cel**: Statystyki AI (suma wszystkich generated i accepted)

### Agregacja w DashboardService:
- Równoległe wywołania wszystkich trzech endpointów
- Error handling dla każdego endpoint osobno
- Fallback values przy błędach (0 dla statystyk)

## 8. Interakcje użytkownika

### Nawigacja CTA
- **Generuj fiszki**: `onclick` → `window.location.href = '/ai/generate-flashcards'`
- **Moje fiszki**: `onclick` → `window.location.href = '/flashcards'`
- **Sesja nauki**: `onclick` → `window.location.href = '/study-session'`

### Auto-refresh
- JavaScript timer (`setInterval`) odświeża statystyki co 5 minut
- Fetch do `/api/dashboard/refresh-stats` endpoint
- Update tylko liczb w kartach (partial update)

### Accessibility
- **Keyboard navigation**: Tab przez wszystkie przyciski CTA
- **Screen readers**: Proper ARIA labels na kartach statystyk
- **Focus management**: Visible focus indicators

### Responsive interactions
- **Hover states**: Karty statystyk i przyciski CTA mają hover effects
- **Touch support**: Properly sized touch targets (44px minimum)

## 9. Warunki i walidacja

### Walidacja danych wejściowych (Backend)
- **user_id z JWT**: Sprawdzenie czy token jest ważny i user istnieje
- **API responses**: Walidacja że wszystkie endpoint response są prawidłowe
- **Data consistency**: Sprawdzenie czy statystyki są logicznie spójne

### Walidacja stanu interfejsu (Frontend)
- **Loading states**: Każda karta ma osobny loading spinner podczas refresh
- **Empty states**: Gdy `total_flashcards = 0` → komunikat zachęcający do rozpoczęcia
- **Error states**: Przy błędach API → retry button i error message
- **Data validation**: Sprawdzenie czy wszystkie liczby są >= 0

### Warunki biznesowe
- **Due cards calculation**: Tylko fiszki z `due_date <= NOW()` są liczone
- **Active flashcards**: Tylko fiszki ze statusem `active` w statystykach
- **AI stats aggregation**: Suma z wszystkich `ai_generation_events` użytkownika

## 10. Obsługa błędów

### Scenariusze błędów
1. **401 Unauthorized**: JWT token wygasł lub nieprawidłowy
   - **Obsługa**: Automatyczne przekierowanie na `/login`
   - **User feedback**: Komunikat "Sesja wygasła, zaloguj się ponownie"

2. **500 Internal Server Error**: Błąd serwera podczas pobierania statystyk
   - **Obsługa**: Wyświetlenie error state z retry button
   - **User feedback**: "Wystąpił błąd podczas ładowania danych"

3. **Network Error**: Brak połączenia z internetem
   - **Obsługa**: Offline mode indicator, retry po odzyskaniu połączenia
   - **User feedback**: "Brak połączenia z internetem"

4. **Partial API failure**: Jeden z endpointów zwraca błąd
   - **Obsługa**: Wyświetlenie dostępnych statystyk, error indicator dla failed
   - **User feedback**: Placeholder "Niedostępne" dla missing data

### Error boundaries
- **Template level**: Jinja2 try-except blocks dla każdej sekcji
- **Service level**: Exception handling w DashboardService
- **Client level**: JavaScript error handling dla auto-refresh

### Monitoring i logging
- **Backend logs**: Wszystkie błędy API są logowane z user_id
- **Client logs**: JavaScript errors zapisywane do console (dev mode)
- **Performance monitoring**: Response times dla dashboard load

## 11. Kroki implementacji

1. **Utworzenie modeli typów**
   - Dodanie `DashboardContext`, `DashboardStats`, `AIGenerationSummary` do `src/dtos.py`
   - Walidacja typów i testowanie serializacji

2. **Implementacja DashboardService**
   - Utworzenie `src/services/dashboard_service.py`
   - Implementacja metody `get_dashboard_stats()` z równoległymi API calls
   - Dodanie error handling i fallback values

3. **Utworzenie FastAPI route**
   - Dodanie route `/dashboard` w nowym router `src/api/v1/routers/dashboard_router.py`
   - Integracja z DashboardService i template rendering
   - Authentication dependency z JWT validation

4. **Implementacja Jinja2 templates**
   - Utworzenie `templates/dashboard/` directory
   - Implementacja `dashboard.html` main template
   - Utworzenie macros dla komponenty w `templates/macros/dashboard/`

5. **Styling z Tailwind CSS**
   - Implementacja responsive grid layout dla stats cards
   - Styling przycisków CTA z hover states
   - Accessibility improvements (focus states, ARIA labels)

6. **JavaScript functionality**
   - Implementacja auto-refresh timer w `static/js/dashboard.js`
   - Dodanie loading states i error handling
   - Event listeners dla keyboard navigation

7. **Integration z routing**
   - Dodanie dashboard router do `main.py`
   - Konfiguracja redirect z `/` na `/dashboard` dla authenticated users
   - Update navigation w base template

8. **Testing**
   - Unit testy dla DashboardService
   - Integration testy dla dashboard endpoint
   - E2E testy dla user interactions i auto-refresh

9. **Error handling i monitoring**
   - Implementacja comprehensive error handling
   - Dodanie logging i monitoring
   - Performance optimization dla aggregated queries

10. **Documentation i deployment**
    - Aktualizacja API documentation
    - User documentation dla Dashboard features
    - Deployment verification i monitoring setup 