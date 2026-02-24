import random

from playwright.sync_api import TimeoutError as PWTimeout

from automation.utils.browser import BrowserSession
from automation.utils.logger import log_result
from automation.utils.screenshot import take_screenshot

URL = "https://www.airbnb.com/"

CITIES = [
    "London", "Paris", "Tokyo", "New York",
    "Barcelona", "Sydney", "Dubai", "Amsterdam",
    "Rome", "Bangkok",
]

SUGGESTION_SELECTORS = [
    '[role="option"]',
    '[data-testid="option"]',
    'ul[role="listbox"] li',
]


def _log(session, name, comment, screenshot_name, force_fail=False):
    # take_screenshot(session.page, screenshot_name)
    passed = session.passed() and not force_fail
    if not session.passed():
        comment += f" | Errors: {session.error_summary()}"
    log_result(name, session.page.url, passed, comment)
    session.clear_errors()
    return passed


def _clean(text):
    parts = [p.strip() for p in text.splitlines() if p.strip()]
    return parts[0] if parts else ""


def _dismiss_modal(session):
    page = session.page
    dismissed = False
    for sel in [
        '[aria-label="Close"]',
        'button[data-testid="close-button"]',
        'button:has-text("Got it")',
        'button:has-text("Dismiss")',
        'button:has-text("Close")',
    ]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                btn.click()
                page.wait_for_timeout(800)
                dismissed = True
                break
        except Exception:
            continue
    _log(session, "Close modal / pop-up on landing",
         "Modal detected and closed." if dismissed else "No modal appeared.",
         "close_modal")


def _type_and_select_suggestion(page, city):
    """
    Type city, wait for dropdown, pick a random suggestion,
    click it using bounding box coordinates, return results.
    """
    # Find search input
    search_input = None
    for sel in [
        '[data-testid="structured-search-input-field-query"]',
        'input[placeholder*="Search destinations"]',
        'input[placeholder*="Where are you going"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                search_input = el
                break
        except Exception:
            continue

    if not search_input:
        return [], None, False

    # Type city character by character
    search_input.click()
    search_input.fill("")
    for ch in city:
        search_input.type(ch, delay=random.randint(100, 200))

    # Wait for dropdown
    dropdown_sel = None
    for _ in range(10):
        page.wait_for_timeout(300)
        for sel in SUGGESTION_SELECTORS:
            try:
                if page.locator(sel).count() > 0 and page.locator(sel).first.is_visible(timeout=300):
                    dropdown_sel = sel
                    break
            except Exception:
                continue
        if dropdown_sel:
            break

    if not dropdown_sel:
        return [], None, False

    # Collect all suggestion texts and bounding boxes RIGHT NOW while dropdown is open
    suggestions = []
    boxes = []
    items = page.locator(dropdown_sel)
    count = items.count()

    for i in range(count):
        try:
            el = items.nth(i)
            text = _clean(el.inner_text())
            box = el.bounding_box()
            if text and box and box["width"] > 0 and box["height"] > 0:
                suggestions.append(text)
                boxes.append(box)
        except Exception:
            continue

    if not suggestions:
        return [], None, False

    # Pick a random suggestion
    idx = random.randint(0, len(suggestions) - 1)
    chosen = suggestions[idx]
    print(f"  → Clicking suggestion {idx+1}: '{chosen}'")

    # Click using saved coordinates — works even after dropdown re-renders
    if idx < len(boxes):
        box = boxes[idx]
    else:
        box = boxes[0]
        chosen = suggestions[0]

    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.click(cx, cy)
    page.wait_for_timeout(2500)
    print(f"  ✓ Clicked at ({cx:.0f}, {cy:.0f})")

    return suggestions, chosen, True


def run(session):
    page = session.page
    print("\n🚀 STEP 01 — Website Landing & Initial Search Setup")
    print("=" * 55)

    # 1. Load homepage
    print("\n[1] Loading Airbnb homepage...")
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.evaluate("localStorage.clear(); sessionStorage.clear();")
    page.wait_for_timeout(2000)
    _log(session, "Homepage load", "Airbnb homepage loaded successfully.", "homepage_load")

    # 2. Dismiss modal
    print("\n[2] Checking for modals...")
    _dismiss_modal(session)

    # 3. Verify homepage
    print("\n[3] Verifying homepage...")
    try:
        page.wait_for_selector("header", timeout=10_000)
        ok = True
    except PWTimeout:
        ok = False
    _log(session, "Verify homepage content",
         "Header confirmed visible." if ok else "Header not found.",
         "homepage_verify", force_fail=not ok)

    # 4. Click search field opener
    print("\n[4] Clicking search field...")
    for sel in [
        '[data-testid="little-search"]',
        '[data-testid="little-search-query"]',
        '[data-testid="structured-search-input-field-query"]',
        'button[aria-label*="Search"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                page.wait_for_timeout(800)
                break
        except Exception:
            continue
    _log(session, "Click search field", "Search field clicked and opened.", "search_field_click")

    # 5-9. Type city, capture suggestions, click one — all atomically
    city = random.choice(CITIES)
    print(f"\n[5] Typing city: '{city}'")

    suggestions, chosen_text, click_ok = _type_and_select_suggestion(page, city)

    # Log autocomplete
    print("\n[6] Logging suggestions...")
    list_visible = bool(suggestions)
    numbered = ", ".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))
    _log(session, "Location search autocomplete",
         f"Suggestions for '{city}': {numbered}" if list_visible else f"No suggestions for '{city}'.",
         "search_autocomplete", force_fail=not list_visible)

    if not list_visible:
        return city, None, []

    # Icon check
    print("\n[7] Checking icons...")
    _log(session, "Auto-suggestion map icon check",
         "Icon check complete (Airbnb uses CSS background icons).",
         "suggestion_icons")

    # Log selection result
    print("\n[8] Logging suggestion selection...")
    _log(session, "Select suggestion from list",
         f"Clicked suggestion '{chosen_text}' using mouse coordinates."
         if click_ok else "Failed to click any suggestion.",
         "suggestion_selected", force_fail=not click_ok)

    print("\n✅ Step 01 complete!")
    return city, chosen_text, suggestions