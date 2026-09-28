"""
main.py - FastAPI application entry point for FitBuddy.

This is the file that Uvicorn runs:
    uvicorn app.main:app --reload

It sets up the FastAPI app, mounts static files,
creates database tables, includes all routes, and logs Gemini model configuration on startup.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routes import router
from app.gemini_config import (
    GEMINI_WORKOUT_MODEL,
    GEMINI_NUTRITION_MODEL,
    GEMINI_UPDATE_MODEL,
    GEMINI_FALLBACK_MODEL,
)

logger = logging.getLogger("uvicorn.info")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Safe startup logging to verify model configuration at runtime (Step 5 & 18)."""
    banner = f"""
================================
FITBUDDY GEMINI CONFIGURATION
Workout model: {GEMINI_WORKOUT_MODEL}
Nutrition model: {GEMINI_NUTRITION_MODEL}
Update model: {GEMINI_UPDATE_MODEL}
================================
""".strip()
    print(banner, flush=True)
    logger.info(banner)
    yield


# ─── Create FastAPI Application ────────────────────────────────────────────
app = FastAPI(
    title="FitBuddy",
    description="AI Fitness Plan Generator using Google Gemini",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Mount Static Files (CSS, images) ─────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── Create Database Tables ───────────────────────────────────────────────
# This creates all tables defined in models.py if they don't already exist.
# The database file (fitbuddy.db) is created automatically.
Base.metadata.create_all(bind=engine)

# ─── Include Routes ───────────────────────────────────────────────────────
app.include_router(router)
