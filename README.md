# 10x-cards

## Table of Contents
1.  [Project Description](#project-description)
2.  [Tech Stack](#tech-stack)
3.  [Getting Started Locally](#getting-started-locally)
4.  [Available Scripts](#available-scripts)
5.  [Project Scope](#project-scope)
6.  [Project Status](#project-status)
7.  [License](#license)

## Project Description
**10x-cards** is a web application designed to help users efficiently create, manage, and study educational flashcards. It leverages Large Language Models (LLMs) via an API to automatically generate flashcard suggestions from user-provided text, significantly reducing the time and effort associated with manual flashcard creation. The core goal is to provide a streamlined tool for an effective learning method: spaced repetition.

## Tech Stack

The project utilizes the following technologies:

*   **Backend:**
    *   **Framework:** FastAPI (Python) - For building the main application logic and API.
    *   **Database & Auth:** Supabase (Self-Hosted) - Provides a PostgreSQL database and user authentication capabilities.
*   **Frontend:**
    *   **Templating:** Jinja2 (served by FastAPI) - For rendering dynamic HTML pages.
    *   **Styling:** Tailwind CSS - For utility-first CSS styling.
*   **AI Integration:**
    *   **Service:** Openrouter.ai - To access a variety of Large Language Models (LLMs) for flashcard generation.
*   **CI/CD & Hosting:**
    *   **CI/CD:** GitHub Actions - For automating build, test, and deployment pipelines.
    *   **Hosting:** DigitalOcean - Application deployed via a Docker image, encompassing both the FastAPI application and the self-hosted Supabase instance.

## Getting Started Locally

To set up and run the project locally, follow these steps:

**Prerequisites:**
*   Python (version 3.8+ recommended)
*   Pip (Python package installer)
*   Docker and Docker Compose (for self-hosting Supabase and potentially running the application)
*   Access to an Openrouter.ai API key

**Setup:**

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd 10x-cards
    ```

2.  **Set up Python Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure you have a `requirements.txt` file in your project root.)*

4.  **Configure Environment Variables:**
    Create a `.env` file in the project root. You can copy `.env.example` if provided.
    This file should contain necessary configurations, such as:
    ```ini
    # Supabase (Self-Hosted) - Adjust based on your self-hosting setup
    SUPABASE_URL=your_self_hosted_supabase_url
    SUPABASE_KEY=your_self_hosted_supabase_anon_key
    DATABASE_URL=postgresql://user:password@host:port/database

    # Openrouter.ai
    OPENROUTER_API_KEY=your_openrouter_api_key

    # FastAPI settings
    SECRET_KEY=your_fastapi_secret_key
    # ... other necessary variables
    ```

5.  **Set up and Run Self-Hosted Supabase:**
    Follow the official Supabase documentation for self-hosting using Docker:
    [Supabase Self-Hosting Guide](https://supabase.com/docs/guides/hosting/overview)
    Ensure your Supabase instance is running and accessible before starting the FastAPI application.

6.  **Database Migrations (if applicable):**
    If the project uses database migrations (e.g., with Alembic for SQLAlchemy, or Supabase's built-in migrations), run them:
    ```bash
    # Example: alembic upgrade head (if using Alembic)
    # Or follow Supabase CLI instructions for migrations
    ```

7.  **Run the FastAPI Application:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    *(Adjust `main:app` if your FastAPI application instance is defined elsewhere, e.g., `app.main:app`)*

The application should now be accessible at `http://localhost:8000`.

## Available Scripts

*   **Run development server:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
*   **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
*   **(Potentially) Database migration scripts:**
    *(Add commands here if you use a migration tool like Alembic or Supabase CLI for migrations)*

## Project Scope

**Key Features (MVP):**
*   **AI-Powered Flashcard Generation:** Users can paste text, and the application will use an LLM (via Openrouter.ai) to suggest flashcards (question/answer pairs). Users can accept, edit, or reject these suggestions.
*   **Manual Flashcard Management:**
    *   Create new flashcards manually (front and back).
    *   Edit existing flashcards.
    *   Delete flashcards.
*   **User Authentication:**
    *   User registration and login.
    *   Ability for users to request deletion of their account and associated data (GDPR compliance).
*   **Spaced Repetition Integration:** Integration with a ready-made (third-party) spaced repetition algorithm to schedule flashcard reviews.
*   **Data Storage:** Securely store user accounts and flashcard data using the self-hosted Supabase (PostgreSQL) instance.
*   **Basic Statistics:** Collect data on the number of AI-generated flashcards and the acceptance rate by users.

**Out of Scope (for the current MVP):**
*   Developing an advanced, custom spaced repetition algorithm (e.g., SuperMemo, Anki-style).
*   Mobile applications (the current focus is web-only).
*   Gamification features.
*   Importing flashcards from various document formats (e.g., PDF, DOCX).
*   A publicly accessible API for third-party integrations.
*   Features for sharing flashcards or flashcard sets between users.
*   Advanced notification systems.
*   Complex keyword-based search functionality for flashcards.

## Project Status
The project is currently in the **prototyping/development phase** for an MVP (Minimum Viable Product).

**Primary Goals for MVP Success:**
*   Achieve a user acceptance rate of at least 75% for AI-generated flashcards.
*   Have users create at least 75% of their new flashcards utilizing the AI generation feature.

## License
This project is licensed under the **MIT License**.
*(You can replace this with your chosen license. If you haven't chosen one, MIT is a common and permissive open-source license. Consider adding a `LICENSE` file to your repository with the full license text.)* 