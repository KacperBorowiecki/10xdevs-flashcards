# REST API Plan

This document outlines the REST API plan for the 10x-cards application, based on the provided database schema, Product Requirements Document (PRD), and technology stack.

## 1. Resources

*   **Flashcards**: Represents individual flashcards.
    *   Corresponds to `flashcards` table.
*   **AI**: Namespace for AI-related operations like flashcard generation and statistics.
    *   Interacts with `source_texts`, `flashcards`, and `ai_generation_events` tables.
*   **SpacedRepetition**: Manages spaced repetition learning sessions and data.
    *   Corresponds to `user_flashcard_spaced_repetition` table, linked to `flashcards`.
*   **(Implicit) Users**: User authentication is handled by Supabase. User context (`user_id`) is derived from JWTs for all authenticated requests. RLS at the database level enforces user-specific data access.

## 2. Endpoints

### 2.1. Flashcards Resource (`/flashcards`)

#### 2.1.1. Create Manual Flashcard
*   **Method:** `POST`
*   **Path:** `/flashcards`
*   **Description:** Creates a new flashcard manually. The flashcard source will be set to 'manual' and status to 'active'.
*   **Request Body:**
    ```json
    {
        "front_content": "What is the capital of France?",
        "back_content": "Paris"
    }
    ```
*   **Response Body (Success 201 - Created):**
    ```json
    {
        "id": "uuid-of-new-flashcard",
        "user_id": "uuid-of-user",
        "source_text_id": null,
        "front_content": "What is the capital of France?",
        "back_content": "Paris",
        "source": "manual",
        "status": "active",
        "created_at": "timestamp",
        "updated_at": "timestamp"
    }
    ```
*   **Error Codes:**
    *   `400 Bad Request`: Invalid request payload (e.g., missing fields, content too long).
    *   `401 Unauthorized`: Authentication required.
    *   `422 Unprocessable Entity`: Validation error (e.g. content length).

#### 2.1.2. List User's Flashcards
*   **Method:** `GET`
*   **Path:** `/flashcards`
*   **Description:** Retrieves a list of flashcards for the authenticated user.
*   **Query Parameters:**
    *   `status` (optional, string): Filter by status (e.g., `active`, `pending_review`). Defaults to `active` if not specified.
    *   `source` (optional, string): Filter by source (e.g., `manual`, `ai_suggestion`).
    *   `page` (optional, int): Page number for pagination (e.g., `1`). Defaults to `1`.
    *   `size` (optional, int): Number of items per page (e.g., `20`). Defaults to `20`.
*   **Response Body (Success 200 - OK):**
    ```json
    {
        "items": [
            {
                "id": "uuid-of-flashcard-1",
                "user_id": "uuid-of-user",
                "source_text_id": "uuid-if-ai-generated-else-null",
                "front_content": "Front of card 1",
                "back_content": "Back of card 1",
                "source": "manual", // or "ai_suggestion"
                "status": "active", // or "pending_review", "rejected"
                "created_at": "timestamp",
                "updated_at": "timestamp"
            }
            // ... more flashcards
        ],
        "total": 25,
        "page": 1,
        "size": 20,
        "pages": 2
    }
    ```
*   **Error Codes:**
    *   `401 Unauthorized`: Authentication required.

#### 2.1.3. Get Specific Flashcard
*   **Method:** `GET`
*   **Path:** `/flashcards/{flashcard_id}`
*   **Description:** Retrieves a specific flashcard by its ID.
*   **Response Body (Success 200 - OK):**
    ```json
    {
        "id": "uuid-of-flashcard",
        "user_id": "uuid-of-user",
        "source_text_id": "uuid-if-ai-generated-else-null",
        "front_content": "Front content",
        "back_content": "Back content",
        "source": "manual", // or "ai_suggestion"
        "status": "active", // or "pending_review", "rejected"
        "created_at": "timestamp",
        "updated_at": "timestamp"
    }
    ```
*   **Error Codes:**
    *   `401 Unauthorized`: Authentication required.
    *   `404 Not Found`: Flashcard not found or user does not have access.

