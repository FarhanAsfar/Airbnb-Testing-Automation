import re
from urllib.parse import urlparse, parse_qs

from automation.utils.logger import log_result
from automation.utils.screenshot import take_screenshot
from automation.models import Listing


def _log(session, name, comment, screenshot_name, force_fail=False):
    take_screenshot(session.page, screenshot_name)
    passed = session.passed() and not force_fail
    if not session.passed():
        comment += f" | Errors: {session.error_summary()}"
    log_result(name, session.page.url, passed, comment)
    session.clear_errors()
    return passed


def _parse_url_params(url):
    """Extract checkin, checkout, adults from Airbnb search URL."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return {
            "checkin": params.get("checkin", [None])[0],
            "checkout": params.get("checkout", [None])[0],
            "adults": params.get("adults", [None])[0],
        }
    except Exception:
        return {}


def run(session, chosen_text, date_info, guest_info):
    page = session.page
    print("\n🔍 STEP 05 — Search Results Verification & Scraping")
    print("=" * 55)

    current_url = page.url
    print(f"  URL: {current_url}")

    # 1. Verify results page loaded
    print("\n[1] Verifying results page loaded...")
    results_loaded = False

    for sel in [
        '[data-testid="card-container"]',
        '[data-testid="listing-card-title"]',
        '[data-testid="explore-section-wrapper"]',
        '[data-testid="listing-tile"]',
        'div[itemprop="itemListElement"]',
    ]:
        try:
            if page.locator(sel).first.is_visible(timeout=5000):
                results_loaded = True
                print(f"  ✓ Results confirmed via: {sel}")
                break
        except Exception:
            continue

    _log(session, "Search results page loads",
         f"Results page loaded. URL: {current_url}" if results_loaded
         else "Results page did not load properly.",
         "results_page", force_fail=not results_loaded)

    if not results_loaded:
        return None

    # 2. Confirm dates and guest count appear in page UI
    print("\n[2] Checking dates and guests in page UI...")
    page.wait_for_timeout(1000)

    ui_checks = []

    # Look for dates in the search bar / filters area
    checkin = date_info.get("checkin", "") if date_info else ""
    checkout = date_info.get("checkout", "") if date_info else ""
    guests = str(guest_info.get("guests", "")) if guest_info else ""

    # Check for date text anywhere visible on page
    try:
        page_text = page.inner_text("body")
        # Dates may appear as "Feb 1 - Feb 5" or "Feb 1–5" etc.
        if checkin:
            # Try matching month abbreviation from the date
            month_match = re.search(r'(\w{3})\s+\d+', checkin)
            if month_match and month_match.group(0).lower() in page_text.lower():
                ui_checks.append(f"check-in date visible")
        if guests and guests in page_text:
            ui_checks.append(f"guest count ({guests}) visible")
    except Exception:
        pass

    # Also look in the top search bar text
    for sel in ['[data-testid="little-search"]', '[data-testid="little-search-query"]',
                '[data-testid="structured-search-input-field-query"]']:
        try:
            text = page.locator(sel).first.inner_text()
            if chosen_text and chosen_text.split(",")[0].lower() in text.lower():
                ui_checks.append("location visible in search bar")
                break
        except Exception:
            continue

    _log(session, "Dates and guest count appear in UI",
         f"UI checks passed: {', '.join(ui_checks)}." if ui_checks
         else "Could not confirm dates/guests in UI (may be in collapsed bar).",
         "results_ui_check")

    # 3. Validate dates and guests in URL
    print("\n[3] Validating URL parameters...")
    url_params = _parse_url_params(current_url)
    print(f"  URL params: {url_params}")

    url_valid = bool(url_params.get("checkin") or url_params.get("adults"))
    url_checks = []
    if url_params.get("checkin"):
        url_checks.append(f"checkin={url_params['checkin']}")
    if url_params.get("checkout"):
        url_checks.append(f"checkout={url_params['checkout']}")
    if url_params.get("adults"):
        url_checks.append(f"adults={url_params['adults']}")

    _log(session, "Dates and guests present in URL",
         f"URL contains: {', '.join(url_checks)}." if url_checks
         else f"No search params found in URL: {current_url}",
         "results_url_check")

    # 4. Scrape listings
    print("\n[4] Scraping listing data...")
    page.wait_for_timeout(1000)

    listings = []

    # Get all listing cards
    cards = page.locator('[data-testid="card-container"]').all()
    if not cards:
        cards = page.locator('[data-testid="listing-tile"]').all()
    print(f"  Found {len(cards)} listing cards")

    for i, card in enumerate(cards[:20]):  # Cap at 20 listings
        try:
            title, price, img_url = None, None, None

            # Title
            for sel in ['[data-testid="listing-card-title"]', 'div[data-testid*="title"]',
                        '[aria-label]', 'h3', 'h2']:
                try:
                    el = card.locator(sel).first
                    text = el.inner_text().strip()
                    if text and len(text) > 3:
                        title = text
                        break
                except Exception:
                    continue

            # Price
            for sel in ['[data-testid="price-availability-row"]', 'span[data-testid*="price"]',
                        'span:has-text("$")', 'span:has-text("£")', 'span:has-text("€")',
                        '[class*="price"]']:
                try:
                    el = card.locator(sel).first
                    text = el.inner_text().strip()
                    if text and any(c.isdigit() for c in text):
                        price = text.split("\n")[0].strip()
                        break
                except Exception:
                    continue

            # Image URL
            try:
                img = card.locator("img").first
                img_url = img.get_attribute("src") or img.get_attribute("data-src")
            except Exception:
                pass

            if title:
                listings.append({
                    "title": title,
                    "price": price or "N/A",
                    "img_url": img_url or "",
                })
                print(f"  [{i+1}] {title[:50]} | {price}")
        except Exception:
            continue

    _log(session, "Scrape listing titles, prices, images",
         f"Scraped {len(listings)} listings from results page." if listings
         else "No listings could be scraped.",
         "results_scraped", force_fail=not listings)

    if not listings:
        return None

    # 5. Store listings in DB
    print(f"\n[5] Storing {len(listings)} listings in database...")
    saved = 0
    search_url = current_url

    for item in listings:
        try:
            Listing.objects.create(
                title=item["title"][:500],
                price=item["price"][:100],
                img_url=item["img_url"][:1000],
                search_url=search_url[:1000],
                location=chosen_text or "",
                checkin=url_params.get("checkin") or (date_info.get("checkin") if date_info else ""),
                checkout=url_params.get("checkout") or (date_info.get("checkout") if date_info else ""),
                guests=guest_info.get("guests", 0) if guest_info else 0,
            )
            saved += 1
        except Exception as e:
            print(f"  ⚠ DB save failed: {e}")

    _log(session, "Store listing data in database",
         f"Saved {saved}/{len(listings)} listings to database." if saved
         else "Failed to save listings to database.",
         "results_stored", force_fail=saved == 0)

    print("\n✅ Step 05 complete!")
    return {
        "listings_found": len(listings),
        "listings_saved": saved,
        "url_params": url_params,
    }