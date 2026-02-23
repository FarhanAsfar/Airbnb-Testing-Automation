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



    """Type directly into element with visible human-like delays."""
    element.focus()
    for char in text:
        element.type(char, delay=random.randint(140, 320))