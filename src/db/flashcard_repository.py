import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from supabase import Client

logger = logging.getLogger(__name__)


class FlashcardRepository:
    """Repository pattern for optimized flashcard database operations."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_flashcard_by_id_and_user(
        self, flashcard_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get flashcard by ID with user ownership verification using single query.

        Args:
            flashcard_id: UUID of the flashcard
            user_id: UUID of the user

        Returns:
            Flashcard data if found and accessible, None otherwise
        """
        try:
            response = (
                self.supabase.table("flashcards")
                .select("*")
                .eq("id", str(flashcard_id))
                .eq("user_id", str(user_id))
                .limit(1)
                .execute()
            )

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting flashcard {flashcard_id}: {str(e)}")
            raise

    def update_flashcard_optimized(
        self, flashcard_id: uuid.UUID, user_id: uuid.UUID, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update flashcard using optimized single query with built-in ownership check.

        Args:
            flashcard_id: UUID of the flashcard to update
            user_id: UUID of the user
            updates: Dictionary of fields to update

        Returns:
            Updated flashcard data if successful, None if not found/no access
        """
        try:
            # Add automatic timestamp update
            updates_with_timestamp = updates.copy()
            updates_with_timestamp["updated_at"] = datetime.utcnow().isoformat()

            # Single query with ownership verification built-in
            response = (
                self.supabase.table("flashcards")
                .update(updates_with_timestamp)
                .eq("id", str(flashcard_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating flashcard {flashcard_id}: {str(e)}")
            raise

    def get_ai_generation_event_by_source_text(
        self, source_text_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get AI generation event by source text ID for statistics updates.

        Args:
            source_text_id: UUID of the source text

        Returns:
            AI generation event data if found, None otherwise
        """
        try:
            response = (
                self.supabase.table("ai_generation_events")
                .select("*")
                .eq("source_text_id", str(source_text_id))
                .limit(1)
                .execute()
            )

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(
                f"Error getting AI generation event for source_text {source_text_id}: {str(e)}"
            )
            raise

    def update_ai_generation_event_stats(
        self, event_id: uuid.UUID, stats_updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update AI generation event statistics using optimized query.

        Args:
            event_id: UUID of the AI generation event
            stats_updates: Dictionary of statistics to update

        Returns:
            Updated event data if successful, None otherwise
        """
        try:
            # Add automatic timestamp update
            stats_with_timestamp = stats_updates.copy()
            stats_with_timestamp["updated_at"] = datetime.utcnow().isoformat()

            response = (
                self.supabase.table("ai_generation_events")
                .update(stats_with_timestamp)
                .eq("id", str(event_id))
                .execute()
            )

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating AI generation event {event_id}: {str(e)}")
            raise

    async def batch_get_flashcards_with_stats(
        self, user_id: uuid.UUID, flashcard_ids: List[uuid.UUID]
    ) -> List[Dict[str, Any]]:
        """
        Batch get multiple flashcards for efficiency.

        Args:
            user_id: UUID of the user
            flashcard_ids: List of flashcard UUIDs

        Returns:
            List of flashcard data
        """
        try:
            if not flashcard_ids:
                return []

            # Convert UUIDs to strings for query
            id_strings = [str(fid) for fid in flashcard_ids]

            response = (
                self.supabase.table("flashcards")
                .select("*")
                .eq("user_id", str(user_id))
                .in_("id", id_strings)
                .execute()
            )

            return response.data or []

        except Exception as e:
            logger.error(f"Error batch getting flashcards: {str(e)}")
            raise

    async def get_flashcard_with_concurrent_check(
        self,
        flashcard_id: uuid.UUID,
        user_id: uuid.UUID,
        expected_updated_at: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get flashcard with optional concurrent modification check.

        Args:
            flashcard_id: UUID of the flashcard
            user_id: UUID of the user
            expected_updated_at: Expected timestamp for optimistic locking

        Returns:
            Flashcard data if found and not modified, None otherwise

        Raises:
            ValueError: If concurrent modification detected
        """
        try:
            flashcard = await self.get_flashcard_by_id_and_user(flashcard_id, user_id)

            if not flashcard:
                return None

            # Check for concurrent modifications if timestamp provided
            if expected_updated_at:
                current_updated_at = flashcard.get("updated_at")
                if isinstance(current_updated_at, str):
                    current_updated_at = datetime.fromisoformat(
                        current_updated_at.replace("Z", "+00:00")
                    )

                time_diff = abs(
                    (current_updated_at - expected_updated_at).total_seconds()
                )
                if time_diff > 1:  # More than 1 second difference
                    raise ValueError(
                        "Flashcard was modified by another process. Please refresh and try again."
                    )

            return flashcard

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Error getting flashcard with concurrent check {flashcard_id}: {str(e)}"
            )
            raise

    async def execute_transaction_simulation(
        self, operations: List[Dict[str, Any]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Simulate transaction behavior for multiple operations.
        Note: Supabase doesn't support true transactions, but we can implement
        compensating actions for rollback scenarios.

        Args:
            operations: List of operation dictionaries with 'type', 'table', 'data', etc.

        Returns:
            List of operation results
        """
        results = []
        executed_operations = []

        try:
            for i, operation in enumerate(operations):
                op_type = operation.get("type")
                table = operation.get("table")
                data = operation.get("data")
                conditions = operation.get("conditions", {})

                if op_type == "update":
                    query = self.supabase.table(table).update(data)
                    for key, value in conditions.items():
                        query = query.eq(key, value)

                    response = query.execute()
                    result = response.data[0] if response.data else None
                    results.append(result)
                    executed_operations.append(
                        {"index": i, "type": op_type, "table": table, "result": result}
                    )

                elif op_type == "insert":
                    response = self.supabase.table(table).insert(data).execute()
                    result = response.data[0] if response.data else None
                    results.append(result)
                    executed_operations.append(
                        {"index": i, "type": op_type, "table": table, "result": result}
                    )

            return results

        except Exception as e:
            # Implement compensating actions (simplified rollback)
            logger.error(
                f"Transaction simulation failed at operation {len(executed_operations)}: {str(e)}"
            )
            await self._compensate_operations(executed_operations)
            raise

    async def _compensate_operations(
        self, executed_operations: List[Dict[str, Any]]
    ) -> None:
        """
        Implement compensating actions for failed transaction simulation.

        Args:
            executed_operations: List of successfully executed operations to compensate
        """
        try:
            # Reverse operations in LIFO order
            for operation in reversed(executed_operations):
                op_type = operation.get("type")

                if op_type == "insert":
                    # For insert, try to delete the created record
                    result = operation.get("result")
                    if result and "id" in result:
                        try:
                            self.supabase.table(operation["table"]).delete().eq(
                                "id", result["id"]
                            ).execute()
                            logger.info(
                                f"Compensated insert operation for {operation['table']} id {result['id']}"
                            )
                        except Exception as comp_error:
                            logger.error(
                                f"Failed to compensate insert: {str(comp_error)}"
                            )

                # For updates, we would need to store original values to restore them
                # This is a simplified implementation

        except Exception as e:
            logger.error(f"Error during compensation: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on database connection and table accessibility.

        Returns:
            Health status information
        """
        try:
            # Simple query to check connection
            response = self.supabase.table("flashcards").select("id").limit(1).execute()

            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "connection": "active",
                "tables_accessible": True,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "connection": "failed",
            }
