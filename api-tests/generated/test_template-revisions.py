import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/template-revisions_outputs")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def save_response_screenshot(name, response):
    """Save API response to a JSON file for debugging"""
    filepath = SCREENSHOT_DIR / f"{name}.json"
    try:
        json.dump(response.json(), open(filepath, "w", encoding="utf-8"), indent=4)
    except Exception:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)
    print(f"Saved response screenshot: {filepath}")




def test_get_all_template_revisions():
    """Test retrieving all template_revisions"""
    url = f"{BASE_URL}/wp/v2/template_revisions"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_all_template_revisions", response)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_unauthorized_template_revisions():
    """Test unauthorized access to template_revisions"""
    url = f"{BASE_URL}/wp/v2/template_revisions"
    response = requests.get(url)
    save_response_screenshot("unauthorized_template_revisions", response)
    
    assert response.status_code == 401

def test_pagination_template_revisions():
    """Test pagination for template_revisions"""
    url = f"{BASE_URL}/wp/v2/template_revisions?page=1&per_page=5"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("pagination_template_revisions", response)
    
    assert response.status_code == 200
    assert len(response.json()) <= 5

def test_schema_template_revisions():
    """Test response schema for template_revisions"""
    url = f"{BASE_URL}/wp/v2/template_revisions"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("schema_template_revisions", response)
    
    assert response.status_code == 200
    items = response.json()
    for item in items:
        assert isinstance(item, dict)
        assert "_links" in item

def test_head_template_revisions():
    """Test HEAD request for template_revisions"""
    url = f"{BASE_URL}/wp/v2/template_revisions"
    response = requests.head(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("head_template_revisions", response)
    
    assert response.status_code == 200
    assert response.text == ""