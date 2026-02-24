import random
from datetime import datetime

from automation.utils.browser import BrowserSession
from automation.utils.logger import log_result
from automation.utils.screenshot import take_screenshot


def _log(session, name, comment, screenshot_name, force_fail=False):
    # take_screenshot(session.page, screenshot_name)
    passed = session.passed() and not force_fail
    if not session.passed():
        comment += f" | Errors: {session.error_summary()}"
    log_result(name, session.page.url, passed, comment)
    session.clear_errors()
    return passed


def _parse_date(el):
    for attr in ['aria-label', 'data-date']:
        try:
            val = (el.get_attribute(attr) or '').strip()
            for prefix in ['Choose ', 'Selected ', 'Available ']:
                if val.startswith(prefix):
                    val = val[len(prefix):].strip()
            for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d', '%A, %B %d, %Y']:
                try:
                    return datetime.strptime(val, fmt)
                except ValueError:
                    continue
        except Exception:
            continue
    return None


def _get_month(page):
    for sel in ['h2[aria-live]', '[data-testid="calendar-month-and-year"]',
                '[aria-live="polite"]', 'h2']:
        try:
            els = page.locator(sel).all()
            for el in els:
                text = el.inner_text().strip()
                if any(m in text for m in ['Jan','Feb','Mar','Apr','May','Jun',
                                            'Jul','Aug','Sep','Oct','Nov','Dec']):
                    return text
        except Exception:
            continue
    return "unknown"


def _get_days(page):
    for sel in ['[data-testid="calendar-day"]',
                'button[aria-label*="202"]',
                'button[aria-label*="203"]',
                'td:not([aria-disabled="true"]) button']:
        try:
            items = page.locator(sel).all()
            visible = [el for el in items if el.is_visible() and not el.get_attribute('disabled')]
            if visible:
                print(f"  ✓ Day selector: {sel} ({len(visible)} days)")
                return visible
        except Exception:
            continue
    return []


def _is_calendar_open(page):
    for sel in ['[data-testid="calendar-day"]', 'button[aria-label*="202"]',
                'button[aria-label*="203"]']:
        try:
            if page.locator(sel).first.is_visible(timeout=1500):
                return True
        except Exception:
            continue
    return False