#### 2.1.4. Update Flashcard
*   **Method:** `PATCH`
*   **Path:** `/flashcards/{flashcard_id}`
*   **Description:** Updates a flashcard's content (front/back) or status (for AI-suggested cards: `pending_review` -> `active` or `rejected`).
*   **Request Body (Example updating content):**
    ```json
    {
        "front_content": "Updated front content"
    }
    ```
*   **Request Body (Example updating status for AI suggestion):**
    ```json
    {
        "status": "active" // or "rejected"
    }
    ```
*   **Response Body (Success 200 - OK):**
    ```json
    {
        "id": "uuid-of-flashcard",
        "user_id": "uuid-of-user",
        "source_text_id": "uuid-if-ai-generated-else-null",
        "front_content": "Updated front content",
        "back_content": "Original or updated back content",
        "source": "manual", // or "ai_suggestion"
        "status": "active", // or "rejected", or original if only content changed
        "created_at": "timestamp",
        "updated_at": "new-timestamp"
    }
    ```
*   **Error Codes:**
    *   `400 Bad Request`: Invalid request payload or invalid status transition.
    *   `401 Unauthorized`: Authentication required.
    *   `404 Not Found`: Flashcard not found or user does not have access.
    *   `422 Unprocessable Entity`: Validation error (e.g. content length, invalid status value).

#### 2.1.5. Delete Flashcard
*   **Method:** `DELETE`
*   **Path:** `/flashcards/{flashcard_id}`
*   **Description:** Deletes a specific flashcard.
*   **Response Body (Success 204 - No Content):** (Empty body)
*   **Error Codes:**
    *   `401 Unauthorized`: Authentication required.
    *   `404 Not Found`: Flashcard not found or user does not have access.

### 2.2. AI Resource (`/ai`)

#### 2.2.1. Generate Flashcards from Text
*   **Method:** `POST`
*   **Path:** `/ai/generate-flashcards`
*   **Description:** User submits text, AI generates flashcard suggestions. Creates `source_texts`, `flashcards` (status `pending_review`, source `ai_suggestion`), and `ai_generation_events` records.
*   **Request Body:**
    ```json
    {
        "text_content": "Long text content (1000-10000 characters) to generate flashcards from..."
    }
    ```
*   **Response Body (Success 200 - OK):**
    Returns a list of generated flashcards pending review.
    ```json
    {
        "source_text_id": "uuid-of-created-source-text",
        "ai_generation_event_id": "uuid-of-created-event",
        "suggested_flashcards": [
            {
                "id": "uuid-of-suggested-flashcard-1",
                "user_id": "uuid-of-user",
                "source_text_id": "uuid-of-created-source-text",
                "front_content": "AI generated question 1?",
                "back_content": "AI generated answer 1.",
                "source": "ai_suggestion",
                "status": "pending_review",
                "created_at": "timestamp",
                "updated_at": "timestamp"
            }
            // ... more suggested flashcards
        ]
    }
    ```
*   **Error Codes:**
    *   `400 Bad Request`: Invalid request payload (e.g., missing `text_content`).
    *   `401 Unauthorized`: Authentication required.
    *   `422 Unprocessable Entity`: Validation error (e.g., `text_content` length not within 1000-10000 characters).
    *   `503 Service Unavailable`: LLM service error or timeout.

#### 2.2.2. Get AI Generation Statistics
*   **Method:** `GET`
*   **Path:** `/ai/generation-stats`
*   **Description:** Retrieves statistics about AI flashcard generation events for the authenticated user.
*   **Query Parameters:**
    *   `page` (optional, int): Page number for pagination. Defaults to `1`.
    *   `size` (optional, int): Number of items per page. Defaults to `20`.
*   **Response Body (Success 200 - OK):**
    ```json
    {
        "items": [
            {
                "id": "uuid-of-event",
                "user_id": "uuid-of-user",
                "source_text_id": "uuid-of-source-text",
                "llm_model_used": "gpt-3.5-turbo",
                "generated_cards_count": 10,
                "accepted_cards_count": 7,
                "rejected_cards_count": 2, // Note: (generated - accepted - rejected) = pending review
                "cost": 0.0015,
                "created_at": "timestamp",
                "updated_at": "timestamp"
            }
            // ... more events
        ],
        "total": 5,
        "page": 1,
        "size": 20,
        "pages": 1
    }
    ```
