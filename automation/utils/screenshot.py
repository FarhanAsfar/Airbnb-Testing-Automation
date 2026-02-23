import re
from pathlib import Path
from django.conf import settings


def take_screenshot(page, test_name: str) -> str:
    """Save screenshot and return relative path."""
    folder = Path(settings.SCREENSHOTS_DIR)
    folder.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    filename = re.sub(r'[^a-z0-9]+', '_', test_name.lower()).strip('_') + '.png'
    filepath = folder / filename

    page.screenshot(path=str(filepath), full_page=True)
    print(f"  📸 Screenshot saved: {filepath.name}")
    return str(filepath)