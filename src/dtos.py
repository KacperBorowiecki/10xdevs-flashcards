from pydantic import BaseModel, Field
from typing import Optional, List, TypeVar, Generic
from datetime import datetime
import uuid

# Importuj bazowe modele i Enumy z schemas.py, aby na nich bazować
from src.db.schemas import (
    FlashcardBase,
    AiGenerationEventBase,
    UserFlashcardSpacedRepetitionBase,
    FlashcardSourceEnum,
    FlashcardStatusEnum
)

# --- Modele Ogólne ---
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

# --- Modele dla komunikacji z LLM ---

class LLMFlashcardSuggestion(BaseModel):
    """Model reprezentujący pojedynczą sugestię fiszki z LLM."""
    front_content: str = Field(..., description="Front content of the suggested flashcard")
    back_content: str = Field(..., description="Back content of the suggested flashcard")

class LLMGenerateResponse(BaseModel):
    """Model odpowiedzi z LLM."""
    flashcards: List[LLMFlashcardSuggestion] = Field(..., description="List of generated flashcard suggestions")
    model_used: str = Field(..., description="Name of the LLM model used")
    cost: Optional[float] = Field(None, description="Cost of the LLM request in USD")

# --- Modele dla zasobu Flashcards ---

class FlashcardManualCreateRequest(BaseModel):
    front_content: str = Field(..., max_length=500, description="Front content of the flashcard.")
    back_content: str = Field(..., max_length=1000, description="Back content of the flashcard.")

class FlashcardResponse(FlashcardBase):
    # Dziedziczy wszystkie pola z FlashcardBase (id, user_id, source_text_id, front_content, back_content, source, status, created_at, updated_at)
    # To jest zgodne z większością odpowiedzi dla fiszek w api-plan.md
    model_config = {"from_attributes": True}

class FlashcardPatchRequest(BaseModel):
    front_content: Optional[str] = Field(None, max_length=500, description="Optional new front content.")
    back_content: Optional[str] = Field(None, max_length=1000, description="Optional new back content.")
    status: Optional[FlashcardStatusEnum] = Field(None, description="Optional new status, e.g., for AI suggestions 'active' or 'rejected'.")

# --- Modele dla zasobu AI ---

class AIGenerateFlashcardsRequest(BaseModel):
    text_content: str = Field(..., min_length=1000, max_length=10000, description="Text content to generate flashcards from (1000-10000 characters).")

# AISuggestedFlashcard może być tym samym co FlashcardResponse, ponieważ struktura jest identyczna,
# a wartości pól 'source' i 'status' będą ustawiane przez logikę serwera.
# Użyjemy FlashcardResponse dla uproszczenia.
class AIGenerateFlashcardsResponse(BaseModel):
    source_text_id: uuid.UUID
    ai_generation_event_id: uuid.UUID
    suggested_flashcards: List[FlashcardResponse]

class AIGenerationEventResponse(AiGenerationEventBase):
    # Dziedziczy wszystkie pola z AiGenerationEventBase
    model_config = {"from_attributes": True}

# --- Modele dla zasobu Spaced Repetition ---

class RepetitionData(BaseModel):
    due_date: datetime
    current_interval: int # in days
    last_reviewed_at: Optional[datetime]

class DueFlashcardResponse(FlashcardResponse):
    # Rozszerza FlashcardResponse o dane dotyczące powtórek
    repetition_data: Optional[RepetitionData] = Field(None, description="Spaced repetition data if available.")

class SubmitReviewRequest(BaseModel):
    flashcard_id: uuid.UUID = Field(..., description="ID of the flashcard being reviewed.")
    performance_rating: int = Field(..., ge=1, le=5, description="User's performance rating for the flashcard (e.g., 1-5).") # Zakładamy skalę 1-5

class SpacedRepetitionRecordResponse(UserFlashcardSpacedRepetitionBase):
    # Dziedziczy wszystkie pola z UserFlashcardSpacedRepetitionBase
    model_config = {"from_attributes": True}

# --- Modele dla Dashboard ---

class AIGenerationSummary(BaseModel):
    """Podsumowanie statystyk generowania AI."""
    total_generated: int = Field(..., ge=0, description="Łączna liczba wygenerowanych fiszek")
    total_accepted: int = Field(..., ge=0, description="Łączna liczba zaakceptowanych fiszek")
    
    @property
    def acceptance_ratio(self) -> str:
        """Zwraca ratio w formacie 'x/y' dla wyświetlenia."""
        return f"{self.total_accepted}/{self.total_generated}"

class DashboardStats(BaseModel):
    """Zagregowane statystyki dla Dashboard."""
    total_flashcards: int = Field(..., ge=0, description="Łączna liczba aktywnych fiszek")
    due_cards_today: int = Field(..., ge=0, description="Liczba fiszek do powtórki dziś")
    ai_stats: AIGenerationSummary = Field(..., description="Podsumowanie statystyk AI")

class DashboardContext(BaseModel):
    """Główny kontekst przekazywany do template Dashboard."""
    user_email: str = Field(..., description="Email zalogowanego użytkownika")
    stats: DashboardStats = Field(..., description="Statystyki użytkownika")
    error_message: Optional[str] = Field(None, description="Komunikat błędu jeśli wystąpił")

# Przykładowe użycie (można usunąć lub zakomentować)
if __name__ == "__main__":
    # Przykładowe dane dla FlashcardManualCreateRequest
    manual_card_data = {"front_content": "What is FastAPI?", "back_content": "A modern Python web framework."}
    manual_card = FlashcardManualCreateRequest(**manual_card_data)
    print(f"Manual Card Create Request: {manual_card.model_dump_json(indent=2)}")

    # Przykładowe dane dla FlashcardResponse
    flashcard_resp_data = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "source_text_id": None,
        "front_content": "Hello",
        "back_content": "World",
        "source": FlashcardSourceEnum.MANUAL,
        "status": FlashcardStatusEnum.ACTIVE,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    flashcard_resp = FlashcardResponse(**flashcard_resp_data)
    print(f"Flashcard Response: {flashcard_resp.model_dump_json(indent=2)}")

    # Przykładowe dane dla AIGenerateFlashcardsRequest
    ai_gen_req_data = {"text_content": "x" * 1500} # Tekst o długości 1500 znaków
    ai_gen_req = AIGenerateFlashcardsRequest(**ai_gen_req_data)
    print(f"AI Generate Request: {ai_gen_req.model_dump_json(indent=2)}") 