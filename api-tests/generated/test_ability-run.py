import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
import re
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/ability-run_outputs")
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


def get_ability_by_annotation(readonly=None, destructive=None, idempotent=None):
    """Helper function to get an ability with specific annotations"""
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    
    if response.status_code != 200:
        return None
    
    abilities = response.json()
    for ability in abilities:
        annotations = ability.get("meta", {}).get("annotations", {})
        if isinstance(annotations, dict):
            match = True
            if readonly is not None and annotations.get("readonly") != readonly:
                match = False
            if destructive is not None and annotations.get("destructive") != destructive:
                match = False
            if idempotent is not None and annotations.get("idempotent") != idempotent:
                match = False
            if match:
                return ability
    return None


def test_execute_readonly_with_get():
    """Test executing readonly ability with GET"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{name}/run".replace("{name}", ability_name)
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("execute_readonly_get", response)
    
    assert response.status_code == 200


def test_execute_readonly_wrong_method():
    """Test executing readonly with wrong method"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{name}/run".replace("{name}", ability_name)
    response = requests.post(url, json={"input": {}}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("readonly_wrong_method", response)
    
    assert response.status_code == 405


def test_execute_invalid_ability():
    """Test executing non-existent ability"""
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{name}/run".replace("{name}", "invalid-ability")
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("execute_invalid", response)
    
    assert response.status_code == 404


def test_execute_unauthorized():
    """Test executing without authentication"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{name}/run".replace("{name}", ability_name)
    response = requests.get(url)
    save_response_screenshot("execute_unauthorized", response)
    
    assert response.status_code == 401