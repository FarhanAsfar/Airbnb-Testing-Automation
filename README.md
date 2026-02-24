# 🧪 Airbnb Search Automation 

An end-to-end browser automation script that validates the Airbnb search flow step-by-step using Playwright.

This project simulates a real user journey:

1. Enter location  
2. Select suggestion  
3. Select dates  
4. Select number of guests  
5. Submit search  
6. Validate results  

---


# 🏗️ Project Structure
automation/
│
├── steps/
│ ├── step01_landing.py # (step1 + step2) Location input + autocomplete
│ ├──
│ ├── step03_dates.py # Date picker handling
│ ├── step04_guests.py # Guest selection
│ └── step05_results.py # Search results validation
│
├── utils/
│ ├── browser.py # Browser session wrapper
│ ├── logger.py # Structured logging
│ ├── screenshot.py # Screenshot utility
│ └── session.py # Session state management
│
└── run_automation.py # Entry point (Django command)

---

# Project Installation

### Clone Repository

```bash
git clone <your-repository-url>
cd <project-folder>
```

### Activate UV Environment
```
uv venv
```

### Install Dependencies
```
uv pip install -r requirements.txt
```

### Migrate Database
```
uv run manage.py migrate
```

### Running the Automation
```bash
uv run manage.py run_automation
```

### To Check the Database in Admin Panel
**Create a Super User**
```bash
uv run manage.py createsuperuser
```
**Run the Server**
```
uv run manage.py runserver
```
**Visit**
```
http://127.0.0.1:8000/admin/
```

---


Execution Flow
Step 01 — Landing & Location Search

Opens Airbnb homepage

Types city name

Waits for autocomplete suggestions

Selects a valid suggestion

Logs result

Takes screenshot

Step 02 — Suggestion Selection

Validates suggestion list

Ensures selected option exists

Confirms selection state

Step 03 — Date Selection

Opens date picker

Selects valid check-in and check-out

Verifies selected dates in input

Logs validation

Step 04 — Guest Selection

Opens guest selector popup

Selects random number of adults (2–5)

Verifies guest count in input field

Submits search

Logs each verification step

Takes screenshots after each validation

Step 05 — Results Validation

Confirms URL contains search parameters

Validates results are visible

Checks listing elements exist

Logs pass/fail
