"""
schemas.py - Pydantic models for request validation.

These schemas validate the data coming from HTML forms before
it reaches the database or Gemini API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# Valid choices for dropdowns
VALID_GOALS = ["Weight Loss", "Muscle Gain", "General Wellness", "Flexibility"]
VALID_INTENSITIES = ["Low", "Medium", "High"]


class UserInput(BaseModel):
    """
    Validates the workout generation form input.
    """
    name: str = Field(..., min_length=1, max_length=100, description="User's name")
    user_id: str = Field(..., min_length=1, max_length=50, description="Unique user ID")
    age: int = Field(..., ge=10, le=100, description="Age between 10 and 100")
    weight: float = Field(..., gt=20, le=300, description="Weight in kg (20-300)")
    goal: str = Field(..., description="Fitness goal")
    intensity: str = Field(..., description="Workout intensity level")

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v):
        if v not in VALID_GOALS:
            raise ValueError(f"Goal must be one of: {', '.join(VALID_GOALS)}")
        return v

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, v):
        if v not in VALID_INTENSITIES:
            raise ValueError(f"Intensity must be one of: {', '.join(VALID_INTENSITIES)}")
        return v

    @field_validator("name", "user_id")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip()


class FeedbackInput(BaseModel):
    """
    Validates the feedback form input.
    """
    user_id: str = Field(..., min_length=1, max_length=50, description="User ID")
    feedback: str = Field(..., min_length=5, max_length=1000, description="Feedback text")

    @field_validator("user_id", "feedback")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip()
