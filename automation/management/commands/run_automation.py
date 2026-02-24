import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.core.management.base import BaseCommand
from automation.utils.browser import BrowserSession
from automation.steps import step01_landing, step03_datepicker


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
                selected_suggestion = None
                date_info = None

                if step == 0 or step == 1:
                    city, chosen_text, suggestion_items = step01_landing.run(session)
                    self.stdout.write(self.style.SUCCESS(
                        f"\n   City: {city} | Selected: {chosen_text}"
                    ))

                # if step == 0 or step == 2:
                #     if not city:
                #         self.stdout.write(self.style.ERROR("Step 2 requires Step 1."))
                #     else:
                #         selected_suggestion = step02_suggestions.run(
                #             session, city, suggestion_items, chosen_text
                #         )

                if step == 0 or step == 3:
                    suggestion = chosen_text
                    if not suggestion:
                        self.stdout.write(self.style.ERROR("Step 3 requires a selected suggestion."))
                    else:
                        date_info = step03_datepicker.run(session, suggestion)
                        if date_info and isinstance(date_info, dict):
                            self.stdout.write(self.style.SUCCESS(
                                f"\n   Dates: {date_info['checkin']} → {date_info['checkout']}"
                            ))
                
                # if step == 0 or step == 4:
                #     suggestion = chosen_text 
                #     if not suggestion:
                #         self.stdout.write(self.style.ERROR("Step 4 requires a selected suggestion."))
                #     else:
                #         guest_info = step04_guests.run(session, suggestion, date_info)
                #         if guest_info and isinstance(guest_info, dict):
                #             self.stdout.write(self.style.SUCCESS(f"\n   Guests: {guest_info['guests']}"))


            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Automation crashed: {e}"))
                raise

        self.stdout.write(self.style.SUCCESS("\n🏁 Automation complete. Check DB for results."))