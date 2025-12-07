import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path
import uuid
import time

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "I1KhCgDNwKwjYyo9SLqGbdm2"
USER_ID = 1   # Change if needed

SCREENSHOT_DIR = Path("api-tests/screenshots/test_run_outputs")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def save_response(name, response):
    """Save every test API response as a JSON file for screenshot/report."""
    output = SCREENSHOT_DIR / f"{name}.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump({
            "status": response.status_code,
            "url": response.url,
            "body": safe_json(response)
        }, f, indent=2)
    return output


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return response.text


def api(method, endpoint, **kwargs):
    """Wrapper to make authenticated requests & save logs."""
    url = f"{BASE_URL}{endpoint}"
    response = requests.request(
        method,
        url,
        auth=HTTPBasicAuth(USERNAME, APP_PASSWORD),
        **kwargs
    )
    return response


# ------------------------------------------------------
# -------------------   TEST CASES   -------------------
# ------------------------------------------------------

def test_01_list_application_passwords():
    """GET all application passwords"""
    response = api("GET", f"/wp/v2/users/{USER_ID}/application-passwords")
    save_response("01_list_passwords", response)

    assert response.status_code in (200, 404)
    assert isinstance(safe_json(response), (dict, list))


def test_02_create_application_password():
    """POST → create new password"""
    payload = {
        "name": f"TestKey-{uuid.uuid4()}",
    }

    response = api("POST", f"/wp/v2/users/{USER_ID}/application-passwords", json=payload)
    save_response("02_create_password", response)

    assert response.status_code == 201
    assert "uuid" in response.json()

    global CREATED_UUID
    CREATED_UUID = response.json()["uuid"]


def test_03_get_single_password():
    """GET specific password by uuid"""
    response = api("GET", f"/wp/v2/users/{USER_ID}/application-passwords/{CREATED_UUID}")
    save_response("03_get_single_password", response)

    assert response.status_code == 200
    assert response.json().get("uuid") == CREATED_UUID


def test_04_update_application_password():
    """PUT → update the name"""
    payload = {"name": "Updated-Test-Password"}

    response = api("PUT", f"/wp/v2/users/{USER_ID}/application-passwords/{CREATED_UUID}",
                   json=payload)
    save_response("04_update_password", response)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated-Test-Password"


def test_05_introspect_password():
    """GET /introspect endpoint → check currently used application password"""
    response = api("GET", f"/wp/v2/users/{USER_ID}/application-passwords/introspect")
    save_response("05_introspect", response)

    assert response.status_code in (200, 404)


def test_06_delete_single_password():
    """DELETE specific password"""
    response = api("DELETE", f"/wp/v2/users/{USER_ID}/application-passwords/{CREATED_UUID}")
    save_response("06_delete_single", response)

    assert response.status_code == 200


def test_07_delete_all_passwords():
    """DELETE all passwords"""
    response = api("DELETE", f"/wp/v2/users/{USER_ID}/application-passwords")
    save_response("07_delete_all", response)

    assert response.status_code in (200, 204)


def test_08_invalid_uuid():
    """Accessing invalid uuid must return 404"""
    fake = "00000000-0000-0000-0000-000000000000"

    response = api("GET", f"/wp/v2/users/{USER_ID}/application-passwords/{fake}")
    save_response("08_invalid_uuid", response)

    assert response.status_code == 404


def test_09_missing_name_field_on_create():
    """POST with missing required name must fail"""
    response = api("POST", f"/wp/v2/users/{USER_ID}/application-passwords",
                   json={})
    save_response("09_missing_name", response)

    assert response.status_code == 400


def test_10_unauthenticated_access():
    """No credentials should return 401"""
    url = f"{BASE_URL}/wp/v2/users/{USER_ID}/application-passwords"
    response = requests.get(url)  # no auth
    save_response("10_unauthenticated", response)

    assert response.status_code in (401, 403)
