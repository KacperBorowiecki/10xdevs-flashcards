# Plan implementacji widoku Logowania/Rejestracji

## 1. Przegląd
Widok logowania/rejestracji stanowi punkt wejścia do aplikacji 10x-cards. Jego głównym celem jest uwierzytelnienie użytkownika poprzez integrację z Supabase Auth. Widok oferuje możliwość logowania dla istniejących użytkowników oraz rejestracji nowych kont. Design jest minimalistyczny i skupiony na funkcjonalności, z pełną obsługą walidacji i stanów błędów.

## 2. Routing widoku
- **Ścieżka logowania**: `/login`
- **Ścieżka rejestracji**: `/register`
- **Przekierowanie po uwierzytelnieniu**: `/dashboard`
- **Obsługa routingu**: FastAPI z szablonem Jinja2 na jednej stronie z przełączaniem między trybami

## 3. Struktura komponentów
```
AuthPage (główny szablon Jinja2)
├── PageHeader (logo i tytuł)
├── AuthToggle (przełączanie login/register)
├── AuthForm (dynamiczny formularz)
│   ├── EmailField (pole email z walidacją)
│   ├── PasswordField (pole hasło)
│   ├── ConfirmPasswordField (tylko dla rejestracji)
│   ├── SubmitButton (z loading state)
│   └── ErrorDisplay (komunikaty błędów)
└── LoadingOverlay (overlay podczas autoryzacji)
```

## 4. Szczegóły komponentów

### AuthPage (główny szablon)
- **Opis komponentu**: Główny kontener strony uwierzytelniania z logiką przełączania między trybami logowania i rejestracji
- **Główne elementy**: Wyśrodkowany kontener max-width 400px, tło z gradientem, card z shadow
- **Obsługiwane interakcje**: Przełączanie między trybami, obsługa formularzy
- **Obsługiwana walidacja**: Walidacja email (format), hasło (min 6 znaków), potwierdzenie hasła
- **Typy**: AuthPageState, AuthFormData
- **Propsy**: mode ('login' | 'register'), error_message (opcjonalny)

### AuthToggle
- **Opis komponentu**: Przełącznik między trybami logowania i rejestracji
- **Główne elementy**: Dwa przyciski z active state, smooth transition
- **Obsługiwane interakcje**: Kliknięcie zmieniające tryb
- **Obsługiwana walidacja**: Brak
- **Typy**: AuthMode
- **Propsy**: current_mode, on_mode_change callback

### AuthForm
- **Opis komponentu**: Dynamiczny formularz dostosowujący się do trybu (login/register)
- **Główne elementy**: Form element z polami input, submit button, error display
- **Obsługiwane interakcje**: Submit formularza, real-time walidacja
- **Obsługiwana walidacja**: 
  - Email: wymagane, format email, max 254 znaki
  - Hasło: wymagane, min 6 znaków, max 128 znaków
  - Potwierdzenie hasła: zgodność z hasłem (tylko register)
- **Typy**: LoginFormData, RegisterFormData, ValidationErrors
- **Propsy**: mode, is_loading, on_submit callback, validation_errors

### EmailField
- **Opis komponentu**: Pole input dla adresu email z walidacją
- **Główne elementy**: Label, input type="email", error message span
- **Obsługiwane interakcje**: Blur validation, real-time feedback
- **Obsługiwana walidacja**: Format email, wymagane pole
- **Typy**: string
- **Propsy**: value, error, on_change callback, disabled

### PasswordField
- **Opis komponentu**: Pole input dla hasła z opcją pokazywania/ukrywania
- **Główne elementy**: Label, input type="password", toggle visibility button, error span
- **Obsługiwane interakcje**: Show/hide password, blur validation
- **Obsługiwana walidacja**: Min 6 znaków, wymagane pole
- **Typy**: string
- **Propsy**: value, error, on_change callback, disabled, show_toggle

### SubmitButton
- **Opis komponentu**: Przycisk submit z loading state
- **Główne elementy**: Button element z spinnerem, tekst zmienny według trybu
- **Obsługiwane interakcje**: Click submit, loading state
- **Obsługiwana walidacja**: Disabled podczas loading lub gdy form invalid
- **Typy**: boolean (loading state)
- **Propsy**: is_loading, mode, disabled, text

