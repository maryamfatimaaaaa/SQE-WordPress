# Test Cases — Menu-Location

    ## Source Information
    - **Controller:** WP_REST_Menu_Locations_Controller
    - **Source File:** class-wp-rest-menu-locations-controller.php
    - **Endpoint:** `/wp/v2/menu-locations/{id}`
    - **Methods:** GET
    - **Type:** single

    ---

    # Test Case Documentation

    
    ### Test Case 1 — Get Valid Item

    **Name:** test_get_valid_item

    **Purpose:** Retrieve a valid resource.

    **API:** GET /wp/v2/menu-locations/{id}/{id}

    **Steps:**
    - Send authenticated GET request using valid ID.

    **Expected Results:**
    - Status: 200

    ---
    
    ### Test Case 2 — Get Invalid Item

    **Name:** test_get_invalid_item

    **Purpose:** Verify 404 for invalid resource.

    **API:** GET /wp/v2/menu-locations/{id}/999999

    **Steps:**
    - Send GET request with non-existent ID.

    **Expected Results:**
    - Status: 404

    ---
    
    ### Test Case 3 — Unauthorized Access

    **Name:** test_unauthorized_access

    **Purpose:** Ensure unauthenticated calls fail.

    **API:** GET /wp/v2/menu-locations/{id}/{id}

    **Steps:**
    - Send GET without authentication.

    **Expected Results:**
    - Status: 401 or 403

    ---
    
    ### Test Case 4 — Response Schema Validation

    **Name:** test_response_schema_validation

    **Purpose:** Validate single item schema.

    **API:** GET /wp/v2/menu-locations/{id}/{id}

    **Steps:**
    - Check keys against schema.

    **Expected Results:**
    - Status: 200

    ---
    
    ### Test Case 5 — Response Content Type

    **Name:** test_response_content_type

    **Purpose:** Ensure MIME type is correct.

    **API:** GET /wp/v2/menu-locations/{id}/{id}

    **Steps:**
    - Inspect Content-Type header.

    **Expected Results:**
    - Header: application/json

    ---
    
    ### Test Case 6 — Response Structure Validation

    **Name:** test_response_structure_validation

    **Purpose:** Ensure response is a JSON object.

    **API:** GET /wp/v2/menu-locations/{id}/{id}

    **Steps:**
    - Validate object structure.

    **Expected Results:**
    - Status: 200

    ---
    

    *Auto-generated from class-wp-rest-menu-locations-controller.php*
    