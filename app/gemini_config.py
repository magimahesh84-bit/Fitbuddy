"""
gemini_config.py - Centralized configuration for Google Gemini models and options.

Reads model assignments from environment variables with safe defaults.
Uses gemini-3.5-flash-lite as the default primary model to protect against
strict single-model daily quota exhaustion on the free tier.
"""

import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# ─── Centralized Model Configurations ────────────────────────────────────────
GEMINI_WORKOUT_MODEL = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-3.5-flash-lite")
GEMINI_NUTRITION_MODEL = os.getenv("GEMINI_NUTRITION_MODEL", "gemini-3.5-flash-lite")
GEMINI_UPDATE_MODEL = os.getenv("GEMINI_UPDATE_MODEL", "gemini-3.5-flash-lite")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite")
