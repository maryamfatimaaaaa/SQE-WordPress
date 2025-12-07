import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/post-types_outputs")
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




def test_get_all_post_types():
    """Test retrieving all post_types"""
    url = f"{BASE_URL}/wp-abilities/v1/post_types"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_all_post_types", response)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_unauthorized_post_types():
    """Test unauthorized access to post_types"""
    url = f"{BASE_URL}/wp-abilities/v1/post_types"
    response = requests.get(url)
    save_response_screenshot("unauthorized_post_types", response)
    
    assert response.status_code == 401

def test_pagination_post_types():
    """Test pagination for post_types"""
    url = f"{BASE_URL}/wp-abilities/v1/post_types?page=1&per_page=5"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("pagination_post_types", response)
    
    assert response.status_code == 200
    assert len(response.json()) <= 5

def test_schema_post_types():
    """Test response schema for post_types"""
    url = f"{BASE_URL}/wp-abilities/v1/post_types"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("schema_post_types", response)
    
    assert response.status_code == 200
    items = response.json()
    for item in items:
        assert isinstance(item, dict)
        assert "_links" in item

def test_head_post_types():
    """Test HEAD request for post_types"""
    url = f"{BASE_URL}/wp-abilities/v1/post_types"
    response = requests.head(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("head_post_types", response)
    
    assert response.status_code == 200
    assert response.text == ""