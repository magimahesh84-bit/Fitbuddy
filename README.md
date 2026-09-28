# FitBuddy – AI Fitness Plan Generator

> A web-based AI fitness plan generator powered by Google Gemini (gemini-3.5-flash-lite), built with FastAPI, SQLAlchemy, and Jinja2 templates.

---

## 📋 Project Overview

FitBuddy is a college project that generates personalized 7-day workout plans using Google Gemini AI. Users enter their profile information (name, age, weight, fitness goal, intensity), and the application creates a tailored workout plan along with nutrition/recovery tips. Users can also provide feedback to get an updated plan without losing the original.

---

## ✨ Features

- **Personalized 7-Day Workout Plan** – Generated using Gemini 3.8 Flash based on user profile
- **Nutrition & Recovery Tips** – Quick tips generated using Gemini 3.8 Flash
- **Feedback System** – Submit feedback to regenerate an improved plan
- **Plan History** – Both original and updated plans are preserved
- **Input Validation** – Pydantic-based validation for all form inputs
- **Error Handling** – Graceful handling of API failures and invalid input
- **Responsive Design** – Works on desktop and mobile devices

---

## 🛠 Technologies Used

| Component      | Technology                  |
|----------------|-----------------------------|
| Backend        | Python, FastAPI, Uvicorn    |
| AI Model       | Google Gemini (Primary: gemini-3.5-flash-lite, Fallback: gemini-3.6-flash via google-genai SDK) |
| Frontend       | HTML, CSS, Jinja2 Templates |
| Database       | SQLite, SQLAlchemy          |
| Validation     | Pydantic                    |
| Configuration  | python-dotenv, .env file    |

---

## 📁 Project Structure

```
FitBuddy/
│
├── app/
│   ├── __init__.py              # Package initializer
│   ├── main.py                  # FastAPI app entry point
│   ├── routes.py                # All route handlers
│   ├── database.py              # SQLAlchemy database setup
│   ├── models.py                # ORM models (User table)
│   ├── schemas.py               # Pydantic validation schemas
│   ├── gemini_generator.py      # Workout generation (Gemini 3.8 Flash)
│   ├── gemini_flash_generator.py # Nutrition tips (Gemini 3.8 Flash)
│   └── updated_plan.py          # Feedback-based plan updates (Gemini 3.8 Flash)
│
├── templates/
│   ├── index.html               # Homepage with input form
│   └── result.html              # Workout plan display + feedback
│
├── static/
│   ├── css/
│   │   └── style.css            # Application styles
│   └── images/                  # Image assets
│
├── .env                         # API key (not committed to Git)
├── .env.example                 # Example environment config
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🚀 Installation & Setup

### 1. Prerequisites

- **Python 3.10+** installed on your system
- **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 2. Clone/Open the Project

```cmd
cd C:\Users\abdul\Documents\project
```

### 3. Create a Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies

```cmd
pip install -r requirements.txt
```

### 5. Configure Gemini API Key

Create a `.env` file in the project root (or edit the existing one):

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

> The app also supports `GOOGLE_API_KEY` for backward compatibility.

> ⚠️ Never share or commit your `.env` file. It is already in `.gitignore`.

### 6. Database Setup

The SQLite database (`fitbuddy.db`) is **created automatically** when the application starts for the first time. No manual setup required.

---

## ▶️ Running the Application

```cmd
uvicorn app.main:app --reload
```

The application will be available at:

| URL                                | Description           |
|------------------------------------|-----------------------|
| http://127.0.0.1:8000              | Homepage              |
| http://127.0.0.1:8000/docs         | FastAPI Auto Docs     |

---

## 🔗 Available Routes

| Method | Route               | Description                        |
|--------|---------------------|------------------------------------|
| GET    | `/`                 | Homepage with workout form         |
| POST   | `/generate-workout` | Generate workout plan + tip        |
| POST   | `/submit-feedback`  | Submit feedback for plan update    |

---

## 🧪 Testing the Application

### Test 1: Open Homepage
Visit `http://127.0.0.1:8000` – you should see the FitBuddy form.

### Test 2: Submit User Information
Fill in: Name, User ID, Age, Weight, Goal, Intensity → Click **Generate**.

### Test 3: Verify Workout Plan
A 7-day workout plan should appear on the result page.

### Test 4: Verify Nutrition Tip
A nutrition/recovery tip should appear below the user summary.

### Test 5: Verify Database Storage
Check `fitbuddy.db` – the user record should be stored.

### Test 6: Submit Feedback
Enter feedback like "Add more cardio" → Click **Update My Plan**.

### Test 7: Verify Updated Plan
A revised plan should appear alongside the original.

### Test 8: Verify Original Plan Unchanged
The original plan should still be visible and unchanged.

### Test 9: API Documentation
Visit `http://127.0.0.1:8000/docs` – verify all user endpoints are documented and no admin endpoint exists.

### Test 10: Data Persistence
Stop the server, restart it – existing user and workout records in `fitbuddy.db` persist across restarts.

---

## 📝 Notes

- The Gemini API key must be valid for workout generation to work.
- The application includes a disclaimer that AI-generated content is not medical advice.
- Gemini 3.5 Flash-Lite is used for workouts, nutrition tips, and plan updates, with Gemini 3.6 Flash configured as fallback (via the `google-genai` SDK).
- If the API key is unavailable, the homepage still functions.

---

## 👨‍💻 Author

College Project – Built with FastAPI + Google Gemini AI
