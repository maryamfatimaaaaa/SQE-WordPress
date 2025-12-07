# Test Cases - Ability

## Controller: WP_REST_Abilities_V1_List_Controller
## Source File: class-wp-rest-abilities-v1-list-controller.php
## Endpoint: `/wp-abilities/v1/abilities/{name}`
## Methods: GET

---

## Overview

This test suite was automatically generated from the PHP controller file.

**Generated Tests:**

- Get valid resource
- Get invalid resource (404)
- Unauthorized access (401)

---

## Running Tests

```bash
# Run all tests for this endpoint
pytest api-tests/generated/test-ability.py -v

# Run specific test
pytest api-tests/generated/test-ability.py::test_get_all_ability -v
```

---

*Auto-generated from class-wp-rest-abilities-v1-list-controller.php*
