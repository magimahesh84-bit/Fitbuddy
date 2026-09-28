"""
gemini_generator.py - Workout plan generation using Google Gemini.

Uses the centralized Gemini service with configurable models,
quota detection, and transient error resilience.
"""

from app.gemini_config import GEMINI_WORKOUT_MODEL, GEMINI_FALLBACK_MODEL
from app.gemini_service import (
    call_gemini_with_retry,
    GeminiQuotaError,
    GeminiRateLimitError,
    GeminiCapacityError,
    GeminiAuthError,
    GeminiModelError,
    GeminiError,
)


def generate_workout_gemini(name: str, age: int, weight: float,
                            goal: str, intensity: str) -> str:
    """
    Generate a personalized 7-day workout plan using Gemini.
    Uses GEMINI_WORKOUT_MODEL (default: gemini-3.5-flash-lite) as primary.

    Args:
        name:      User's name
        age:       User's age
        weight:    User's weight in kg
        goal:      Fitness goal (e.g. Weight Loss, Muscle Gain)
        intensity: Workout intensity (Low, Medium, High)

    Returns:
        A formatted string containing the 7-day workout plan.

    Raises:
        Exception: With clean, user-friendly error text if generation fails.
    """
    prompt = f"""
You are an expert fitness coach. Create a detailed, personalized 7-day workout plan
for the following user:

- Name: {name}
- Age: {age} years old
- Weight: {weight} kg
- Fitness Goal: {goal}
- Workout Intensity: {intensity}

Please provide a complete 7-day workout plan with the following structure for EACH day:

**Day [number] - [Workout Focus]**
- **Warm-up:** (5-10 minutes of specific warm-up exercises)
- **Main Workout:** (List each exercise with sets, reps or duration)
- **Rest:** (Rest periods between sets/exercises)
- **Cooldown/Recovery:** (5-10 minutes of cooldown stretches)

Guidelines:
- Tailor the exercises to the user's goal ({goal}) and intensity ({intensity}).
- For {intensity} intensity, adjust the number of sets, reps, and rest periods accordingly.
- Include at least one rest day or active recovery day in the week.
- Make the plan progressive and balanced.
- Use clear, simple language that a beginner can understand.
- Format each day clearly with the day number and workout focus.
- Safety & Wellness: Keep all content age-appropriate and focused on sustainable, healthy physical activity. Do not include extreme physical challenges, dangerous movements, crash diets, restrictive calorie targets, or performance supplements/drugs.

Provide the complete 7-day plan now.
"""

    try:
        return call_gemini_with_retry(
            prompt=prompt,
            primary_model=GEMINI_WORKOUT_MODEL,
            fallback_model=GEMINI_FALLBACK_MODEL,
        )
    except (GeminiQuotaError, GeminiRateLimitError, GeminiCapacityError,
            GeminiAuthError, GeminiModelError, GeminiError) as ge:
        raise Exception(str(ge))
    except Exception as e:
        raise Exception(f"Workout generation error: {str(e)}")
