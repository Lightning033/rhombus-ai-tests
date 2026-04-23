"""
test_api.py – Black-box API tests for Rhombus AI

Coverage:
  1. Authentication & session behaviour
  2. Dataset upload
  3. Pipeline / job execution status
  4. Download endpoints
  5. Error handling for invalid input

Run:
    cd api-tests
    pytest -v
"""

import io
import os
import pytest
import requests


EMAIL    = os.getenv("RHOMBUS_EMAIL", "")
PASSWORD = os.getenv("RHOMBUS_PASSWORD", "")

AUTH_ENDPOINTS = [
    "/api/auth/login",
    "/api/auth/signin",
    "/api/login",
    "/auth/login",
]

UPLOAD_ENDPOINTS = [
    "/api/datasets/upload",
    "/api/files/upload",
    "/api/upload",
    "/api/projects/upload",
]

PIPELINE_ENDPOINTS = [
    "/api/pipelines",
    "/api/jobs",
    "/api/pipeline",
    "/api/runs",
]

DOWNLOAD_ENDPOINTS = [
    "/api/datasets/download",
    "/api/files/download",
    "/api/download",
    "/api/export",
]


# ── Helper ────────────────────────────────────────────────────────────────────

def probe(session, base_url, paths, method="GET", **kwargs):
    """Try each path and return the first non-404 response."""
    fn = getattr(session, method.lower())
    for path in paths:
        try:
            resp = fn(f"{base_url}{path}", timeout=15, **kwargs)
            if resp.status_code != 404:
                return resp
        except requests.exceptions.ConnectionError:
            continue
    return None


# ── 1. Authentication ─────────────────────────────────────────────────────────

class TestAuthentication:

    def test_valid_login_returns_200(self, anon_client, base_url):
        """POSITIVE: Valid credentials should return 200."""
        if not EMAIL or not PASSWORD:
            pytest.skip("No credentials in .env")

        resp = probe(
            anon_client, base_url, AUTH_ENDPOINTS,
            method="POST",
            json={"email": EMAIL, "password": PASSWORD}
        )
        assert resp is not None, "No auth endpoint responded"
        assert resp.status_code in (200, 201), (
            f"Expected 200/201, got {resp.status_code}. Body: {resp.text[:300]}"
        )

    def test_wrong_password_rejected(self, anon_client, base_url):
        """NEGATIVE: Wrong password must return 4xx."""
        resp = probe(
            anon_client, base_url, AUTH_ENDPOINTS,
            method="POST",
            json={"email": "nobody@nowhere.invalid", "password": "wrongpass123"}
        )
        assert resp is not None, "No auth endpoint responded"
        assert 400 <= resp.status_code < 500, (
            f"Expected 4xx for wrong password, got {resp.status_code}"
        )

    def test_missing_password_returns_4xx(self, anon_client, base_url):
        """NEGATIVE: Missing password field must return 4xx not 500."""
        resp = probe(
            anon_client, base_url, AUTH_ENDPOINTS,
            method="POST",
            json={"email": EMAIL or "test@test.com"}
        )
        assert resp is not None, "No auth endpoint responded"
        assert resp.status_code != 500, (
            "Server returned 500 on missing password — this is a bug"
        )
        assert resp.status_code >= 400, (
            f"Expected 4xx, got {resp.status_code}"
        )

    def test_missing_email_returns_4xx(self, anon_client, base_url):
        """NEGATIVE: Missing email field must return 4xx not 500."""
        resp = probe(
            anon_client, base_url, AUTH_ENDPOINTS,
            method="POST",
            json={"password": "somepassword"}
        )
        assert resp is not None, "No auth endpoint responded"
        assert resp.status_code != 500, (
            "Server returned 500 on missing email — this is a bug"
        )
        assert resp.status_code >= 400, (
            f"Expected 4xx, got {resp.status_code}"
        )

    def test_protected_endpoint_blocks_anon(self, anon_client, base_url):
        """NEGATIVE: Unauthenticated request to protected route must return 401/403."""
        resp = probe(anon_client, base_url, PIPELINE_ENDPOINTS, method="GET")

        if resp is None:
            pytest.skip("No pipeline endpoint responded")

        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}"
        )


# ── 2. Dataset Upload ─────────────────────────────────────────────────────────

