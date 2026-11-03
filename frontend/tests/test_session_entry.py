"""Browser regression: run against npm run dev with Python Playwright installed.

ASTRA_ENTRY_URL=http://127.0.0.1:8771 python -m unittest discover -s frontend/tests -p test_session_entry.py
Set PLAYWRIGHT_CHROME_PATH to use an installed Chrome instead of Playwright Chromium.
All account API responses are local fixtures; no WhatsApp messages are sent.
"""

import json
import os
import unittest

# Manual check: the release gate has neither a dev server nor Playwright.
if not os.getenv("ASTRA_ENTRY_URL"):
    raise unittest.SkipTest("set ASTRA_ENTRY_URL to run browser entry tests")

from playwright.sync_api import sync_playwright, expect


class SessionEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        options = {"headless": True}
        if os.getenv("PLAYWRIGHT_CHROME_PATH"):
            options["executable_path"] = os.environ["PLAYWRIGHT_CHROME_PATH"]
        cls.browser = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 1000})
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.page.set_default_timeout(15000)
        self.starts = []
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.context.route("**/api/me**", self.account_api)

    def account_api(self, route):
        path = route.request.url.split("/api/me", 1)[1].split("?", 1)[0]
        if path == "/whatsapp-login/start":
            self.starts.append(route.request.url)
            body = {"code": "ABCDEFGH", "poll_token": "local-test", "expires_in": 600,
                    "whatsapp_url": "https://wa.me/910000000000?text=local-test"}
        elif path == "/whatsapp-login/poll":
            body = {"status": "pending"}
        elif path == "/onboarding":
            body = {"name": "Ravi", "interests": [], "step": "complete",
                    "completed": True, "completed_at": "2026-11-03T08:00:00Z"}
        elif path == "":
            self.assertEqual(route.request.headers.get("authorization"), "Bearer wa.local-test.signature")
            body = {"phone_number": "919999999999", "name": "Ravi", "member_since": None,
                    "plan": {"is_premium": False, "name": "Astra Free", "expires_at": None, "price_usd": 0},
                    "usage": {"used_today": 5, "daily_limit": 5}, "whatsapp_number": "910000000000",
                    "connections": [], "available_plans": []}
        elif path == "/session":
            self.assertEqual(route.request.headers.get("authorization"), "Bearer wa.local-test.signature")
            body = {"ok": True}
        else:
            raise AssertionError(f"Unexpected API request: {path}")
        route.fulfill(json=body)

    def open_home(self, signed_in):
        if signed_in:
            saved = json.dumps({"token": "wa.local-test.signature", "phoneNumber": "+919999999999"})
            self.context.add_init_script(f"localStorage.setItem('astra:wa_session', {json.dumps(saved)});")
        self.page.goto(os.getenv("ASTRA_ENTRY_URL", "http://127.0.0.1:8771"))
        self.page.wait_for_load_state("networkidle")
        self.page.locator("#whatsapp-qr img").wait_for(state="attached")

    def test_returning_user_qr_entry_opens_account_without_new_login(self):
        self.open_home(signed_in=True)
        self.assertEqual(self.starts, [], "Landing page created a new login for a saved session")
        expect(self.page.locator("#whatsapp-qr")).to_have_attribute("href", "/app")
        self.page.get_by_text("Scan to get started", exact=False).click()
        expect(self.page.get_by_role("heading", name="Hey Ravi 👋")).to_be_visible()
        self.page.reload()
        expect(self.page.get_by_role("heading", name="Hey Ravi 👋")).to_be_visible()
        self.assertEqual(self.starts, [])
        self.assertEqual(self.errors, [])

    def test_mobile_login_entry_restores_saved_account(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.open_home(signed_in=True)
        self.page.get_by_role("link", name="Log in", exact=True).click()
        expect(self.page.get_by_role("heading", name="Hey Ravi 👋")).to_be_visible()
        self.assertEqual(self.starts, [])
        self.assertEqual(self.errors, [])

    def test_new_user_starts_login_only_after_entering_app(self):
        self.open_home(signed_in=False)
        self.assertEqual(self.starts, [], "A public page visit should not create a login challenge")
        self.page.get_by_text("Scan to get started", exact=False).click()
        self.page.wait_for_url("**/app")
        expect(self.page.get_by_role("link", name="Continue with WhatsApp", exact=True)).to_be_visible()
        self.assertGreaterEqual(len(self.starts), 1)
        self.assertEqual(self.errors, [])


if __name__ == "__main__":
    unittest.main()
