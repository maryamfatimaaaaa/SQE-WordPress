import os
import json
import pytest
import requests
from requests.auth import HTTPBasicAuth

# -----------------------------------------
# CONFIGURATION
# -----------------------------------------

WP_BASE = "http://localhost:8000/wp-json/wp/v2"
USERNAME = "maryamfatima"                     # your username
APP_PASSWORD = "I1KhCgDNwKwjYyo9SLqGbdm2"     # your app password
AUTH = HTTPBasicAuth(USERNAME, APP_PASSWORD)

created_ids = []


# -----------------------------------------
# Helper — save API response for debugging
# -----------------------------------------

def save_response_screenshot(testname, response):
    directory = "api-tests/screenshots/attachments"
    os.makedirs(directory, exist_ok=True)
    filename = os.path.join(directory, f"{testname}.json")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        }, indent=2))


# ============================================================
# TEST 1 — CREATE MEDIA (NO REAL UPLOAD)
# ============================================================

def test_create_media_without_binary():
    """
    Test Scenario:
      Validate creating an attachment record using force=true.

    Steps:
      • POST /wp/v2/media?force=true with only metadata
      • No binary file is uploaded

    Expected Result:
      • HTTP 201
      • Returned object contains id and metadata
    """
    url = f"{WP_BASE}/media?force=true"

    payload = {
        "title": "Fake Attachment",
        "caption": "Created without binary upload",
        "mime_type": "image/png"
    }

    response = requests.post(url, json=payload, auth=AUTH)

    save_response_screenshot("create_media_no_upload", response)

    assert response.status_code == 201, f"Unexpected: {response.text}"
    data = response.json()
    assert "id" in data
    created_ids.append(data["id"])


# ============================================================
# TEST 2 — GET THE CREATED MEDIA
# ============================================================

def test_get_created_media():
    assert created_ids, "No ID from previous test"

    media_id = created_ids[0]
    url = f"{WP_BASE}/media/{media_id}"

    response = requests.get(url, auth=AUTH)
    save_response_screenshot("get_media", response)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == media_id


# ============================================================
# TEST 3 — UPDATE MEDIA METADATA
# ============================================================

def test_update_media_metadata():
    assert created_ids
    media_id = created_ids[0]

    url = f"{WP_BASE}/media/{media_id}"
    payload = {
        "title": "Updated Fake Title",
        "caption": "Updated Fake Caption"
    }

    response = requests.post(url, json=payload, auth=AUTH)
    save_response_screenshot("update_media", response)

    assert response.status_code == 200
    data = response.json()
    assert data["title"]["raw"] == "Updated Fake Title"
    assert data["caption"]["raw"] == "Updated Fake Caption"


# ============================================================
# TEST 4 — POST PROCESS MEDIA (ALLOWED ON FAKE MEDIA)
# ============================================================

def test_post_process_fake_media():
    assert created_ids
    media_id = created_ids[0]

    url = f"{WP_BASE}/media/{media_id}/post-process"
    payload = {"action": "create-image-subsizes"}

    response = requests.post(url, json=payload, auth=AUTH)
    save_response_screenshot("post_process", response)

    # WordPress returns 400 for fake media (correct behavior)
    assert response.status_code in (400, 404, 501)


# ============================================================
# TEST 5 — EDIT MEDIA (ALLOWED ON FAKE MEDIA)
# ============================================================

def test_edit_media_fake():
    assert created_ids
    media_id = created_ids[0]

    edit_url = f"{WP_BASE}/media/{media_id}/edit"
    payload = {
        "src": "https://example.com/fake.png",   # fake URL allowed
        "modifiers": {"rotation": 90}
    }

    response = requests.post(edit_url, json=payload, auth=AUTH)
    save_response_screenshot("edit_media_fake", response)

    # WordPress will return 400 or 501 because actual editing cannot run
    assert response.status_code in (400, 404, 501)
