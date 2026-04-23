"""
save_session.py - Saves session by logging in manually.

Run:
    cd ui-tests
    python save_session.py
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import tempfile

AUTH_STATE_PATH = Path(__file__).parent / ".auth_state.json"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            ignore_default_args=["--enable-automation"],
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        print("Opening Rhombus AI...")
        print("Please log in manually in the browser window.")
        print("Once you see the dashboard, come back here and press Enter.")

        page.goto("https://rhombusai.com")

        input("\nPress Enter AFTER you are logged in and see the dashboard...")

        context.storage_state(path=str(AUTH_STATE_PATH))
        print(f"\nSession saved to {AUTH_STATE_PATH}")
        print("You can now run: pytest tests/ -v --headed")

        browser.close()

if __name__ == "__main__":
    main()