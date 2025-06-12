import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from openai import AsyncOpenAI

from src.core.config import Settings
from src.dtos import LLMFlashcardSuggestion, LLMGenerateResponse

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when LLM service operations fail."""

    def __init__(self, operation: str, details: str, status_code: Optional[int] = None):
        self.operation = operation
        self.details = details
        self.status_code = status_code
        super().__init__(f"LLM service error during {operation}: {details}")


class LLMClient:
    """Client for communicating with OpenRouter.ai LLM service using OpenAI SDK."""

    def __init__(self):
        self.settings = Settings()
        self.client: Optional[AsyncOpenAI] = None

        # Prompt template for flashcard generation
        self.flashcard_generation_prompt = """
Based on the following text, generate educational flashcards that test comprehension and key concepts.
Each flashcard should have a clear question (front) and comprehensive answer (back).
Generate 5-10 flashcards that cover the most important concepts from the text.

Guidelines:
- Questions should be specific and test understanding
- Answers should be complete but concise
- Focus on key facts, concepts, and relationships
- Avoid overly obvious or trivial questions
- Include different question types (what, how, why, when, etc.)

Text: {text_content}

Return response in the following JSON format:
{{
  "flashcards": [
    {{"front_content": "What is...?", "back_content": "The answer is..."}},
    {{"front_content": "How does...?", "back_content": "It works by..."}}
  ]
}}

Respond ONLY with valid JSON. Do not include any other text or explanations.
        """.strip()

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = AsyncOpenAI(
            base_url=self.settings.OPENROUTER_BASE_URL,
            api_key=self.settings.OPENROUTER_API_KEY,
            timeout=self.settings.LLM_TIMEOUT,
            default_headers={
                "HTTP-Referer": "https://localhost:3000",  # Optional: replace with your domain
                "X-Title": "Flashcard Generator",  # Optional: app name
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.close()

    async def generate_flashcards(self, text_content: str) -> LLMGenerateResponse:
        """
        Generate flashcards from text using OpenRouter.ai LLM via OpenAI SDK.

        Args:
            text_content: Source text to generate flashcards from

        Returns:
            LLM response with generated flashcards

        Raises:
            LLMServiceError: If LLM service fails or returns invalid response
        """
        if not self.client:
            raise LLMServiceError(
                operation="generate_flashcards",
                details="LLM client not initialized. Use async context manager.",
            )

        try:
            # Prepare the prompt
            formatted_prompt = self.flashcard_generation_prompt.format(
                text_content=text_content
            )

            logger.info(f"Sending request to LLM service: {self.settings.LLM_MODEL}")
            start_time = datetime.utcnow()

            # Make async request to OpenRouter.ai via OpenAI SDK
            response = await self.client.chat.completions.create(
                model=self.settings.LLM_MODEL,
                messages=[{"role": "user", "content": formatted_prompt}],
                max_tokens=self.settings.LLM_MAX_TOKENS,
                temperature=0.7,  # Some creativity but not too random
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
            )

            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"LLM request completed in {elapsed_time:.2f}s")

            # Extract the generated content
            if not response.choices:
                raise LLMServiceError(
                    operation="parse_response", details="No choices in LLM response"
                )

            content = response.choices[0].message.content
            if not content:
                raise LLMServiceError(
                    operation="parse_response", details="Empty content in LLM response"
                )

            logger.debug(f"Raw LLM response: {content[:200]}...")

            # Replace to meet the JSON format requirements
            content = content.replace("```json", "").replace("```", "")

            # Parse the JSON response
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {content[:500]}")
                raise LLMServiceError(
                    operation="parse_json",
                    details=f"Invalid JSON in LLM response: {str(e)}",
                )

            # Validate and convert to our models
            if "flashcards" not in parsed_content:
                raise LLMServiceError(
                    operation="validate_response",
                    details="Missing 'flashcards' key in LLM response",
                )

            flashcards = []
            for card_data in parsed_content["flashcards"]:
                if not isinstance(card_data, dict):
                    continue

                if "front_content" not in card_data or "back_content" not in card_data:
                    logger.warning(f"Skipping invalid flashcard: {card_data}")
                    continue

                try:
                    flashcard = LLMFlashcardSuggestion(
                        front_content=str(card_data["front_content"]).strip(),
                        back_content=str(card_data["back_content"]).strip(),
                    )
                    flashcards.append(flashcard)
                except Exception as e:
                    logger.warning(
                        f"Failed to create flashcard from data {card_data}: {e}"
                    )
                    continue

            if not flashcards:
                raise LLMServiceError(
                    operation="validate_flashcards",
                    details="No valid flashcards generated from LLM response",
                )

            # Calculate cost if available (OpenRouter provides usage info)
            cost = None
            if hasattr(response, "usage") and response.usage:
                # Using OpenRouter pricing for Gemma 3 27B: $0.10/M input, $0.20/M output
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                input_cost = (input_tokens / 1_000_000) * 0.10
                output_cost = (output_tokens / 1_000_000) * 0.20
                cost = input_cost + output_cost

            logger.info(
                f"Successfully generated {len(flashcards)} flashcards using {self.settings.LLM_MODEL}"
            )

            return LLMGenerateResponse(
                flashcards=flashcards, model_used=self.settings.LLM_MODEL, cost=cost
            )

        except asyncio.TimeoutError:
            logger.error(f"LLM request timeout after {self.settings.LLM_TIMEOUT}s")
            raise LLMServiceError(
                operation="timeout",
                details=f"Request timeout after {self.settings.LLM_TIMEOUT} seconds",
            )
        except Exception as e:
            # Handle OpenAI SDK specific exceptions
            if hasattr(e, "status_code"):
                logger.error(f"OpenAI API error {e.status_code}: {str(e)}")
                raise LLMServiceError(
                    operation="api_error",
                    details=f"API error: {str(e)}",
                    status_code=e.status_code,
                )
            elif isinstance(e, LLMServiceError):
                # Re-raise our custom exceptions
                raise
            else:
                logger.error(f"Unexpected error in LLM client: {str(e)}")
                raise LLMServiceError(
                    operation="unexpected_error", details=f"Unexpected error: {str(e)}"
                )


async def get_llm_client() -> LLMClient:
    """Dependency function to get LLM client instance."""
    return LLMClient()
