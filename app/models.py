"""
models.py - SQLAlchemy ORM models (database tables).

Defines the User table which stores user info, workout plans, and feedback.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """
    User table - stores all user data, plans, and feedback.

    Columns:
        id              - Auto-increment primary key
        user_id         - User-chosen identifier (unique)
        name            - User's name
        age             - User's age
        weight          - User's weight in kg
        goal            - Fitness goal (e.g. Weight Loss, Muscle Gain)
        intensity       - Workout intensity (Low, Medium, High)
        workout_plan    - Original AI-generated 7-day workout plan
        nutrition_tip   - AI-generated nutrition/recovery tip
        updated_plan    - Revised plan after user feedback (nullable)
        feedback        - User's feedback text (nullable)
        created_at      - Timestamp when record was created
        updated_at      - Timestamp when record was last updated
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String(50), nullable=False)
    intensity = Column(String(20), nullable=False)
    workout_plan = Column(Text, nullable=True)
    nutrition_tip = Column(Text, nullable=True)
    updated_plan = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
