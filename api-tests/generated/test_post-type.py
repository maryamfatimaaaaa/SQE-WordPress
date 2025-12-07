import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/post-type_outputs")
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




def test_get_valid_post_type():
    """Test getting valid post_type"""
    list_path = "/wp-abilities/v1/post_types"
    list_url = f"{BASE_URL}{list_path}"
    list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    
    if list_response.status_code != 200 or not list_response.json():
        pytest.skip("No items available")
    
    item = list_response.json()[0]
    identifier = item.get("id", item.get("slug", item.get("name", "1")))
    
    url = f"{BASE_URL}/wp-abilities/v1/post_types/{id}".replace("{id}", str(identifier))
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_valid_post_type", response)
    
    assert response.status_code == 200

def test_get_invalid_post_type():
    """Test getting invalid post_type"""
    url = f"{BASE_URL}/wp-abilities/v1/post_types/{id}".replace("{id}", "invalid-999")
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_invalid_post_type", response)
    
    assert response.status_code == 404

def test_unauthorized_post_type():
    """Test unauthorized access"""
    url = f"{BASE_URL}/wp-abilities/v1/post_types/{id}".replace("{id}", "test")
    response = requests.get(url)
    save_response_screenshot("unauthorized_post_type", response)
    
    assert response.status_code == 401