import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
import re
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "I1KhCgDNwKwjYyo9SLqGbdm2"

SCREENSHOT_DIR = Path("api-tests/screenshots/test_lists_outputs")
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


def test_get_all_abilities():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_all_abilities", response)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_get_valid_ability():
    list_url = f"{BASE_URL}/wp-abilities/v1/abilities"
    list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    assert list_response.status_code == 200
    abilities = list_response.json()
    assert len(abilities) > 0, "No abilities found to test"
    
    ability_name = abilities[0]["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"get_ability_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == ability_name
    assert "label" in data
    assert "description" in data
    assert "category" in data
    assert "input_schema" in data
    assert "output_schema" in data
    assert "meta" in data


def test_get_invalid_ability():
    url = f"{BASE_URL}/wp-abilities/v1/abilities/invalid-ability-name"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("get_invalid_ability", response)
    
    assert response.status_code == 404
    assert response.json().get("message") == "Ability not found."


def test_unauthorized_access():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url)
    save_response_screenshot("unauthorized_access_abilities", response)
    
    assert response.status_code == 401


def test_pagination():
    url = f"{BASE_URL}/wp-abilities/v1/abilities?page=1&per_page=5"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("pagination_abilities", response)
    
    assert response.status_code == 200
    assert len(response.json()) <= 5
    assert "X-WP-Total" in response.headers
    assert "X-WP-TotalPages" in response.headers


def test_pagination_navigation():
    url = f"{BASE_URL}/wp-abilities/v1/abilities?page=2&per_page=2"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("pagination_navigation", response)
    
    assert response.status_code == 200
    if int(response.headers.get("X-WP-TotalPages", 1)) > 1:
        assert "Link" in response.headers or response.headers.get("X-WP-TotalPages") == "1"


def test_head_request():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.head(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("head_request_abilities", response)
    
    assert response.status_code == 200
    assert response.text == ""
    assert "X-WP-Total" in response.headers


def test_schema_validation():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("schema_validation_abilities", response)
    
    assert response.status_code == 200
    abilities = response.json()
    
    for ability in abilities:
        assert "name" in ability
        assert "label" in ability
        assert "description" in ability
        assert "category" in ability
        assert "input_schema" in ability
        assert "output_schema" in ability
        assert "meta" in ability
        assert isinstance(ability["input_schema"], (dict, list))
        assert isinstance(ability["output_schema"], (dict, list))
        assert isinstance(ability["meta"], dict)


def test_links_validation():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("links_validation_abilities", response)
    
    assert response.status_code == 200
    abilities = response.json()
    
    for ability in abilities:
        assert "_links" in ability
        links = ability["_links"]
        assert "self" in links
        assert "collection" in links
        assert "wp:action-run" in links


def test_filter_by_category():
    category = "site"
    url = f"{BASE_URL}/wp-abilities/v1/abilities?category={category}"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"filter_by_category_{category}", response)
    
    assert response.status_code == 200
    abilities = response.json()
    
    for ability in abilities:
        assert ability["category"] == category


def test_filter_by_invalid_category():
    url = f"{BASE_URL}/wp-abilities/v1/abilities?category=invalid-category"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("filter_by_invalid_category", response)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_input_output_schema_structure():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("schema_structure_validation", response)
    
    assert response.status_code == 200
    abilities = response.json()
    
    for ability in abilities:
        input_schema = ability["input_schema"]
        output_schema = ability["output_schema"]
        
        assert isinstance(input_schema, (dict, list))
        assert isinstance(output_schema, (dict, list))


def test_meta_annotations_field():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("meta_annotations_validation", response)
    
    assert response.status_code == 200
    abilities = response.json()
    
    for ability in abilities:
        assert "meta" in ability
        meta = ability["meta"]
        if "annotations" in meta:
            annotations = meta["annotations"]
            if annotations is not None and not isinstance(annotations, bool):
                assert isinstance(annotations, dict)
                for key, value in annotations.items():
                    assert isinstance(value, bool), f"Annotation {key} should be boolean"


def test_per_page_limits():
    url_min = f"{BASE_URL}/wp-abilities/v1/abilities?per_page=1"
    response_min = requests.get(url_min, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("per_page_minimum", response_min)
    assert response_min.status_code == 200
    assert len(response_min.json()) <= 1
    
    url_max = f"{BASE_URL}/wp-abilities/v1/abilities?per_page=100"
    response_max = requests.get(url_max, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("per_page_maximum", response_max)
    assert response_max.status_code == 200


def test_ability_name_pattern():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("ability_name_pattern", response)
    
    assert response.status_code == 200
    abilities = response.json()
    
    pattern = re.compile(r'^[a-zA-Z0-9\-/]+$')
    
    for ability in abilities:
        assert pattern.match(ability["name"]), f"Invalid name pattern: {ability['name']}"


def test_show_in_rest_filter():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("show_in_rest_filter", response)
    
    assert response.status_code == 200


def test_context_parameter():
    url = f"{BASE_URL}/wp-abilities/v1/abilities?context=view"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("context_parameter", response)
    
    assert response.status_code == 200
    abilities = response.json()
    assert len(abilities) > 0


def test_response_content_type():
    url = f"{BASE_URL}/wp-abilities/v1/abilities"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("response_content_type", response)
    
    assert response.status_code == 200
    assert "application/json" in response.headers.get("Content-Type", "")


def test_combined_filters():
    url = f"{BASE_URL}/wp-abilities/v1/abilities?category=site&page=1&per_page=3"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("combined_filters", response)
    
    assert response.status_code == 200
    abilities = response.json()
    assert len(abilities) <= 3
    for ability in abilities:
        assert ability["category"] == "site"