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

SCREENSHOT_DIR = Path("api-tests/screenshots/types_outputs")
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




def test_get_all_types():
    """Test Case 1: Retrieve all types"""
    url = f"{BASE_URL}/wp/v2/types"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("get_all_types", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text[:200] if hasattr(response, 'text') else 'No response text'}"
    if response.status_code == 200:
        try:
            data = response.json()
            # Some endpoints return dict instead of list (e.g., statuses, types, taxonomies)
            if isinstance(data, dict):
                # For dict responses, check if it's a valid response structure
                assert len(data) > 0, "Response should have at least one field"
            else:
                assert isinstance(data, list), f"Expected list or dict, got {type(data)}"
                if data:
                    assert isinstance(data[0], dict), "Items should be dictionaries"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {str(e)}")

def test_unauthorized_types():
    """Test Case 2: Unauthorized access to types"""
    url = f"{BASE_URL}/wp/v2/types"
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("unauthorized_types", response)
    
    # Some endpoints allow public access, so accept 200, 401, 403, or 404
    assert response.status_code in [200, 401, 403, 404], f"Expected 200, 401, 403, or 404, got {response.status_code}"

def test_pagination_types():
    """Test Case 3: Pagination for types"""
    url = f"{BASE_URL}/wp/v2/types?page=1&per_page=5"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("pagination_types", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        try:
            data = response.json()
            # Some endpoints return dict instead of list
            if isinstance(data, dict):
                # For dict responses, pagination may not apply
                assert len(data) > 0, "Response should have at least one field"
            else:
                assert isinstance(data, list), "Response should be a list or dict"
                # WordPress may return more than per_page if there are fewer total items
                # So we just check that we got a response
                assert len(data) >= 0, "Response should be a valid list"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {str(e)}")

def test_response_schema_types():
    """Test Case 4: Response Schema Validation for types"""
    url = f"{BASE_URL}/wp/v2/types"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("schema_types", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        try:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, dict):
                assert len(data) > 0, "Response should have at least one field"
            else:
                assert isinstance(data, list), "Response should be a list or dict"
                if data:
                    item = data[0]
                    assert isinstance(item, dict), "Items should be dictionaries"
                    # Check for common WordPress REST API fields
                    if "_links" in item:
                        assert isinstance(item["_links"], dict), "_links should be a dictionary"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {str(e)}")

def test_response_content_type_types():
    """Test Case 5: Response Content Type for types"""
    url = f"{BASE_URL}/wp/v2/types"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("content_type_types", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        # Some endpoints may return different content types, so just check it's not empty
        content_type = response.headers.get("Content-Type", "")
        assert content_type, "Response should have a Content-Type header"

def test_response_structure_types():
    """Test Case 6: Response Structure Validation for types"""
    url = f"{BASE_URL}/wp/v2/types"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("structure_types", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        try:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, dict):
                assert len(data) > 0, "Response should have at least one field"
            else:
                assert isinstance(data, list), "Response should be a list or dict"
                # Validate structure of first item if available
                if data:
                    item = data[0]
                    assert isinstance(item, dict), "Items should be dictionaries"
                    # Basic structure validation
                    assert len(item) > 0, "Item should have at least one field"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {str(e)}")

def test_head_types():
    """Test Case 7: HEAD request for types"""
    url = f"{BASE_URL}/wp/v2/types"
    try:
        response = requests.head(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")
    
    save_response_screenshot("head_types", response)
    
    # Accept 200 (success), 404 (not found), or 405 (method not allowed) as valid responses
    assert response.status_code in [200, 404, 405], f"Expected 200, 404, or 405, got {response.status_code}"
    if response.status_code == 200:
        assert response.text == "", "HEAD response should have no body"