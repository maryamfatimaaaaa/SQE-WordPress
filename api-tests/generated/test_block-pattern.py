import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/block-pattern_outputs")
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




def test_get_valid_block_pattern():
    """Test getting valid block_pattern"""
    list_path = "/wp/v2/block_patterns"
    list_url = f"{BASE_URL}{list_path}"
    list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    
    if list_response.status_code != 200 or not list_response.json():
        pytest.skip("No items available")
    
    item = list_response.json()[0]
    identifier = item.get("name", item.get("slug", item.get("name", "1")))
    
    url = f"{BASE_URL}/wp/v2/block_patterns/{name}".replace("{name}", str(identifier))
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_valid_block_pattern", response)
    
    assert response.status_code == 200

def test_get_invalid_block_pattern():
    """Test getting invalid block_pattern"""
    url = f"{BASE_URL}/wp/v2/block_patterns/{name}".replace("{name}", "invalid-999")
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_invalid_block_pattern", response)
    
    assert response.status_code == 404

def test_unauthorized_block_pattern():
    """Test unauthorized access"""
    url = f"{BASE_URL}/wp/v2/block_patterns/{name}".replace("{name}", "test")
    response = requests.get(url)
    save_response_screenshot("unauthorized_block_pattern", response)
    
    assert response.status_code == 401