from supabase import create_client, Client
from src.core.config import settings  # Importujemy nasze skonfigurowane ustawienia

# Przechowujemy URL i klucz w zmiennych dla czytelności
supabase_url: str = settings.SUPABASE_URL
supabase_key: str = settings.SUPABASE_KEY

# Możemy zdefiniować globalną instancję klienta lub funkcję, która ją tworzy.
# Dla supabase-py, create_client() jest operacją lekką i bezpieczną do wywoływania.
# Jednakże, aby uniknąć wielokrotnego tworzenia obiektu bez potrzeby,
# możemy zastosować prosty wzorzec "singleton-like" dla tej funkcji zależności.
# Alternatywnie, dla bardzo prostych przypadków, można by tworzyć klienta za każdym razem.

_supabase_client_instance: Client | None = None

def get_supabase_client() -> Client:
    """
    Zwraca instancję klienta Supabase.
    Jeśli instancja nie istnieje, tworzy ją.
    Ta funkcja jest przeznaczona do użycia jako zależność FastAPI.
    """
    global _supabase_client_instance
    if _supabase_client_instance is None:
        # Logika inicjalizacji klienta powinna być tutaj.
        # Upewnij się, że biblioteka supabase-py jest poprawnie skonfigurowana
        # do pracy asynchronicznej, jeśli Twoje endpointy FastAPI są asynchroniczne.
        # Supabase-py v2.x.x zwraca klienta, którego metody (np. .table(...).select(...).execute())
        # są asynchroniczne i powinny być `await`owane.
        try:
            _supabase_client_instance = create_client(supabase_url, supabase_key)
        except Exception as e:
            # Możesz dodać tutaj logowanie błędu inicjalizacji, jeśli jest potrzebne
            # np. logger.error(f"Nie udało się zainicjalizować klienta Supabase: {e}")
            raise RuntimeError(f"Nie udało się zainicjalizować klienta Supabase: {e}") from e
            
    return _supabase_client_instance

# Możesz również rozważyć bardziej zaawansowane zarządzanie cyklem życia klienta,
# np. zamykanie połączeń, jeśli biblioteka supabase-py tego wymaga
# i jeśli używasz go w sposób, który tworzy trwałe połączenia.
# Jednak dla wielu przypadków użycia z supabase-py, powyższe podejście jest wystarczające.

# Przykład użycia (do testowania, usuń lub zakomentuj w kodzie produkcyjnym):
# async def main_test():
#     try:
#         client = get_supabase_client()
#         print("Pomyślnie uzyskano klienta Supabase.")
#         # Przykładowe zapytanie (dostosuj 'your_table_name' do istniejącej tabeli)
#         # response = await client.table('source_texts').select("id, text_content", count="exact").limit(1).execute()
#         # print("Odpowiedź z Supabase:", response)
#     except Exception as e:
#         print(f"Błąd podczas testowania klienta Supabase: {e}")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main_test()) 