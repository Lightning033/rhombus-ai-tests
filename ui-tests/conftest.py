"""
conftest.py - shared Playwright fixtures for Rhombus AI UI tests.
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

BASE_URL        = os.getenv("RHOMBUS_BASE_URL", "https://rhombusai.com").rstrip("/")
AUTH_STATE_PATH = Path(__file__).parent / ".auth_state.json"
CSV_PATH        = Path(__file__).parent / "fixtures" / "messy_data.csv"


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def csv_path() -> Path:
    assert CSV_PATH.exists(), f"CSV fixture missing at {CSV_PATH}"
    return CSV_PATH


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Launch real Chrome to avoid bot detection."""
    return {
        "headless": False,
        "executable_path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
        "ignore_default_args": ["--enable-automation"],
    }


@pytest.fixture(scope="session")
def auth_state():
    """Use the saved session from save_session.py."""
    if not AUTH_STATE_PATH.exists():
        pytest.skip(
            "No saved session found. Run: python save_session.py first."
        )
    return AUTH_STATE_PATH


@pytest.fixture
def logged_in_page(browser_type, browser_type_launch_args, auth_state):
    """Fresh page using real Chrome with authenticated session."""
    browser = browser_type.launch(**browser_type_launch_args)
    context = browser.new_context(
        storage_state=str(auth_state),
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    page = context.new_page()
    yield page
    context.close()
    browser.close()