*   **Error Codes:**
    *   `401 Unauthorized`: Authentication required.

### 2.3. Spaced Repetition Resource (`/spaced-repetition`)

#### 2.3.1. Get Due Flashcards for Review
*   **Method:** `GET`
*   **Path:** `/spaced-repetition/due-cards`
*   **Description:** Retrieves a list of active flashcards that are due for review in the user's spaced repetition schedule.
*   **Query Parameters:**
    *   `limit` (optional, int): Maximum number of cards to return. Defaults to a system-defined limit (e.g., 10 or 20).
*   **Response Body (Success 200 - OK):**
    A list of flashcard objects (full flashcard details as in `GET /flashcards/{flashcard_id}`).
    ```json
    [
        {
            "id": "uuid-of-due-flashcard-1",
            "user_id": "uuid-of-user",
            "source_text_id": null,
            "front_content": "Due card 1 front",
            "back_content": "Due card 1 back",
            "source": "manual",
            "status": "active",
            "created_at": "timestamp",
            "updated_at": "timestamp",
            // Potentially include spaced repetition data like last_reviewed_at if helpful for UI
            "repetition_data": {
                 "due_date": "timestamp",
                 "current_interval": 3, // days
                 "last_reviewed_at": "timestamp"
            }
        }
        // ... more due flashcards
    ]
    ```
*   **Error Codes:**
    *   `401 Unauthorized`: Authentication required.

#### 2.3.2. Submit Flashcard Review Result
*   **Method:** `POST`
*   **Path:** `/spaced-repetition/reviews`
*   **Description:** Submits the user's performance rating for a flashcard review. This updates the spaced repetition data for that card (e.g., next `due_date`, `interval`).
*   **Request Body:**
    ```json
    {
        "flashcard_id": "uuid-of-reviewed-flashcard",
        "performance_rating": 5 // Example: an integer rating (1-5) or specific value expected by SR algorithm
    }
    ```
*   **Response Body (Success 200 - OK):**
    The updated `user_flashcard_spaced_repetition` record.
    ```json
    {
        "id": "uuid-of-repetition-record",
        "user_id": "uuid-of-user",
        "flashcard_id": "uuid-of-reviewed-flashcard",
        "due_date": "new-due-date-timestamp",
        "current_interval": 5, // new interval in days
        "last_reviewed_at": "current-timestamp",
        "data_extra": {}, // any extra data stored by the SR algorithm
        "created_at": "timestamp",
        "updated_at": "current-timestamp"
    }
    ```
*   **Error Codes:**
    *   `400 Bad Request`: Invalid request payload (e.g., missing fields).
    *   `401 Unauthorized`: Authentication required.
    *   `404 Not Found`: `flashcard_id` not found or not active for the user.
    *   `422 Unprocessable Entity`: Invalid `performance_rating` or other SR algorithm constraint.

## 3. Uwierzytelnianie i autoryzacja

*   **Authentication Mechanism:** Supabase JWT (JSON Web Tokens).
    *   Clients will obtain a JWT from Supabase upon successful login.
    *   This JWT must be included in the `Authorization` header of API requests as a Bearer token (e.g., `Authorization: Bearer <your-supabase-jwt>`).
    *   FastAPI backend will use Supabase client libraries or a JWT middleware to validate the token and extract user information (`user_id`).
*   **Authorization Mechanism:** PostgreSQL Row Level Security (RLS).
    *   RLS policies are defined on database tables (`source_texts`, `flashcards`, `ai_generation_events`, `user_flashcard_spaced_repetition`).
    *   These policies ensure that users can only access or modify their own data. The `user_id` from the JWT is used by PostgreSQL functions like `auth.uid()` in RLS policies.
    *   API endpoints operate under the security context of the authenticated user.