### ErrorDisplay
- **Opis komponentu**: Komponent do wyświetlania błędów uwierzytelniania
- **Główne elementy**: Alert box z ikoną błędu, możliwość zamykania
- **Obsługiwane interakcje**: Zamykanie alertu
- **Obsługiwana walidacja**: Brak
- **Typy**: AuthError
- **Propsy**: error, on_dismiss callback

## 5. Typy

```typescript
// Główne typy stanu
interface AuthPageState {
  mode: 'login' | 'register';
  isLoading: boolean;
  error: AuthError | null;
}

// Typy formularzy
interface LoginFormData {
  email: string;
  password: string;
}

interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
}

// Typ błędu
interface AuthError {
  message: string;
  field?: 'email' | 'password' | 'confirmPassword' | 'general';
  code?: string;
}

// Typ błędów walidacji
interface ValidationErrors {
  email?: string;
  password?: string;
  confirmPassword?: string;
}

// Typ odpowiedzi Supabase
interface SupabaseAuthResponse {
  user: User | null;
  session: Session | null;
  error: AuthError | null;
}
```

## 6. Zarządzanie stanem
Zarządzanie stanem będzie oparte na vanilla JavaScript z wykorzystaniem wzorca Observer dla reaktywności:

- **Globalny stan**: `AuthState` przechowywany w obiekcie JavaScript
- **Lokalne stany**: Walidacja formularzy w real-time
- **Persistencja**: Session/localStorage dla zapamiętania trybu
- **Reaktywność**: Event listeners dla aktualizacji UI
- **Supabase Auth**: Integration z auth.onAuthStateChange() dla synchronizacji stanu

Hook pomocniczy `useAuthManager`:
- Zarządzanie stanem uwierzytelniania
- Integracja z Supabase Auth
- Obsługa przekierowań
- Centralizacja logiki błędów

## 7. Integracja API
Integracja oparta na Supabase JavaScript Client:

### Logowanie:
```javascript
// Request
const loginData = {
  email: string,
  password: string
}

// API Call
const { data, error } = await supabase.auth.signInWithPassword(loginData)

// Response
SupabaseAuthResponse {
  user: User | null,
  session: Session | null,
  error: AuthError | null
}
```

### Rejestracja:
```javascript
// Request
const registerData = {
  email: string,
  password: string
}

// API Call
const { data, error } = await supabase.auth.signUp(registerData)

// Response
SupabaseAuthResponse {
  user: User | null,
  session: Session | null,
  error: AuthError | null
}
```

### Obsługa sesji:
```javascript
// Sprawdzanie aktualnej sesji
const { data: { session } } = await supabase.auth.getSession()

// Nasłuchiwanie zmian
supabase.auth.onAuthStateChange((event, session) => {
  // Obsługa zmian stanu uwierzytelniania
})
```

## 8. Interakcje użytkownika

### Przełączanie trybu:
1. **Akcja**: Kliknięcie na przycisk "Zarejestruj się" / "Zaloguj się"
2. **Rezultat**: Zmiana trybu formularza, aktualizacja UI, reset błędów
3. **Implementacja**: Event listener z toggleMode() function

### Wysyłanie formularza logowania:
1. **Akcja**: Submit formularza logowania
2. **Walidacja**: Email format, hasło min 6 znaków
3. **API Call**: supabase.auth.signInWithPassword()
4. **Sukces**: Przekierowanie na /dashboard
5. **Błąd**: Wyświetlenie komunikatu błędu

### Wysyłanie formularza rejestracji:
1. **Akcja**: Submit formularza rejestracji
2. **Walidacja**: Email format, hasło min 6 znaków, potwierdzenie hasła
3. **API Call**: supabase.auth.signUp()
4. **Sukces**: Komunikat o wysłaniu emaila weryfikacyjnego
5. **Błąd**: Wyświetlenie komunikatu błędu

### Real-time walidacja:
1. **Akcja**: Blur na polach input
2. **Walidacja**: Sprawdzenie kryteriów pola
3. **Feedback**: Natychmiastowe wyświetlenie błędów

