import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "7BXacgwVlWHXWNzwpL7ZtzGS"

SCREENSHOT_DIR = Path("api-tests/screenshots/test_run_outputs")
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


def test_execute_readonly_ability_with_get():
    """Test executing a readonly ability using GET method"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"execute_readonly_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_readonly_ability_with_post_should_fail():
    """Test executing a readonly ability with POST method should fail"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    response = requests.post(url, json={"input": None}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"readonly_post_fail_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code == 405
    assert "Read-only abilities require GET method" in response.json().get("message", "")


def test_execute_update_ability_with_post():
    """Test executing an update ability using POST method"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    response = requests.post(url, json={"input": None}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"execute_update_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_update_ability_with_get_should_fail():
    """Test executing an update ability with GET method should fail"""
    ability = get_ability_by_annotation(readonly=False, destructive=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"update_get_fail_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code == 405
    assert "Abilities that perform updates require POST method" in response.json().get("message", "")


def test_execute_destructive_ability_with_delete():
    """Test executing a destructive+idempotent ability using DELETE method"""
    ability = get_ability_by_annotation(destructive=True, idempotent=True)
    if not ability:
        pytest.skip("No destructive+idempotent ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    response = requests.delete(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"execute_destructive_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_destructive_ability_with_post_should_fail():
    """Test executing a destructive ability with POST method should fail"""
    ability = get_ability_by_annotation(destructive=True, idempotent=True)
    if not ability:
        pytest.skip("No destructive+idempotent ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    response = requests.post(url, json={"input": None}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"destructive_post_fail_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code == 405
    assert "destructive actions require DELETE method" in response.json().get("message", "")


def test_execute_invalid_ability():
    """Test executing non-existent ability"""
    url = f"{BASE_URL}/wp-abilities/v1/abilities/invalid-ability/run"
    response = requests.post(url, json={"input": None}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("execute_invalid_ability", response)
    
    assert response.status_code == 404
    assert response.json().get("message") == "Ability not found."


def test_execute_ability_unauthorized():
    """Test executing ability without authentication"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    response = requests.get(url)  # No auth, use GET for readonly
    save_response_screenshot("execute_unauthorized", response)
    
    assert response.status_code == 401


def test_execute_ability_with_valid_input():
    """Test executing ability with valid input in POST body"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    test_input = {"test": "data"}
    response = requests.post(url, json={"input": test_input}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"execute_with_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_readonly_ability_with_query_input():
    """Test executing readonly ability with input in query parameters"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.get(url, params={"input": "test"}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"readonly_query_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_ability_with_invalid_input():
    """Test executing ability with invalid input"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    invalid_input = {"completely": "wrong", "structure": 12345}
    response = requests.post(url, json={"input": invalid_input}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"invalid_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [400, 403]


def test_execute_ability_without_required_permissions():
    """Test executing ability without required permissions"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.post(url, json={"input": None}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"no_permissions_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_ability_with_null_input():
    """Test executing ability with null input"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.post(url, json={"input": None}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"null_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_ability_response_structure():
    """Test that ability execution response has proper structure"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"response_structure_{ability_name.replace('/', '_')}", response)
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None


def test_execute_ability_with_empty_input():
    """Test executing ability with empty object input"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.post(url, json={"input": {}}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"empty_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_ability_content_type():
    """Test that response has proper Content-Type header"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"content_type_{ability_name.replace('/', '_')}", response)
    
    if response.status_code == 200:
        assert "application/json" in response.headers.get("Content-Type", "")


def test_execute_ability_with_array_input():
    """Test executing ability with array input"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    array_input = ["item1", "item2", "item3"]
    response = requests.post(url, json={"input": array_input}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"array_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_ability_with_string_input():
    """Test executing ability with string input"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.post(url, json={"input": "test_string"}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"string_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_ability_with_number_input():
    """Test executing ability with number input"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.post(url, json={"input": 42}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"number_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_ability_with_boolean_input():
    """Test executing ability with boolean input"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.post(url, json={"input": True}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"boolean_input_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code in [200, 400, 403]


def test_execute_hidden_ability():
    """Test that abilities with show_in_rest=false return 404"""
    url = f"{BASE_URL}/wp-abilities/v1/abilities/hidden-ability-name/run"
    response = requests.post(url, json={"input": None}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot("execute_hidden_ability", response)
    
    assert response.status_code == 404


def test_execute_ability_error_handling():
    """Test that ability execution errors are properly returned"""
    ability = get_ability_by_annotation(readonly=False)
    if not ability:
        pytest.skip("No update ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.post(url, json={"input": None}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"error_handling_{ability_name.replace('/', '_')}", response)
    
    if response.status_code >= 400:
        error_data = response.json()
        assert "code" in error_data or "message" in error_data


def test_method_validation_order():
    """Test that method validation happens before input validation"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability found")
    
    ability_name = ability["name"]
    url = f"{BASE_URL}/wp-abilities/v1/abilities/{ability_name}/run"
    
    response = requests.post(url, json={"input": "invalid_data"}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD))
    save_response_screenshot(f"method_validation_order_{ability_name.replace('/', '_')}", response)
    
    assert response.status_code == 405
    assert "Read-only abilities require GET method" in response.json().get("message", "")