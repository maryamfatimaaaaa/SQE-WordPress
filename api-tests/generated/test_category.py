import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/category_outputs")
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




def test_get_valid_category():
    """Test getting valid category"""
    list_path = "/wp/v2/"
    list_url = f"{BASE_URL}{list_path}"
    list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    
    if list_response.status_code != 200 or not list_response.json():
        pytest.skip("No items available")
    
    item = list_response.json()[0]
    identifier = item.get("slug", item.get("slug", item.get("name", "1")))
    
    url = f"{BASE_URL}/wp/v2//{slug}".replace("{slug}", str(identifier))
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_valid_category", response)
    
    assert response.status_code == 200

def test_get_invalid_category():
    """Test getting invalid category"""
    url = f"{BASE_URL}/wp/v2//{slug}".replace("{slug}", "invalid-999")
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_invalid_category", response)
    
    assert response.status_code == 404

def test_unauthorized_category():
    """Test unauthorized access"""
    url = f"{BASE_URL}/wp/v2//{slug}".replace("{slug}", "test")
    response = requests.get(url)
    save_response_screenshot("unauthorized_category", response)
    
    assert response.status_code == 401