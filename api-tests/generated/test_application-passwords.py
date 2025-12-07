import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/application-passwords_outputs")
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




def test_get_all_application_passwords():
    """Test retrieving all application_passwords"""
    url = f"{BASE_URL}/wp-abilities/v1/application_passwords"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_all_application_passwords", response)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_unauthorized_application_passwords():
    """Test unauthorized access to application_passwords"""
    url = f"{BASE_URL}/wp-abilities/v1/application_passwords"
    response = requests.get(url)
    save_response_screenshot("unauthorized_application_passwords", response)
    
    assert response.status_code == 401

def test_pagination_application_passwords():
    """Test pagination for application_passwords"""
    url = f"{BASE_URL}/wp-abilities/v1/application_passwords?page=1&per_page=5"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("pagination_application_passwords", response)
    
    assert response.status_code == 200
    assert len(response.json()) <= 5

def test_schema_application_passwords():
    """Test response schema for application_passwords"""
    url = f"{BASE_URL}/wp-abilities/v1/application_passwords"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("schema_application_passwords", response)
    
    assert response.status_code == 200
    items = response.json()
    for item in items:
        assert isinstance(item, dict)
        assert "_links" in item

def test_head_application_passwords():
    """Test HEAD request for application_passwords"""
    url = f"{BASE_URL}/wp-abilities/v1/application_passwords"
    response = requests.head(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("head_application_passwords", response)
    
    assert response.status_code == 200
    assert response.text == ""