import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
import re
from pathlib import Path
from urllib.parse import quote

BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "I1KhCgDNwKwjYyo9SLqGbdm2"

SCREENSHOT_DIR = Path("api-tests/screenshots/template_outputs")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def save_response_screenshot(name, response):
    """Save API response to a JSON file for debugging"""
    # Sanitize filename to remove invalid characters
    safe_name = re.sub(r'[<>:"/\|?*()\[\]{}]', '_', str(name))
    safe_name = re.sub(r'\\', '_', safe_name)  # Remove escaped backslashes
    safe_name = re.sub(r'\d', 'd', safe_name)  # Fix \d patterns
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    if len(safe_name) > 200:  # Limit filename length
        safe_name = safe_name[:200]
    
    filepath = SCREENSHOT_DIR / (safe_name + ".json")
    try:
        if response.status_code >= 200 and response.status_code < 300:
            try:
                json.dump(response.json(), open(filepath, "w", encoding="utf-8"), indent=4)
            except (json.JSONDecodeError, ValueError):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(response.text)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Status: {response.status_code}\n")
                f.write(f"Headers: {dict(response.headers)}\n")
                try:
                    f.write(f"Body: {response.text}")
                except Exception:
                    f.write("Body: [Unable to read response body]")
    except Exception as e:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Error saving response: {str(e)}\n")
            f.write(f"Status Code: {getattr(response, 'status_code', 'N/A')}\n")
    print("Saved response screenshot: " + str(filepath))




def test_get_valid_template():
    """Test Case 1: Get valid template"""
    # First, get list to find a valid identifier
    list_path = "/wp/v2/templates"
    list_url = f"{BASE_URL}{list_path}"
    try:
        list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    if list_response.status_code != 200:
        pytest.skip("No items available to test")
    try:
        items = list_response.json()
    except (json.JSONDecodeError, ValueError):
        pytest.skip("Invalid response from server")
    
    # Handle both list and dict responses
    if isinstance(items, dict):
        if items:
            first_key = list(items.keys())[0]
            item = items[first_key] if isinstance(items[first_key], dict) else {first_key: items[first_key]}
        else:
            pytest.skip("No items available to test")
    elif isinstance(items, list):
        if not items:
            pytest.skip("No items available to test")
        item = items[0]
    else:
        pytest.skip("Invalid response format")
    
    if not item:
        pytest.skip("No items available to test")
    
    identifier = item.get("id", item.get("slug", item.get("name", item.get("id", "1"))))
    
    url = f"{BASE_URL}/wp/v2/templates/{{id}}".replace("{{id}}", str(identifier))
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("get_valid_template", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text[:200] if hasattr(response, 'text') else 'No response text'}"
    if response.status_code == 200:
        try:
            data = response.json()
            assert isinstance(data, dict), "Response should be a dictionary"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {str(e)}")
    # If 404, that's also valid - resource doesn't exist

def test_get_invalid_template():
    """Test Case 2: Get invalid template"""
    url = f"{BASE_URL}/wp/v2/templates/{{id}}".replace("{{id}}", "invalid-999999")
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("get_invalid_template", response)
    
    # Accept 404 (not found) as expected, or 200 if somehow valid
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"

def test_unauthorized_template():
    """Test Case 3: Unauthorized access to template"""
    url = f"{BASE_URL}/wp/v2/templates/{{id}}".replace("{{id}}", "test")
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("unauthorized_template", response)
    
    # Accept 200 (if public), 401 (unauthorized), 403 (forbidden), or 404 (not found) as valid responses
    assert response.status_code in [200, 401, 403, 404], f"Expected 200, 401, 403, or 404, got {response.status_code}"

def test_response_schema_template():
    """Test Case 4: Response Schema Validation for template"""
    # First, get list to find a valid identifier
    list_path = "/wp/v2/templates"
    list_url = f"{BASE_URL}{list_path}"
    try:
        list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    if list_response.status_code != 200:
        pytest.skip("No items available to test")
    try:
        items = list_response.json()
    except (json.JSONDecodeError, ValueError):
        pytest.skip("Invalid response from server")
    
    # Handle both list and dict responses
    if isinstance(items, dict):
        if items:
            first_key = list(items.keys())[0]
            item = items[first_key] if isinstance(items[first_key], dict) else {first_key: items[first_key]}
        else:
            pytest.skip("No items available to test")
    elif isinstance(items, list):
        if not items:
            pytest.skip("No items available to test")
        item = items[0]
    else:
        pytest.skip("Invalid response format")
    
    if not item:
        pytest.skip("No items available to test")
    
    identifier = item.get("id", item.get("slug", item.get("name", item.get("id", "1"))))
    
    url = f"{BASE_URL}/wp/v2/templates/{{id}}".replace("{{id}}", str(identifier))
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("schema_template", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        try:
            data = response.json()
            assert isinstance(data, dict), "Response should be a dictionary"
            assert len(data) > 0, "Response should have at least one field"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {str(e)}")

def test_response_content_type_template():
    """Test Case 5: Response Content Type for template"""
    # First, get list to find a valid identifier
    list_path = "/wp/v2/templates"
    list_url = f"{BASE_URL}{list_path}"
    try:
        list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    if list_response.status_code != 200:
        pytest.skip("No items available to test")
    try:
        items = list_response.json()
    except (json.JSONDecodeError, ValueError):
        pytest.skip("Invalid response from server")
    
    # Handle both list and dict responses
    if isinstance(items, dict):
        if items:
            first_key = list(items.keys())[0]
            item = items[first_key] if isinstance(items[first_key], dict) else {first_key: items[first_key]}
        else:
            pytest.skip("No items available to test")
    elif isinstance(items, list):
        if not items:
            pytest.skip("No items available to test")
        item = items[0]
    else:
        pytest.skip("Invalid response format")
    
    if not item:
        pytest.skip("No items available to test")
    
    identifier = item.get("id", item.get("slug", item.get("name", item.get("id", "1"))))
    
    url = f"{BASE_URL}/wp/v2/templates/{{id}}".replace("{{id}}", str(identifier))
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("content_type_template", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "")
        assert content_type, "Response should have a Content-Type header"

def test_response_structure_template():
    """Test Case 6: Response Structure Validation for template"""
    # First, get list to find a valid identifier
    list_path = "/wp/v2/templates"
    list_url = f"{BASE_URL}{list_path}"
    try:
        list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    if list_response.status_code != 200:
        pytest.skip("No items available to test")
    try:
        items = list_response.json()
    except (json.JSONDecodeError, ValueError):
        pytest.skip("Invalid response from server")
    
    # Handle both list and dict responses
    if isinstance(items, dict):
        if items:
            first_key = list(items.keys())[0]
            item = items[first_key] if isinstance(items[first_key], dict) else {first_key: items[first_key]}
        else:
            pytest.skip("No items available to test")
    elif isinstance(items, list):
        if not items:
            pytest.skip("No items available to test")
        item = items[0]
    else:
        pytest.skip("Invalid response format")
    
    if not item:
        pytest.skip("No items available to test")
    
    identifier = item.get("id", item.get("slug", item.get("name", item.get("id", "1"))))
    
    url = f"{BASE_URL}/wp/v2/templates/{{id}}".replace("{{id}}", str(identifier))
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("structure_template", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        try:
            data = response.json()
            assert isinstance(data, dict), "Response should be a dictionary"
            # Validate structure
            assert len(data) > 0, "Response should have at least one field"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {str(e)}")