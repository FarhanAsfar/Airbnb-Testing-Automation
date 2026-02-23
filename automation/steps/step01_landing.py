import random
import time

from playwright.sync_api import Page, TimeoutError as PWTimeout

from automation.utils.browser import BrowserSession
from automation.utils.logger import log_result
from automation.utils.screenshot import take_screenshot

URL = "https://www.airbnb.com/"

CITIES = [
    "London", "Paris", "Tokyo", "New York",
    "Barcelona", "Sydney", "Dubai", "Amsterdam",
    "Rome", "Bangkok",
]

# ---helper functions--
def _check(session: BrowserSession, name: str, comment: str, screenshot_name: str):
    take_screenshot(session.page, screenshot_name)
    passed = session.passed()
    if not passed:
        comment += f" | Errors: {session.error_summary()}"
    log_result(name, session.page.url, passed, comment)
    session.clear_errors()


def _clean_suggestion(text: str) -> str:
    """Flatten multiline suggestion text into a single clean line."""
    parts = [p.strip() for p in text.splitlines() if p.strip()]
    # First part is the place name, rest are type labels — join nicely
    if len(parts) > 1:
        return f"{parts[0]} ({', '.join(parts[1:])})"
    return parts[0] if parts else ""

def _dismiss_modal(session: BrowserSession):
    page = session.page
    dismissed = False

    close_selectors = [
        '[aria-label="Close"]',
        '[aria-label="Translation on"]',
        'button[data-testid="close-button"]',
        '[data-testid="translation-announce-modal"] button',
        'button:has-text("Got it")',
        'button:has-text("Dismiss")',
        'button:has-text("Close")',
    ]

    for selector in close_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                btn.click()
                page.wait_for_timeout(800)
                dismissed = True
                break
        except Exception:
            continue

    take_screenshot(page, "close_modal_pop_up_on_landing")
    passed = session.passed()
    comment = (
        "Modal/pop-up detected and closed successfully after page landing."
        if dismissed
        else "No modal or pop-up appeared on page landing."
    )
    if not passed:
        comment += f" | Errors: {session.error_summary()}"
    log_result("Close modal / pop-up on landing", page.url, passed, comment)
    session.clear_errors()


def _find_and_activate_search(page: Page) -> tuple[bool, object]:
    """Click the search bar to open the panel, then return the active input element."""
    opener_selectors = [
        '[data-testid="structured-search-input-field-query"]',
        '[data-testid="little-search"]',
        '[data-testid="little-search-query"]',
        'button[aria-label*="Search"]',
        '[placeholder*="Search destinations"]',
        '[placeholder*="Where are you going"]',
    ]
    for sel in opener_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                page.wait_for_timeout(1000)
                break
        except Exception:
            continue

    input_selectors = [
        '[data-testid="structured-search-input-field-query"]',
        'input[placeholder*="Search destinations"]',
        'input[placeholder*="Where are you going"]',
        'input[name="query"]',
        '[aria-label="Search destinations"]',
        'input[type="text"][data-testid]',
        'input[type="search"]',
    ]
    for sel in input_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                page.wait_for_timeout(500)
                return True, el
        except Exception:
            continue

    return False, None


def _type_like_human(element, text: str):
    """Type directly into element with visible human-like delays."""
    element.focus()
    for char in text:
        element.type(char, delay=random.randint(140, 320))


def run(session: BrowserSession):
    page = session.page
    print("\n🚀 STEP 01 — Website Landing & Initial Search Setup")
    print("=" * 55)

    # ── 1. Navigate to Airbnb ──────────────────────────────
    print("\n[1] Opening Airbnb homepage...")
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2000)
    _check(
        session,
        "Homepage load",
        "Successfully navigated to airbnb.com. Homepage loaded with DOM content ready.",
        "homepage_load",
    )

    # ── 2. Dismiss any modal ───────────────────────────────
    print("\n[2] Checking for modals...")
    _dismiss_modal(session)

    # ── 3. Confirm homepage ────────────────────────────────
    print("\n[3] Verifying homepage content...")
    try:
        page.wait_for_selector('header, [data-testid="main-navigation"]', timeout=10_000)
        homepage_ok = True
    except PWTimeout:
        homepage_ok = False

    _check(
        session,
        "Verify homepage content",
        "Homepage verified: header and navigation elements are visible and rendered correctly."
        if homepage_ok
        else "Homepage verification failed: header/navigation element not found in DOM.",
        "homepage_verify",
    )

    # ── 4. Click search field ──────────────────────────────
    print("\n[4] Clicking on the search field...")
    clicked, search_input = _find_and_activate_search(page)
    _check(
        session,
        "Click search field",
        "Search bar clicked successfully. Input field is active and ready for input."
        if clicked
        else "Failed to locate and click the search input field.",
        "search_field_click",
    )

    # ── 5. Select random city & type it ───────────────────
    city = random.choice(CITIES)
    print(f"\n[5] Typing city: '{city}'")

    if search_input:
        _type_like_human(search_input, city)
    else:
        for char in city:
            page.keyboard.type(char)
            time.sleep(random.uniform(0.15, 0.32))