class TestDatasetUpload:

    def test_authenticated_csv_upload(self, session_client, base_url, csv_file):
        """POSITIVE: Authenticated CSV upload should return 200/201/202."""
        with open(csv_file, "rb") as f:
            resp = probe(
                session_client, base_url, UPLOAD_ENDPOINTS,
                method="POST",
                files={"file": (csv_file.name, f, "text/csv")}
            )

        if resp is None:
            pytest.skip("No upload endpoint responded")

        assert resp.status_code in (200, 201, 202), (
            f"Expected 200/201/202, got {resp.status_code}. Body: {resp.text[:300]}"
        )

    def test_unauthenticated_upload_rejected(self, anon_client, base_url, csv_file):
        """NEGATIVE: Upload without auth must return 401/403."""
        with open(csv_file, "rb") as f:
            resp = probe(
                anon_client, base_url, UPLOAD_ENDPOINTS,
                method="POST",
                files={"file": (csv_file.name, f, "text/csv")}
            )

        if resp is None:
            pytest.skip("No upload endpoint responded")

        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}"
        )

    def test_unsupported_file_type_rejected(self, session_client, base_url):
        """NEGATIVE: Uploading an .exe must be rejected with 4xx."""
        fake_exe = io.BytesIO(b"MZ\x90\x00" + b"\x00" * 100)
        resp = probe(
            session_client, base_url, UPLOAD_ENDPOINTS,
            method="POST",
            files={"file": ("malware.exe", fake_exe, "application/octet-stream")}
        )

        if resp is None:
            pytest.skip("No upload endpoint responded")

        assert 400 <= resp.status_code < 500, (
            f"Expected 4xx for unsupported file, got {resp.status_code}"
        )

    def test_empty_file_rejected(self, session_client, base_url):
        """NEGATIVE: Empty CSV must not cause a 500."""
        resp = probe(
            session_client, base_url, UPLOAD_ENDPOINTS,
            method="POST",
            files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        )

        if resp is None:
            pytest.skip("No upload endpoint responded")

        assert resp.status_code != 500, (
            "Empty file upload caused 500 — this is a bug"
        )


# ── 3. Pipeline Status ────────────────────────────────────────────────────────

class TestPipelineStatus:

    def test_authenticated_can_list_pipelines(self, session_client, base_url):
        """POSITIVE: Authenticated GET to pipelines must return 200."""
        resp = probe(session_client, base_url, PIPELINE_ENDPOINTS, method="GET")

        if resp is None:
            pytest.skip("No pipeline endpoint responded")

        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}. Body: {resp.text[:300]}"
        )

    def test_unauthenticated_pipeline_blocked(self, anon_client, base_url):
        """NEGATIVE: Unauthenticated pipeline request must return 401/403."""
        resp = probe(anon_client, base_url, PIPELINE_ENDPOINTS, method="GET")

        if resp is None:
            pytest.skip("No pipeline endpoint responded")

        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}"
        )

    def test_fake_pipeline_id_returns_404(self, session_client, base_url):
        """NEGATIVE: Nonexistent pipeline ID must return 404, not 500."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        paths = [f"{p}/{fake_id}" for p in PIPELINE_ENDPOINTS]
        resp = probe(session_client, base_url, paths, method="GET")

        if resp is None:
            pytest.skip("No pipeline/{id} endpoint responded")

        assert resp.status_code != 500, (
            "Nonexistent pipeline ID caused 500 — this is a bug"
        )
        assert resp.status_code in (400, 404), (
            f"Expected 404/400, got {resp.status_code}"
        )


# ── 4. Download Endpoints ─────────────────────────────────────────────────────

class TestDownloadEndpoints:

    def test_authenticated_download_accessible(self, session_client, base_url):
        """POSITIVE: Authenticated download must not return 401/403."""
        resp = probe(
            session_client, base_url, DOWNLOAD_ENDPOINTS,
            method="GET",
            allow_redirects=False
        )

        if resp is None:
            pytest.skip("No download endpoint responded")

        assert resp.status_code not in (401, 403), (
            "Authenticated download was blocked with 401/403"
        )

    def test_unauthenticated_download_blocked(self, anon_client, base_url):
        """NEGATIVE: Unauthenticated download must return 401/403."""
        resp = probe(
            anon_client, base_url, DOWNLOAD_ENDPOINTS,
            method="GET",
            allow_redirects=False
        )

        if resp is None:
            pytest.skip("No download endpoint responded")

        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}"
        )


# ── 5. Error Handling ─────────────────────────────────────────────────────────

class TestErrorHandling:

    def test_malformed_json_returns_4xx(self, session_client, base_url):
        """NEGATIVE: Malformed JSON body must return 4xx not 500."""
        resp = session_client.post(
            f"{base_url}/api/auth/login",
            data="{ this is not valid json !!!",
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code == 404:
            pytest.skip("Endpoint not found")

        assert resp.status_code != 500, (
            "Malformed JSON caused 500 — this is a bug"
        )
        assert resp.status_code >= 400, (
            f"Expected 4xx, got {resp.status_code}"
        )

    def test_sql_injection_rejected(self, anon_client, base_url):
        """NEGATIVE: SQL injection in email must return 4xx not 500."""
        resp = probe(
            anon_client, base_url, AUTH_ENDPOINTS,
            method="POST",
            json={
                "email": "' OR '1'='1'; DROP TABLE users; --",
                "password": "' OR '1'='1"
            }
        )

        if resp is None:
            pytest.skip("No auth endpoint responded")

        assert resp.status_code != 500, (
            "SQL injection caused 500 — potential vulnerability!"
        )
        assert 400 <= resp.status_code < 500, (
            f"Expected 4xx, got {resp.status_code}"
        )

    def test_oversized_upload_rejected(self, session_client, base_url):
        """NEGATIVE: File over size limit must not cause 500."""
        row = b"1,TestName,12345\n"
        big_data = b"id,name,value\n" + row * (25 * 1024 * 1024 // len(row))

        resp = probe(
            session_client, base_url, UPLOAD_ENDPOINTS,
            method="POST",
            files={"file": ("big.csv", io.BytesIO(big_data), "text/csv")}
        )

        if resp is None:
            pytest.skip("No upload endpoint responded")

        assert resp.status_code != 500, (
            "Oversized upload caused 500 — this is a bug"
        )