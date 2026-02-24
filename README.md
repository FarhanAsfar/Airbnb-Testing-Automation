# 🧪 Airbnb Search Automation Framework

An end-to-end browser automation framework that validates the Airbnb search flow step-by-step using Playwright.

This project simulates a real user journey:

1. Enter location  
2. Select suggestion  
3. Select dates  
4. Select number of guests  
5. Submit search  
6. Validate results  

The framework is built for reliability, structured logging, and deterministic UI validation.

---

# 📌 Project Goals

- Automate the Airbnb search journey
- Validate UI behavior at every step
- Capture screenshots for traceability
- Log pass/fail results clearly
- Enforce step dependencies
- Make debugging failures fast and obvious

This is not just automation — it is structured validation.

---

# 🏗️ Project Structure
automation/
│
├── steps/
│ ├── step01_landing.py # Location input + autocomplete
│ ├── step02_suggestions.py # Suggestion selection
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

# 🚀 Installation

## 1️⃣ Clone Repository

```bash
git clone <your-repository-url>
cd <project-folder>

Install Dependencies
pip install -r requirements.txt

Install Playwright Browsers
playwright install


Running the Automation
Run Full Flow
python manage.py run_automation


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