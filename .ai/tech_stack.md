Frontend - FastAPI z Jinja2 i Tailwind CSS:
- FastAPI będzie serwować dynamiczne strony HTML przy użyciu szablonów Jinja2.
- Tailwind CSS zapewni narzędzia do szybkiego stylowania interfejsu.
- Takie podejście minimalizuje złożoność frontendu, idealne dla prototypu.

Backend - FastAPI i Supabase (self-hosted):
- FastAPI (Python) jako główny framework backendowy do logiki aplikacji i API.
- Supabase (self-hosted) dostarczy bazę danych PostgreSQL oraz system uwierzytelniania.
- Skupiamy się na self-hosting obu komponentów.

AI - Komunikacja z modelami przez usługę Openrouter.ai:
- Dostęp do szerokiej gamy modeli (OpenAI, Anthropic, Google i wiele innych), które pozwolą nam znaleźć rozwiązanie zapewniające wysoką efektywność i niskie koszta
- Pozwala na ustawianie limitów finansowych na klucze API

CI/CD i Hosting:
- Github Actions do tworzenia pipeline'ów CI/CD.
- DigitalOcean do hostowania aplikacji za pośrednictwem obrazu docker (FastAPI + self-hosted Supabase).