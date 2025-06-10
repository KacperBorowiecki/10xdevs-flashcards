from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional # Dodane na wszelki wypadek, gdybyś chciał dodać opcjonalne ustawienia

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # OpenRouter.ai LLM Configuration
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "google/gemma-3-27b-it"
    LLM_TIMEOUT: int = 30
    LLM_MAX_TOKENS: int = 2000
    
    # Możesz tutaj dodać inne globalne ustawienia aplikacji w przyszłości
    # np. DATABASE_URL: str, SECRET_KEY: str, etc.

    # Konfiguracja Pydantic do wczytywania zmiennych z pliku .env
    # oraz ignorowania dodatkowych zmiennych, jeśli istnieją w systemie
    model_config = SettingsConfigDict(env_file=".env", extra='ignore', env_file_encoding='utf-8')

# Tworzymy instancję ustawień, która będzie importowana w innych częściach aplikacji
# settings = Settings()  # Moved to individual modules to avoid circular imports

# Aby upewnić się, że wszystko działa, możesz tymczasowo dodać:
# if __name__ == "__main__":
#     print("Ładowanie ustawień:")
#     print(f"Supabase URL: {settings.SUPABASE_URL}")
#     print(f"Supabase Key: {settings.SUPABASE_KEY}")
#     # Pamiętaj, aby to usunąć lub zakomentować w kodzie produkcyjnym 