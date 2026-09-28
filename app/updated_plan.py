"""
updated_plan.py - Feedback-based workout plan updating using Gemini.

Takes the user's original workout plan and their feedback, then generates
an updated plan that incorporates the requested changes.
Uses the centralized Gemini service with configurable models and quota detection.
"""

from app.gemini_config import GEMINI_UPDATE_MODEL, GEMINI_FALLBACK_MODEL
from app.gemini_service import (
    call_gemini_with_retry,
    GeminiQuotaError,
    GeminiRateLimitError,
    GeminiCapacityError,
    GeminiAuthError,
    GeminiModelError,
    GeminiError,
)

QUOTA_FEEDBACK_MESSAGE = (
    "AI plan updates are temporarily unavailable because the Gemini API quota has been reached. "
    "Your original plan and feedback have been preserved."
)


def update_workout_plan(original_plan: str, feedback: str,
                        goal: str, intensity: str) -> str:
    """
    Generate an updated 7-day workout plan based on user feedback.

    The original plan is preserved in the database — this function
    generates a NEW revised plan stored separately.

    Uses GEMINI_UPDATE_MODEL (default: gemini-3.5-flash-lite).
    If the daily API quota is exhausted, raises GeminiQuotaError so
    the application preserves the original plan without faking an update.

    Args:
        original_plan: The original AI-generated workout plan
        feedback:      User's feedback (e.g. "Add more cardio")
        goal:          User's fitness goal
        intensity:     User's preferred intensity

    Returns:
        A formatted string containing the updated 7-day workout plan.

    Raises:
        GeminiQuotaError: When daily API quota is reached.
        Exception: On other generation errors.
    """
    prompt = f"""
You are an expert fitness coach. A user has received the following 7-day workout plan
and has provided feedback requesting changes.

**ORIGINAL WORKOUT PLAN:**
{original_plan}

**USER FEEDBACK:**
{feedback}

**USER'S GOAL:** {goal}
**USER'S INTENSITY:** {intensity}

Please generate a COMPLETE REVISED 7-day workout plan that:
1. Preserves the useful and effective parts of the original plan.
2. Applies the user's requested changes from their feedback.
3. Maintains the same structured format (Day-by-day with warm-up, main workout, rest, cooldown).
4. Stays aligned with the user's goal ({goal}) and intensity ({intensity}).
5. Safety & Wellness: Keep the plan balanced, age-appropriate, and sustainable. Do not include extreme exercises, dangerous challenges, crash diets, restrictive calorie targets, or performance supplements/drugs.

Provide the complete updated 7-day plan. Do NOT just list the changes — provide the
full revised plan that the user can follow.
"""

    try:
        return call_gemini_with_retry(
            prompt=prompt,
            primary_model=GEMINI_UPDATE_MODEL,
            fallback_model=GEMINI_FALLBACK_MODEL,
        )
    except GeminiQuotaError:
        # Step 10: Clear quota message for feedback update
        raise GeminiQuotaError(QUOTA_FEEDBACK_MESSAGE)
    except (GeminiRateLimitError, GeminiCapacityError, GeminiAuthError,
            GeminiModelError, GeminiError) as ge:
        raise Exception(str(ge))
    except Exception as e:
        raise Exception(f"Plan update error: {str(e)}")
