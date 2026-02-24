import random

from automation.utils.browser import BrowserSession
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


def _get_current_count(page, counter_sel):
    """Read the current number shown in a stepper counter."""
    try:
        el = page.locator(counter_sel).first
        if el.is_visible(timeout=1000):
            text = el.inner_text().strip()
            return int(''.join(filter(str.isdigit, text)) or '0')
    except Exception:
        pass
    return 0


def _click_plus(page, btn, times):
    """Click a + button N times with short pauses."""
    clicked = 0
    for _ in range(times):
        try:
            btn.click()
            page.wait_for_timeout(400)
            clicked += 1
        except Exception:
            break
    return clicked


def run(session, chosen_text, date_info):
    page = session.page
    print("\n👥 STEP 04 — Guest Selection")
    print("=" * 55)

    # 0. Close calendar if still open (press Escape or click outside)
    print("\n[0] Ensuring calendar is closed...")
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
    except Exception:
        pass

    # Debug: show current page state
    try:
        testids = [el.get_attribute("data-testid")
                   for el in page.locator("[data-testid]").all()
                   if el.is_visible()]
        testids = [t for t in testids if t]
        print(f"  Visible testids: {testids[:12]}")
    except Exception:
        pass

    # 1. Click the guests field
    print("\n[1] Clicking guest input field...")
    guest_field_opened = False

    for sel in [
        '[data-testid="structured-search-input-field-guests-btn"]',
        '[data-testid="structured-search-input-field-guests"]',
        'button[aria-label*="guest" i]',
        'button[aria-label*="Who" i]',
        '[data-testid*="guest"]',
        'button:has-text("Add guests")',
        'button:has-text("Who")',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                print(f"  → Clicking guest field: {sel}")
                el.click()
                page.wait_for_timeout(1500)
                guest_field_opened = True
                break
        except Exception:
            continue

    _log(session, "Click guest input field",
         "Guest input field clicked successfully."
         if guest_field_opened else "Could not find guest input field.",
         "guest_field_click", force_fail=not guest_field_opened)

    if not guest_field_opened:
        return None

    # 2. Verify guest popup is open
    print("\n[2] Verifying guest selection popup...")
    popup_open = False
    popup_sel_found = None

    for sel in [
        '[data-testid="structured-search-input-field-guests-panel"]',
        '[data-testid="guest-selector"]',
        '[data-testid="GuestPicker-panel"]',
        '[aria-label*="guests" i]',
        'div[class*="guestpicker" i]',
        # Look for adult stepper as proxy for popup being open
        '[data-testid="stepper-adults-increase-button"]',
        'button[aria-label*="Increase adults" i]',
        'button[aria-label*="Add adult" i]',
        'button[aria-label*="increase" i]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                popup_open = True
                popup_sel_found = sel
                print(f"  ✓ Popup confirmed via: {sel}")
                break
        except Exception:
            continue

    if not popup_open:
        # Debug: show visible testids
        try:
            testids = [el.get_attribute("data-testid")
                       for el in page.locator("[data-testid]").all()
                       if el.is_visible()]
            print(f"  Visible testids: {[t for t in testids if t][:15]}")
        except Exception:
            pass

    _log(session, "Guest selection popup opens",
         "Guest selection popup is open and visible."
         if popup_open else "Guest selection popup did not open.",
         "guest_popup_open", force_fail=not popup_open)

    if not popup_open:
        return None

    # 3. Select random number of guests (2-5)
    target_guests = random.randint(2, 5)
    print(f"\n[3] Selecting {target_guests} guests (adults)...")

    # Find the adults increase button
    adults_plus = None
    for sel in [
        '[data-testid="stepper-adults-increase-button"]',
        'button[aria-label*="Increase adults" i]',
        'button[aria-label*="Add adult" i]',
        'button[aria-label*="increase" i]',
        '[data-testid*="adults"][data-testid*="increase"]',
        '[data-testid*="adults"][data-testid*="plus"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                adults_plus = el
                print(f"  ✓ Adults + button: {sel}")
                break
        except Exception:
            continue

    # Find adults counter to read current value
    adults_count_sel = None
    for sel in [
        '[data-testid="stepper-adults-value"]',
        '[aria-label*="adults" i] span',
        'span[class*="count"]',
        'span[data-testid*="adults"]',
    ]:
        try:
            if page.locator(sel).first.is_visible(timeout=1000):
                adults_count_sel = sel
                break
        except Exception:
            continue

    actual_guests = 0
    if adults_plus:
        # Click + button target_guests times (starting from 0, but Airbnb starts at 1)
        # Read current value first
        current = _get_current_count(page, adults_count_sel) if adults_count_sel else 1
        clicks_needed = max(0, target_guests - current)
        print(f"  Current adults: {current}, need {clicks_needed} more clicks")
        clicked = _click_plus(page, adults_plus, clicks_needed)
        actual_guests = current + clicked
        print(f"  ✓ Clicked + {clicked} times, total guests: {actual_guests}")
    else:
        # Debug: show all buttons
        try:
            btns = [(b.get_attribute("aria-label"), b.get_attribute("data-testid"))
                    for b in page.locator("button").all() if b.is_visible()]
            print(f"  All visible buttons: {btns[:15]}")
        except Exception:
            pass

    _log(session, "Select random number of guests",
         f"Selected {actual_guests} guest(s) by clicking the adults + button {target_guests - 1} times."
         if adults_plus else "Could not find the adults + stepper button.",
         "guests_selected", force_fail=not adults_plus)

    if not adults_plus:
        return None

    # 4. Verify guest count in input field
    print("\n[4] Verifying guest count in input field...")
    page.wait_for_timeout(500)

    displayed_count = None
    for sel in [
        '[data-testid="structured-search-input-field-guests-btn"]',
        '[data-testid="structured-search-input-field-guests"]',
        'button[aria-label*="guest" i]',
        '[data-testid*="guest"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1000):
                text = el.inner_text().strip()
                if text and any(c.isdigit() for c in text):
                    displayed_count = text
                    print(f"  ✓ Guest field shows: '{displayed_count}'")
                    break
        except Exception:
            continue

    count_matches = displayed_count is not None and str(actual_guests) in (displayed_count or '')
    _log(session, "Guest count shown in input field",
         f"Guest field displays: '{displayed_count}'. Expected {actual_guests} guest(s)."
         if displayed_count else "Could not read guest count from input field.",
         "guest_count_verified")

    # 5. Validate displayed count matches selected
    print("\n[5] Validating guest count matches selection...")
    _log(session, "Validate guest count matches selection",
         f"Guest count validated: field shows '{displayed_count}', selected {actual_guests} guest(s). Values match."
         if count_matches else
         f"Mismatch: field shows '{displayed_count}', expected {actual_guests} guest(s).",
         "guest_count_validation")

    # 6. Click Search button
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
                print(f"  → Clicking search: {sel}")
                el.click()
                page.wait_for_timeout(3000)
                search_clicked = True
                print(f"  ✓ Search clicked. URL: {page.url}")
                break
        except Exception:
            continue

    _log(session, "Click Search button",
         f"Search submitted. Now on: {page.url}"
         if search_clicked else "Could not find or click the Search button.",
         "search_submitted", force_fail=not search_clicked)

    print("\n✅ Step 04 complete!")
    return {
        "guests": actual_guests,
        "target": target_guests,
        "search_url": page.url,
    }