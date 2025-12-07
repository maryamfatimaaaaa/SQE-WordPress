import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
import re
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/ability_outputs")
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




def test_get_valid_ability():
    """Test retrieving a valid ability"""
    list_path = "/wp-abilities/v1/abilities"
    list_url = f"{BASE_URL}{list_path}"
    list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    
    if list_response.status_code != 200 or not list_response.json():
        pytest.skip("No items available")
    
    item = list_response.json()[0]
    identifier = item.get("name", item.get("slug", item.get("name", item.get("id"))))
    
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{name}".replace("{name}", str(identifier))
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_valid_ability", response)
    
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_get_invalid_ability():
    """Test retrieving an invalid ability"""
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{name}".replace("{name}", "invalid-12345")
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_invalid_ability", response)
    
    assert response.status_code == 404


def test_unauthorized_ability():
    """Test accessing ability without authentication"""
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{name}".replace("{name}", "test-item")
    response = requests.get(url)
    save_response_screenshot("unauthorized_ability", response)
    
    assert response.status_code == 401