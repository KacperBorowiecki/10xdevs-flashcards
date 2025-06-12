import uuid
import logging
from datetime import datetime
import asyncio
from typing import Optional

from supabase import Client
from src.dtos import DashboardStats, AIGenerationSummary, DashboardContext

logger = logging.getLogger(__name__)

class DashboardServiceError(Exception):
    """Custom exception for Dashboard Service errors."""
    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Dashboard Service Error in {operation}: {details}")

class DashboardService:
    """Service for aggregating dashboard statistics and data."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def _validate_user_access(self, user_id: uuid.UUID) -> None:
        """
        Validate user access with additional security checks.
        
        Args:
            user_id: User UUID to validate
            
        Raises:
            ValueError: If user_id is invalid
        """
        if not user_id:
            raise ValueError("User ID is required")
        
        # Check for nil UUID (additional security)
        if user_id == uuid.UUID('00000000-0000-0000-0000-000000000000'):
            raise ValueError("Invalid user ID provided")
    
    async def get_dashboard_stats(self, user_id: uuid.UUID) -> DashboardStats:
        """
        Agreguje dane z różnych endpointów dla Dashboard.
        
        Args:
            user_id: UUID of the authenticated user
            
        Returns:
            DashboardStats with aggregated statistics
            
        Raises:
            DashboardServiceError: If any data aggregation fails
        """
        try:
            # Enhanced security validation
            self._validate_user_access(user_id)
            
            logger.info(f"Fetching dashboard stats for user {user_id}")
            
            # Równoległe wywołania wszystkich trzech endpointów dla performance
            total_flashcards_task = self._get_total_active_flashcards(user_id)
            due_cards_today_task = self._get_due_cards_today(user_id)
            ai_stats_task = self._get_ai_generation_summary(user_id)
            
            # Czekamy na wszystkie równoległe operacje
            total_flashcards, due_cards_today, ai_stats = await asyncio.gather(
                total_flashcards_task,
                due_cards_today_task,
                ai_stats_task,
                return_exceptions=True
            )
            
            # Error handling dla każdego endpoint osobno z fallback values
            if isinstance(total_flashcards, Exception):
                logger.warning(f"Failed to get total flashcards for user {user_id}: {total_flashcards}")
                total_flashcards = 0
            
            if isinstance(due_cards_today, Exception):
                logger.warning(f"Failed to get due cards for user {user_id}: {due_cards_today}")
                due_cards_today = 0
            
            if isinstance(ai_stats, Exception):
                logger.warning(f"Failed to get AI stats for user {user_id}: {ai_stats}")
                ai_stats = AIGenerationSummary(total_generated=0, total_accepted=0)
            
            dashboard_stats = DashboardStats(
                total_flashcards=total_flashcards,
                due_cards_today=due_cards_today,
                ai_stats=ai_stats
            )
            
            logger.info(f"Successfully aggregated dashboard stats for user {user_id}")
            return dashboard_stats
            
        except ValueError as e:
            logger.warning(f"Input validation failed for dashboard stats: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting dashboard stats for user {user_id}: {str(e)}")
            raise DashboardServiceError(
                operation="get_dashboard_stats",
                details=f"Unexpected error: {str(e)}"
            )
    
    async def _get_total_active_flashcards(self, user_id: uuid.UUID) -> int:
        """
        Pobiera łączną liczbę aktywnych fiszek użytkownika.
        Odpowiednik: GET /api/v1/flashcards?status=active&page=1&size=1
        """
        try:
            # Count query dla aktywnych fiszek
            response = self.supabase.table("flashcards") \
                .select("id", count="exact") \
                .eq("user_id", str(user_id)) \
                .eq("status", "active") \
                .execute()
            
            return response.count or 0
            
        except Exception as e:
            logger.error(f"Error getting total active flashcards for user {user_id}: {str(e)}")
            raise
    
    async def _get_due_cards_today(self, user_id: uuid.UUID) -> int:
        """
        Pobiera liczbę fiszek gotowych do powtórki dziś.
        Odpowiednik: GET /api/v1/spaced-repetition/due-cards?limit=1
        """
        try:
            current_time = datetime.utcnow()
            
            # Count query dla fiszek do powtórki dziś
            response = self.supabase.table("user_flashcard_spaced_repetition") \
                .select("id", count="exact") \
                .eq("user_id", str(user_id)) \
                .lte("due_date", current_time.isoformat()) \
                .execute()
            
            return response.count or 0
            
        except Exception as e:
            logger.error(f"Error getting due cards for user {user_id}: {str(e)}")
            raise
    
    async def _get_ai_generation_summary(self, user_id: uuid.UUID) -> AIGenerationSummary:
        """
        Pobiera zagregowane statystyki AI (suma wszystkich generated i accepted).
        Odpowiednik: GET /api/v1/ai/generation-stats?page=1&size=100
        """
        try:
            # Pobranie wszystkich ai_generation_events dla użytkownika
            response = self.supabase.table("ai_generation_events") \
                .select("generated_cards_count, accepted_cards_count") \
                .eq("user_id", str(user_id)) \
                .execute()
            
            if not response.data:
                return AIGenerationSummary(total_generated=0, total_accepted=0)
            
            # Agregacja sum ze wszystkich eventów
            total_generated = sum(event.get("generated_cards_count", 0) for event in response.data)
            total_accepted = sum(event.get("accepted_cards_count", 0) for event in response.data)
            
            return AIGenerationSummary(
                total_generated=total_generated,
                total_accepted=total_accepted
            )
            
        except Exception as e:
            logger.error(f"Error getting AI generation summary for user {user_id}: {str(e)}")
            raise
    
    async def get_dashboard_context(self, user_id: uuid.UUID, user_email: str) -> DashboardContext:
        """
        Pobiera pełny kontekst dla dashboard template.
        
        Args:
            user_id: UUID of the authenticated user
            user_email: Email of the authenticated user
            
        Returns:
            DashboardContext with all required data for template
        """
        try:
            stats = await self.get_dashboard_stats(user_id)
            
            return DashboardContext(
                user_email=user_email,
                stats=stats,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard context for user {user_id}: {str(e)}")
            
            # Return context with error message and fallback stats
            fallback_stats = DashboardStats(
                total_flashcards=0,
                due_cards_today=0,
                ai_stats=AIGenerationSummary(total_generated=0, total_accepted=0)
            )
            
            return DashboardContext(
                user_email=user_email,
                stats=fallback_stats,
                error_message="Nie udało się załadować statystyk dashboard"
            )

def get_dashboard_service(supabase_client: Client) -> DashboardService:
    """Dependency function to get Dashboard service instance."""
    return DashboardService(supabase_client) 