## 9. Warunki i walidacja

### Walidacja email:
- **Komponent**: EmailField
- **Warunki**: Format email (regex), wymagane pole, max 254 znaki
- **Wpływ na UI**: Czerwona ramka, komunikat błędu pod polem
- **Implementacja**: HTML5 validation + custom regex

### Walidacja hasła:
- **Komponent**: PasswordField  
- **Warunki**: Min 6 znaków, wymagane pole, max 128 znaków
- **Wpływ na UI**: Czerwona ramka, komunikat błędu, wskaźnik siły hasła
- **Implementacja**: JavaScript validation on blur/input

### Walidacja potwierdzenia hasła:
- **Komponent**: ConfirmPasswordField (tylko register)
- **Warunki**: Zgodność z hasłem, wymagane pole
- **Wpływ na UI**: Czerwona ramka, komunikat o niezgodności
- **Implementacja**: Porównanie wartości w real-time

### Walidacja formularza:
- **Komponent**: AuthForm
- **Warunki**: Wszystkie pola valid, brak błędów API
- **Wpływ na UI**: Disabled submit button, loading state
- **Implementacja**: Aggregate validation z wszystkich pól

## 10. Obsługa błędów

### Błędy walidacji po stronie klienta:
- **Typy**: Format email, długość hasła, niezgodność haseł
- **Wyświetlanie**: Pod odpowiednim polem, czerwony tekst
- **Zachowanie**: Real-time feedback, usuwanie po korekcie

### Błędy uwierzytelniania Supabase:
- **Typy**: 
  - "Invalid login credentials" (błędne dane)
  - "User already registered" (email już istnieje)
  - "Email not confirmed" (niezweryfikowany email)
- **Wyświetlanie**: Na górze formularza, alert box z możliwością zamknięcia
- **Zachowanie**: Automatyczne usuwanie po 5 sekundach lub przez użytkownika

### Błędy sieciowe:
- **Typy**: Timeout, brak połączenia, błędy serwera
- **Wyświetlanie**: Ogólny komunikat "Wystąpił błąd połączenia"
- **Zachowanie**: Możliwość ponowienia próby, button "Spróbuj ponownie"

### Błędy niespodziewane:
- **Typy**: JavaScript errors, nieobsłużone błędy API
- **Wyświetlanie**: Ogólny komunikat "Wystąpił nieoczekiwany błąd"
- **Zachowanie**: Logging do konsoli, graceful degradation

## 11. Kroki implementacji

1. **Przygotowanie struktury**
   - Utworzenie szablonu Jinja2 dla auth page
   - Dodanie routingu w FastAPI (/login, /register)
   - Konfiguracja Supabase client w JavaScripcie

2. **Implementacja podstawowego HTML**
   - Struktura strony z Tailwind CSS
   - Formularz z polami email/password
   - Przycisk przełączania trybu

3. **Dodanie walidacji po stronie klienta**
   - JavaScript validation functions
   - Real-time feedback dla pól
   - Warunki submit button

4. **Integracja z Supabase Auth**
   - Konfiguracja Supabase client
   - Implementacja logowania/rejestracji
   - Obsługa callback'ów auth state

5. **Implementacja obsługi błędów**
   - Error handling dla wszystkich scenariuszy
   - UI feedback dla błędów
   - Graceful error recovery

6. **Dodanie stanów loading**
   - Loading spinner podczas auth
   - Disabled states dla formularzy
   - Visual feedback dla użytkownika

7. **Implementacja przekierowań**
   - Przekierowanie po udanej autoryzacji
   - Ochrona przed dostępem dla zalogowanych
   - Handling auth state changes

8. **Stylowanie i UX**
   - Responsive design (desktop-first)
   - Smooth transitions i animations
   - Accessibility improvements

9. **Testowanie i debugowanie**
   - Testy wszystkich scenariuszy user flow
   - Obsługa edge cases
   - Cross-browser compatibility

10. **Optymalizacja i finalizacja**
    - Performance optimization
    - Code cleanup i refactoring
    - Dokumentacja implementacji 