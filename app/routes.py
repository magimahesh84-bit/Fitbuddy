"""
routes.py - All FastAPI route handlers for FitBuddy.

Routes:
    GET  /                  → Homepage with input form
    POST /generate-workout  → Generate workout plan + nutrition tip
    POST /submit-feedback   → Update plan based on feedback
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.database import get_db
from app.models import User
from app.schemas import UserInput, FeedbackInput, VALID_GOALS, VALID_INTENSITIES
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan
from app.gemini_service import format_user_friendly_error

# Create router
router = APIRouter()

# Setup Jinja2 template engine — templates folder is at project root
templates = Jinja2Templates(directory="templates")


# ─── HOMEPAGE ──────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """
    Render the homepage with the workout generation form.
    Passes valid goals and intensities to populate dropdowns.
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "goals": VALID_GOALS,
        "intensities": VALID_INTENSITIES,
    })


# ─── GENERATE WORKOUT ─────────────────────────────────────────────────────

@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    name: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Receive user form data, validate it, generate a workout plan and
    nutrition tip using Gemini, save everything to the database,
    and render the result page.
    """
    # Step 1: Validate input using Pydantic schema
    try:
        user_input = UserInput(
            name=name, user_id=user_id,
            age=age, weight=weight,
            goal=goal, intensity=intensity
        )
    except ValidationError as e:
        # Extract readable error messages
        errors = []
        for err in e.errors():
            field = err.get("loc", ["unknown"])[-1]
            msg = err.get("msg", "Invalid value")
            errors.append(f"{field}: {msg}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "goals": VALID_GOALS,
            "intensities": VALID_INTENSITIES,
            "error": " | ".join(errors),
        })

    # Step 2: Check if user_id already exists
    existing_user = db.query(User).filter(User.user_id == user_input.user_id).first()
    if existing_user:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "goals": VALID_GOALS,
            "intensities": VALID_INTENSITIES,
            "error": f"User ID '{user_input.user_id}' already exists. Please choose a different User ID.",
        })

    # Step 3: Generate workout plan using Gemini
    try:
        workout_plan = generate_workout_gemini(
            name=user_input.name,
            age=user_input.age,
            weight=user_input.weight,
            goal=user_input.goal,
            intensity=user_input.intensity,
        )
    except Exception as e:
        import logging
        logging.getLogger("fitbuddy.routes").error("Workout generation error: %s", e)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "goals": VALID_GOALS,
            "intensities": VALID_INTENSITIES,
            "error": format_user_friendly_error(e),
        })

    # Step 4: Generate nutrition/recovery tip using Gemini Flash
    try:
        nutrition_tip = generate_nutrition_tip_with_flash(
            goal=user_input.goal,
            weight=user_input.weight,
            age=user_input.age,
        )
    except Exception:
        nutrition_tip = "Stay hydrated and get enough sleep for optimal recovery."

    # Step 5: Save to database
    try:
        new_user = User(
            user_id=user_input.user_id,
            name=user_input.name,
            age=user_input.age,
            weight=user_input.weight,
            goal=user_input.goal,
            intensity=user_input.intensity,
            workout_plan=workout_plan,
            nutrition_tip=nutrition_tip,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "goals": VALID_GOALS,
            "intensities": VALID_INTENSITIES,
            "error": f"Database error: {str(e)}",
        })

    # Step 6: Render result page
    return templates.TemplateResponse("result.html", {
        "request": request,
        "user": new_user,
        "workout_plan": workout_plan,
        "nutrition_tip": nutrition_tip,
        "updated_plan": None,
        "feedback_submitted": False,
    })


# ─── SUBMIT FEEDBACK ──────────────────────────────────────────────────────

@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Receive feedback for an existing user's workout plan,
    generate an updated plan using Gemini, and save it
    WITHOUT overwriting the original plan.
    """
    # Step 1: Validate feedback input
    try:
        feedback_input = FeedbackInput(user_id=user_id, feedback=feedback)
    except ValidationError as e:
        errors = []
        for err in e.errors():
            field = err.get("loc", ["unknown"])[-1]
            msg = err.get("msg", "Invalid value")
            errors.append(f"{field}: {msg}")
        return templates.TemplateResponse("result.html", {
            "request": request,
            "user": None,
            "workout_plan": "",
            "nutrition_tip": "",
            "updated_plan": None,
            "feedback_submitted": False,
            "error": " | ".join(errors),
        })

    # Step 2: Find the user in the database
    user = db.query(User).filter(User.user_id == feedback_input.user_id).first()
    if not user:
        return templates.TemplateResponse("result.html", {
            "request": request,
            "user": None,
            "workout_plan": "",
            "nutrition_tip": "",
            "updated_plan": None,
            "feedback_submitted": False,
            "error": f"User ID '{feedback_input.user_id}' not found.",
        })

    # Step 3: Generate updated plan using Gemini
    try:
        revised_plan = update_workout_plan(
            original_plan=user.workout_plan,
            feedback=feedback_input.feedback,
            goal=user.goal,
            intensity=user.intensity,
        )
    except Exception as e:
        import logging
        logging.getLogger("fitbuddy.routes").error("Plan update error for user '%s': %s", feedback_input.user_id, e)
        # Preserve user feedback in database without overwriting original plan (Step 10 & 13)
        try:
            user.feedback = feedback_input.feedback
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()

        return templates.TemplateResponse("result.html", {
            "request": request,
            "user": user,
            "workout_plan": user.workout_plan,
            "nutrition_tip": user.nutrition_tip or "",
            "updated_plan": user.updated_plan,
            "feedback_submitted": False,
            "error": format_user_friendly_error(e),
        })

    # Step 4: Save updated plan and feedback (original plan stays unchanged)
    try:
        user.updated_plan = revised_plan
        user.feedback = feedback_input.feedback
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("result.html", {
            "request": request,
            "user": user,
            "workout_plan": user.workout_plan,
            "nutrition_tip": user.nutrition_tip or "",
            "updated_plan": None,
            "feedback_submitted": False,
            "error": f"Database error: {str(e)}",
        })

    # Step 5: Render result with both original and updated plans
    return templates.TemplateResponse("result.html", {
        "request": request,
        "user": user,
        "workout_plan": user.workout_plan,
        "nutrition_tip": user.nutrition_tip or "",
        "updated_plan": revised_plan,
        "feedback_submitted": True,
    })
