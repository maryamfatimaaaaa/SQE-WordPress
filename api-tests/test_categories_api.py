import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def save_response_screenshot(name, response):
    filepath = SCREENSHOT_DIR / f"{name}.json"
    try:
        json.dump(response.json(), open(filepath, "w", encoding="utf-8"), indent=4)
    except Exception:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)
    print(f"Saved response screenshot: {filepath}")

# ----------------- Tests -----------------

def test_get_all_categories():
    url = f"{BASE_URL}/wp-abilities/v1/categories"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_all_categories", response)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_valid_category():
    slug = "site"  # Replace with valid slug
    url = f"{BASE_URL}/wp-abilities/v1/categories/{slug}"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"get_category_{slug}", response)
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == slug
    assert "label" in data
    assert "description" in data
    assert "meta" in data

def test_get_invalid_category():
    url = f"{BASE_URL}/wp-abilities/v1/categories/example"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_invalid_category", response)
    assert response.status_code == 404
    assert response.json().get("message") == "Ability category not found."

def test_unauthorized_access():
    url = f"{BASE_URL}/wp-abilities/v1/categories"
    response = requests.get(url)  # No auth
    save_response_screenshot("unauthorized_access", response)
    assert response.status_code == 401

def test_pagination():
    url = f"{BASE_URL}/wp-abilities/v1/categories?page=1&per_page=1"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("pagination_test", response)
    assert response.status_code == 200
    assert len(response.json()) <= 1
    assert "X-WP-Total" in response.headers
    assert "X-WP-TotalPages" in response.headers

def test_head_request():
    url = f"{BASE_URL}/wp-abilities/v1/categories"
    response = requests.head(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("head_request_test", response)
    assert response.status_code == 200
    # Response body should be empty for HEAD request
    assert response.text == ""

def test_schema_validation():
    url = f"{BASE_URL}/wp-abilities/v1/categories"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("schema_validation", response)
    for cat in response.json():
        assert "slug" in cat
        assert "label" in cat
        assert "description" in cat
        assert "meta" in cat

def test_links_validation():
    url = f"{BASE_URL}/wp-abilities/v1/categories"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("links_validation", response)
    for cat in response.json():
        assert "_links" in cat
        links = cat["_links"]
        assert "self" in links
        assert "collection" in links
        assert "abilities" in links