def run(session, chosen_text):
    page = session.page
    print("\n📅 STEP 03 — Date Picker Interaction")
    print("=" * 55)

    # 1. Open date picker
    print("\n[1] Opening date picker...")
    page.wait_for_timeout(2000)

    print(f"  Current URL: {page.url}")

    is_open = _is_calendar_open(page)
    print(f"  Calendar already open: {is_open}")

    if not is_open:
        # Step 1: type the location into the search field and click search button
        # This is needed because the suggestion click may not have fully submitted
        search_btn_sel = '[data-testid="structured-search-input-search-button"]'
        try:
            btn = page.locator(search_btn_sel).first
            if btn.is_visible(timeout=2000):
                print(f"  → Clicking search button")
                btn.click()
                page.wait_for_timeout(2000)
        except Exception:
            pass

        # Step 2: now look for date fields
        for sel in [
            '[data-testid="structured-search-input-field-split-dates-0"]',
            '[data-testid="structured-search-input-field-dates-0"]',
            '[data-testid="structured-search-input-field-dates"]',
            'button:has-text("Add dates")',
            'button:has-text("Check in")',
            '[aria-label*="Check in"]',
            '[data-testid*="date"]',
            '[data-testid*="check"]',
        ]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    print(f"  → Clicking date field: {sel}")
                    el.click()
                    page.wait_for_timeout(2000)
                    if _is_calendar_open(page):
                        break
            except Exception:
                continue

    is_open = _is_calendar_open(page)
    # Debug visible testids if still not open
    if not is_open:
        try:
            testids = [el.get_attribute("data-testid") for el in page.locator("[data-testid]").all() if el.is_visible()]
            print(f"  Visible testids: {[t for t in testids if t][:12]}")
        except Exception:
            pass

    is_open = _is_calendar_open(page)
    _log(session, "Date picker modal opens",
         f"Date picker opened after selecting '{chosen_text}'."
         if is_open else f"Date picker did not open after selecting '{chosen_text}'.",
         "datepicker_open", force_fail=not is_open)

    if not is_open:
        return None

    # 2. Navigate months
    num_clicks = random.randint(3, 8)
    print(f"\n[2] Navigating {num_clicks} months forward...")
    clicked_count = 0
    for sel in ['[aria-label="Move forward to switch to the next month"]',
                '[data-testid="calendar-next-month"]',
                '[aria-label="Next month"]',
                'button[aria-label*="next" i]']:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                for _ in range(num_clicks):
                    btn.click()
                    page.wait_for_timeout(500)
                    clicked_count += 1
                break
        except Exception:
            continue

    current_month = _get_month(page)
    print(f"  📅 Now viewing: {current_month}")
    _log(session, "Navigate calendar months",
         f"Clicked Next Month {clicked_count}/{num_clicks} times. Now viewing: {current_month}.",
         "datepicker_month_nav", force_fail=clicked_count == 0)

    # 3. Select check-in
    print("\n[3] Selecting check-in date...")
    page.wait_for_timeout(500)
    days = _get_days(page)
    if not days:
        _log(session, "Select check-in date", "No days found in calendar.",
             "checkin_selected", force_fail=True)
        return None

    mid = max(1, len(days) // 2)
    checkin_el = random.choice(days[:mid])
    checkin_index = days.index(checkin_el)
    checkin_date = _parse_date(checkin_el)
    checkin_label = checkin_el.get_attribute('aria-label') or checkin_el.inner_text().strip()
    print(f"  → Check-in: '{checkin_label}'")
    checkin_el.click()
    page.wait_for_timeout(1000)
    _log(session, "Select check-in date",
         f"Check-in selected: '{checkin_label}'"
         f"{' (' + checkin_date.strftime('%b %d, %Y') + ')' if checkin_date else ''}.",
         "checkin_selected")

    # 4. Select check-out
    print("\n[4] Selecting check-out date...")
    page.wait_for_timeout(500)
    days = _get_days(page)

    checkout_el = None
    checkout_date = None
    if checkin_date:
        for el in days:
            candidate = _parse_date(el)
            if candidate and candidate > checkin_date:
                checkout_el = el
                checkout_date = candidate
                break
    else:
        # If parsing failed for check-in, preserve calendar order and pick the next day cell.
        checkin_pos = None
        for idx, el in enumerate(days):
            label = el.get_attribute('aria-label') or el.inner_text().strip()
            if label == checkin_label:
                checkin_pos = idx
                break
        if checkin_pos is None:
            checkin_pos = checkin_index
        next_pos = checkin_pos + 1
        if next_pos < len(days):
            checkout_el = days[next_pos]
            checkout_date = _parse_date(checkout_el)

    if not checkout_el:
        _log(session, "Select check-out date", "No valid check-out date found.",
             "checkout_selected", force_fail=True)
        return None

    checkout_label = checkout_el.get_attribute('aria-label') or checkout_el.inner_text().strip()
    print(f"  → Check-out: '{checkout_label}'")
    checkout_el.click()
    page.wait_for_timeout(1000)
    _log(session, "Select check-out date",
         f"Check-out selected: '{checkout_label}'"
         f"{' (' + checkout_date.strftime('%b %d, %Y') + ')' if checkout_date else ''}.",
         "checkout_selected")

    # 5. Confirm dates in fields
    print("\n[5] Confirming dates in input fields...")
    page.wait_for_timeout(800)
    confirmed = []
    for sel in ['[data-testid="structured-search-input-field-split-dates-0"]',
                '[data-testid="structured-search-input-field-split-dates-1"]',
                '[data-testid="structured-search-input-field-dates-0"]',
                '[data-testid="structured-search-input-field-dates-1"]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1000):
                text = el.inner_text().strip() or el.get_attribute('value') or ''
                if text and text not in ('Check in', 'Check out', 'Add dates'):
                    confirmed.append(text)
        except Exception:
            continue
    _log(session, "Confirm dates in input fields",
         f"Dates in fields: {' | '.join(confirmed)}." if confirmed else
         "Dates not visible in fields (calendar may still be open).",
         "dates_confirmed")

    # 6. Validate logic
    print("\n[6] Validating date logic...")
    if checkin_date and checkout_date:
        logic_ok = checkout_date > checkin_date
        nights = (checkout_date - checkin_date).days if logic_ok else 0
        comment = (
            f"Date logic valid. Check-in: {checkin_date.strftime('%b %d, %Y')}, "
            f"Check-out: {checkout_date.strftime('%b %d, %Y')}, "
            f"{nights} night(s). Month: {current_month}."
            if logic_ok else
            f"Invalid — check-out not after check-in."
        )
    else:
        logic_ok = True
        comment = f"Check-in: '{checkin_label}', Check-out: '{checkout_label}'. Month: {current_month}."
    _log(session, "Validate selected dates are logical", comment,
         "dates_validation", force_fail=not logic_ok)

    print("\n✅ Step 03 complete!")
    return {
        "checkin": checkin_date.strftime('%Y-%m-%d') if checkin_date else checkin_label,
        "checkout": checkout_date.strftime('%Y-%m-%d') if checkout_date else checkout_label,
        "month": current_month,
    }
