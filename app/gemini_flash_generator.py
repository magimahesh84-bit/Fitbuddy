"""
gemini_flash_generator.py - Nutrition/recovery tip generation using Gemini.

Uses the centralized Gemini service with configurable models,
quota detection, and a safe local fallback if the API is unavailable or quota is exceeded.
"""

import logging
from app.gemini_config import GEMINI_NUTRITION_MODEL, GEMINI_FALLBACK_MODEL
from app.gemini_service import (
    call_gemini_with_retry,
    GeminiQuotaError,
    GeminiRateLimitError,
    GeminiCapacityError,
    GeminiAuthError,
    GeminiModelError,
    GeminiError,
)

logger = logging.getLogger("fitbuddy.nutrition")

# Safe local fallback guidance per Step 9 requirements
LOCAL_NUTRITION_FALLBACK = (
    "Focus on balanced meals containing carbohydrates, protein, fruits or vegetables, "
    "and adequate fluids. Recovery, sleep, and regular meals are important alongside physical activity."
)


def generate_nutrition_tip_with_flash(goal: str, weight: float, age: int) -> str:
    """
    Generate a concise nutrition/recovery tip using Gemini.
    Uses GEMINI_NUTRITION_MODEL (default: gemini-3.5-flash-lite) as primary.
    Falls back gracefully to safe local guidance if API quota is reached or unavailable.

    Args:
        goal:   User's fitness goal
        weight: User's weight in kg
        age:    User's age

    Returns:
        A short nutrition/recovery tip as a string.
    """
    prompt = f"""
You are a certified nutrition and recovery specialist.

Generate a concise, practical nutrition and recovery tip for a person with
the following profile:

- Age: {age} years old
- Weight: {weight} kg
- Fitness Goal: {goal}

Provide:
1. One specific nutrition tip related to their goal ({goal}).
2. One hydration recommendation.
3. One recovery tip (e.g., sleep, stretching, rest).

Keep the response short (3-5 sentences total), practical, and easy to follow.
Do not provide medical advice. Keep it general wellness guidance.
Safety & Wellness: Emphasize balanced nutrition and sustainable habits. Do not suggest crash diets, extreme fasting, restrictive calorie targets, or performance supplements/drugs.
"""

    try:
        tip = call_gemini_with_retry(
            prompt=prompt,
            primary_model=GEMINI_NUTRITION_MODEL,
            fallback_model=GEMINI_FALLBACK_MODEL,
        )
        if tip and tip.strip():
            return tip.strip()
    except GeminiQuotaError as qe:
        logger.warning("Gemini daily quota reached during nutrition generation. Using local fallback: %s", qe)
    except Exception as e:
        logger.warning("Nutrition generation encountered error. Using local fallback: %s", e)

    # Safe local fallback per Step 9
    return LOCAL_NUTRITION_FALLBACK
