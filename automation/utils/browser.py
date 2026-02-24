from playwright.sync_api import sync_playwright, Browser, Page


# Third-party tracking/ad/telemetry URLs — irrelevant to our tests
IGNORED_URL_PATTERNS = (
    'doubleclick.net', 'google-analytics.com', 'googletagmanager.com',
    'facebook.net', 'facebook.com', '/sgtm/', '/jitney/', '/tracking/',
    'airdog', 'ad.doubleclick', 'analytics', 'snap.licdn',
)

# Patterns to ignore in console error messages (not URLs)
IGNORED_CONSOLE_PATTERNS = (
    'AbortError', 'signal is aborted', 'ResizeObserver',
    'Non-Error promise rejection', 'Load failed',
)


def _is_ignored_url(url: str) -> bool:
    return any(pattern in url for pattern in IGNORED_URL_PATTERNS)


def _is_ignored_console(msg: str) -> bool:
    return any(pattern in msg for pattern in IGNORED_CONSOLE_PATTERNS)


class BrowserSession:
    """Manages browser lifecycle and tracks console errors / network failures."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Browser = None
        self.page: Page = None
        self.console_errors: list = []
        self.network_errors: list = []

    def start(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage'],
        )
        context = self._browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        )
        context.clear_cookies()
        self.page = context.new_page()
        self._attach_listeners()
        return self

    def _attach_listeners(self):
        self.page.on('console', self._on_console)
        self.page.on('response', self._on_response)

    def _on_console(self, msg):
        if msg.type == 'error' and not _is_ignored_url(msg.text) and not _is_ignored_console(msg.text):
            self.console_errors.append(msg.text)

    def _on_response(self, response):
        if response.status >= 400 and not _is_ignored_url(response.url):
            self.network_errors.append(f"{response.status} {response.url}")

    def has_errors(self) -> bool:
        return bool(self.console_errors or self.network_errors)

    def clear_errors(self):
        self.console_errors.clear()
        self.network_errors.clear()

    def error_summary(self) -> str:
        parts = []
        if self.console_errors:
            parts.append(f"Console errors: {'; '.join(self.console_errors[:3])}")
        if self.network_errors:
            parts.append(f"Network errors: {'; '.join(self.network_errors[:3])}")
        return ' | '.join(parts) if parts else ''

    def passed(self) -> bool:
        return not self.has_errors()

    def stop(self):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.stop()