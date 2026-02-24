import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.core.management.base import BaseCommand
from automation.utils.browser import BrowserSession
from automation.steps import step01_landing, step03_datepicker, step04_guests, step05_results


class Command(BaseCommand):
    help = "Run Airbnb automation test suite"

    def add_arguments(self, parser):
        parser.add_argument('--headless', action='store_true', default=False)
        parser.add_argument('--step', type=int, default=0)

    def handle(self, *args, **options):
        headless = options['headless']
        step = options['step']

        self.stdout.write(self.style.SUCCESS("🤖 Starting Airbnb Automation"))
        self.stdout.write(f"   Mode: {'Headless' if headless else 'Headed (visible browser)'}")

        with BrowserSession(headless=headless) as session:
            try:
                city, chosen_text, suggestion_items = None, None, []
                date_info = None
                guest_info = None

                if step == 0 or step == 1:
                    city, chosen_text, suggestion_items = step01_landing.run(session)
                    self.stdout.write(self.style.SUCCESS(
                        f"\n   City: {city} | Selected: {chosen_text}"
                    ))

                if step == 0 or step == 3:
                    if not chosen_text:
                        self.stdout.write(self.style.ERROR("Step 3 requires step 1."))
                    else:
                        date_info = step03_datepicker.run(session, chosen_text)
                        if date_info:
                            self.stdout.write(self.style.SUCCESS(
                                f"\n   Dates: {date_info['checkin']} -> {date_info['checkout']}"
                            ))

                if step == 0 or step == 4:
                    if not chosen_text:
                        self.stdout.write(self.style.ERROR("Step 4 requires step 1."))
                    else:
                        guest_info = step04_guests.run(session, chosen_text, date_info)
                        if guest_info:
                            self.stdout.write(self.style.SUCCESS(
                                f"\n   Guests: {guest_info['guests']}"
                            ))

                if step == 0 or step == 5:
                    if not chosen_text:
                        self.stdout.write(self.style.ERROR("Step 5 requires step 1."))
                    else:
                        results_info = step05_results.run(session, chosen_text, date_info, guest_info)
                        if results_info:
                            self.stdout.write(self.style.SUCCESS(
                                f"\n   Listings found: {results_info['listings_found']}"
                                f" | Saved: {results_info['listings_saved']}"
                            ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Automation crashed: {e}"))
                raise

        self.stdout.write(self.style.SUCCESS("\n🏁 Automation complete. Check DB for results."))