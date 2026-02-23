import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.core.management.base import BaseCommand

from automation.utils.browser import BrowserSession
from automation.steps import step01_landing


class Command(BaseCommand):
    help = "Run Airbnb automation test suite"

    def add_arguments(self, parser):
        parser.add_argument(
            '--headless',
            action='store_true',
            default=False,
            help='Run browser in headless mode (no UI)',
        )
        parser.add_argument(
            '--step',
            type=int,
            default=0,
            help='Run a specific step only (0 = all steps)',
        )

    def handle(self, *args, **options):
        headless = options['headless']
        step = options['step']

        self.stdout.write(self.style.SUCCESS("🤖 Starting Airbnb Automation"))
        self.stdout.write(f"   Mode: {'Headless' if headless else 'Headed (visible browser)'}")

        with BrowserSession(headless=headless) as session:
            try:
                if step == 0 or step == 1:
                    city = step01_landing.run(session)
                    self.stdout.write(self.style.SUCCESS(f"\n   Selected city: {city}"))

                # Future steps will be added here:
                # if step == 0 or step == 2:
                #     step02_search.run(session, city)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Automation crashed: {e}"))
                raise

        self.stdout.write(self.style.SUCCESS("\n🏁 Automation complete. Check DB for results."))