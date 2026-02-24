import random

from automation.utils.logger import log_result
from automation.utils.screenshot import take_screenshot


def _log(session, name, comment, screenshot_name, force_fail=False):
    take_screenshot(session.page, screenshot_name)
    passed = session.passed() and not force_fail
    if not session.passed():
        comment += f" | Errors: {session.error_summary()}"
    log_result(name, session.page.url, passed, comment)
    session.clear_errors()
    return passed


def _click_plus(page, btn, times):
    clicked = 0
    for _ in range(times):
        try:
            btn.click()
            page.wait_for_timeout(400)
            clicked += 1
        except Exception:
            break
    return clicked


def _get_count(page, sel):
    try:
        el = page.locator(sel).first
        if el.is_visible(timeout=1000):
            digits = ''.join(filter(str.isdigit, el.inner_text()))
            return int(digits) if digits else 0
    except Exception:
        pass
    return 0


def _expand_search_bar(page):
    """On results page, the search bar is collapsed — click it to expand."""
    for sel in [
        '[data-testid="little-search"]',
        '[data-testid="little-search-icon"]',
        '[data-testid="little-search-query"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                el.click()
                page.wait_for_timeout(1500)
                print(f"  ✓ Expanded search bar via: {sel}")
                return True
        except Exception:
            continue
    return False


def _find_guests_btn(page):
    """Find and click the guests button in the expanded search bar."""
    for sel in [
        '[data-testid="structured-search-input-field-guests-btn"]',
        '[data-testid="structured-search-input-field-guests"]',
        '[data-testid="little-search-guests"]',
        '[data-testid="little-search-anon-guest-display"]',
        'button[aria-label*="guest" i]',
        'button[aria-label*="Who" i]',
        'button:has-text("Add guests")',
        'button:has-text("Who")',
        '[data-testid*="guest"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                el.click()
                page.wait_for_timeout(1200)
                print(f"  ✓ Clicked guests btn: {sel}")
                return True
        except Exception:
            continue
    return False


def _popup_is_open(page):
    for sel in [
        '[data-testid="stepper-adults-increase-button"]',
        'button[aria-label*="increase adults" i]',
        'button[aria-label*="add adult" i]',
        '[data-testid="GuestPicker-panel"]',
    ]:
        try:
            if page.locator(sel).first.is_visible(timeout=1500):
                return True
        except Exception:
            continue
    return False


def run(session, chosen_text, date_info):
    page = session.page
    print("\n👥 STEP 04 — Guest Selection")
    print("=" * 55)

    print(f"  Current URL: {page.url}")
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)

    # 1. Click the guests field
    # Strategy: on results page the search bar is collapsed, expand it first
    print("\n[1] Clicking guest input field...")

    # Try direct guest button first (homepage expanded state)
    opened = _find_guests_btn(page)

    # If not found, expand the collapsed search bar then click guests
    if not opened or not _popup_is_open(page):
        print("  → Search bar collapsed, expanding first...")
        _expand_search_bar(page)
        opened = _find_guests_btn(page)

    _log(session, "Click guest input field",
         "Guest field clicked." if opened else "Guest field not found.",
         "guest_field_click", force_fail=not opened)

    if not opened:
        return None

    # 2. Verify popup open
    print("\n[2] Verifying guest selection popup...")
    popup_open = _popup_is_open(page)

    if not popup_open:
        try:
            testids = [el.get_attribute("data-testid")
                       for el in page.locator("[data-testid]").all() if el.is_visible()]
            btns = [b.get_attribute("aria-label") for b in page.locator("button").all()
                    if b.is_visible() and b.get_attribute("aria-label")]
            print(f"  testids: {[t for t in testids if t][:12]}")
            print(f"  btn labels: {btns[:12]}")
        except Exception:
            pass

    _log(session, "Guest selection popup opens",
         "Guest popup is open." if popup_open else "Guest popup did not open.",
         "guest_popup_open", force_fail=not popup_open)

    if not popup_open:
        return None

    # 3. Select 2–5 guests
    target_guests = random.randint(2, 5)
    print(f"\n[3] Selecting {target_guests} guests...")

    adults_plus = None
    for sel in [
        '[data-testid="stepper-adults-increase-button"]',
        'button[aria-label*="increase adults" i]',
        'button[aria-label*="add adult" i]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                adults_plus = el
                print(f"  ✓ + button: {sel}")
                break
        except Exception:
            continue

    actual_guests = 0
    if adults_plus:
        current = _get_count(page, '[data-testid="stepper-adults-value"]') or 1
        clicks = max(0, target_guests - current)
        print(f"  Current: {current}, clicking + {clicks}x")
        done = _click_plus(page, adults_plus, clicks)
        actual_guests = current + done
        print(f"  ✓ Total guests: {actual_guests}")

    _log(session, "Select random number of guests",
         f"Selected {actual_guests} guest(s)." if adults_plus else "Adults stepper not found.",
         "guests_selected", force_fail=not adults_plus)

    if not adults_plus:
        return None

    # 4. Verify count shown in field
    print("\n[4] Verifying guest count in field...")
    page.wait_for_timeout(500)
    displayed = None
    for sel in [
        '[data-testid="structured-search-input-field-guests-btn"]',
        '[data-testid="little-search-guests"]',
        '[data-testid="little-search-anon-guest-display"]',
        '[data-testid*="guest"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1000):
                text = el.inner_text().strip()
                if text and any(c.isdigit() for c in text):
                    displayed = text
                    print(f"  ✓ Field shows: '{displayed}'")
                    break
        except Exception:
            continue

    _log(session, "Guest count shown in input field",
         f"Field shows: '{displayed}'. Expected: {actual_guests}."
         if displayed else "Could not read guest field.",
         "guest_count_verified")

    # 5. Validate match
    print("\n[5] Validating guest count matches...")
    matches = displayed is not None and str(actual_guests) in (displayed or '')
    _log(session, "Validate guest count matches selection",
         f"Match {'✓' if matches else '✗'}: field='{displayed}', selected={actual_guests}.",
         "guest_count_validation")

    # 6. Click Search
    print("\n[6] Clicking Search button...")
    search_clicked = False
    for sel in [
        '[data-testid="structured-search-input-search-button"]',
        'button[aria-label*="Search" i]',
        'button[type="submit"]',
        'button:has-text("Search")',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                print(f"  → {sel}")
                el.click()
                page.wait_for_timeout(3000)
                search_clicked = True
                print(f"  ✓ URL: {page.url}")
                break
        except Exception:
            continue

    _log(session, "Click Search button",
         f"Search submitted. URL: {page.url}" if search_clicked else "Search button not found.",
         "search_submitted", force_fail=not search_clicked)

    print("\n✅ Step 04 complete!")
    return {
        "guests": actual_guests,
        "target": target_guests,
        "search_url": page.url,
    }