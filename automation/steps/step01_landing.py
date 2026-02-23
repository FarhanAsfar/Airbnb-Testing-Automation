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