## 4. Walidacja i logika biznesowa

### 4.1. Validation Conditions

*   **`source_texts`**:
    *   `text_content`: Required, string, length between 1000 and 10000 characters (for `POST /ai/generate-flashcards`).
*   **`flashcards`**:
    *   `front_content`: Required, string, max length 500 characters.
    *   `back_content`: Required, string, max length 1000 characters.
    *   `source`: Must be one of `flashcard_source_enum` ('manual', 'ai_suggestion'). Set by API logic.
    *   `status`: Must be one of `flashcard_status_enum` ('active', 'pending_review', 'rejected'). Managed by API logic based on operation.
    *   **DB Constraint `check_flashcard_source_and_status`**:
        *   If `source = 'manual'`, then `status` must be `'active'` and `source_text_id` must be `NULL`. (Ensured by `POST /flashcards` logic).
        *   If `source = 'ai_suggestion'`, then `source_text_id` must not be `NULL` and `status` must be one of `'active'`, `'pending_review'`, `'rejected'`. (Ensured by `POST /ai/generate-flashcards` and `PATCH /flashcards/{id}` logic).
*   **Pydantic Models**: Request bodies will be validated using Pydantic models in FastAPI, enforcing data types, required fields, and length constraints.

### 4.2. Business Logic Implementation

*   **AI Flashcard Generation (`POST /ai/generate-flashcards`):**
    1.  Validates `text_content` length.
    2.  Creates a `source_texts` record for the user with `text_content`.
    3.  Calls the configured LLM API with `text_content`.
    4.  For each suggestion from LLM:
        *   Creates a `flashcards` record:
            *   `user_id` = authenticated user.
            *   `source_text_id` = ID of the created `source_texts` record.
            *   `front_content`, `back_content` from LLM.
            *   `source` = `'ai_suggestion'`.
            *   `status` = `'pending_review'`.
    5.  Creates an `ai_generation_events` record:
        *   `user_id` = authenticated user.
        *   `source_text_id` = ID of the created `source_texts` record.
        *   `llm_model_used` (from config/LLM response).
        *   `generated_cards_count` = number of suggestions received.
        *   `accepted_cards_count` = 0.
        *   `rejected_cards_count` = 0.
        *   `cost` (if available from LLM API).
    6.  Returns the list of suggested flashcards.
*   **Manual Flashcard Creation (`POST /flashcards`):**
    1.  Validates `front_content` and `back_content`.
    2.  Creates a `flashcards` record:
        *   `user_id` = authenticated user.
        *   `source_text_id` = `NULL`.
        *   `front_content`, `back_content` from request.
        *   `source` = `'manual'`.
        *   `status` = `'active'`.
    3.  Initializes `user_flashcard_spaced_repetition` record for this new card with default values (e.g., due immediately).
*   **Updating AI Flashcard Status (`PATCH /flashcards/{id}` with status change):**
    1.  Validates `flashcard_id` belongs to user and is an AI suggestion (`source='ai_suggestion'`).
    2.  Validates new status (`'active'` or `'rejected'`).
    3.  Updates `flashcards.status`.
    4.  If `flashcards.source_text_id` is not NULL:
        *   Find the related `ai_generation_events` record.
        *   If new status is `'active'`, increment `accepted_cards_count`.
        *   If new status is `'rejected'`, increment `rejected_cards_count`.
    5.  If status becomes `'active'`, ensures a `user_flashcard_spaced_repetition` record is created/initialized for this card.
*   **Spaced Repetition Logic (`POST /spaced-repetition/reviews`):**
    1.  Validates `flashcard_id` belongs to user and is active.
    2.  Retrieves or creates the `user_flashcard_spaced_repetition` record.
    3.  Uses an integrated spaced repetition algorithm (e.g., SM-2 variant) to calculate the next `due_date` and `current_interval` based on `performance_rating` and current repetition data.
    4.  Updates `last_reviewed_at`, `due_date`, `current_interval`, and any `data_extra`.

This plan provides a comprehensive structure for the REST API, aligning with the project's requirements. 