"""
conftest.py – shared fixtures for Rhombus AI API tests.
"""

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

BASE_URL = os.getenv("RHOMBUS_BASE_URL", "https://rhombusai.com").rstrip("/")
EMAIL    = os.getenv("RHOMBUS_EMAIL", "")
PASSWORD = os.getenv("RHOMBUS_PASSWORD", "")

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CSV_PATH     = FIXTURES_DIR / "messy_data.csv"

AUTH_ENDPOINTS = [
    "/api/auth/login",
    "/api/auth/signin",
    "/api/login",
    "/auth/login",
]


def _build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    })
    return s


def _login(session: requests.Session) -> requests.Session:
    if not EMAIL or not PASSWORD:
        pytest.skip("Set RHOMBUS_EMAIL and RHOMBUS_PASSWORD in .env")

    payload = {"email": EMAIL, "password": PASSWORD}

    for path in AUTH_ENDPOINTS:
        try:
            resp = session.post(
                f"{BASE_URL}{path}",
                json=payload,
                timeout=15
            )
            if resp.status_code in (200, 201):
                try:
                    data = resp.json()
                    token = (
                        data.get("token")
                        or data.get("access_token")
                        or data.get("idToken")
                    )
                    if token:
                        session.headers.update(
                            {"Authorization": f"Bearer {token}"}
                        )
                except Exception:
                    pass
                return session
        except requests.exceptions.ConnectionError:
            continue

    return session


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def anon_client() -> requests.Session:
    """Unauthenticated session for negative tests."""
    return _build_session()


@pytest.fixture(scope="session")
def session_client() -> requests.Session:
    """Authenticated session logged in once per test run."""
    s = _build_session()
    return _login(s)


@pytest.fixture(scope="session")
def csv_file() -> Path:
    assert CSV_PATH.exists(), f"CSV fixture not found at {CSV_PATH}"
    return CSV_PATH