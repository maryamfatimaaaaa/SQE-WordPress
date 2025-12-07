# Test Cases - Ability Run

## Controller: WP_REST_Abilities_V1_Run_Controller
## Source File: class-wp-rest-abilities-v1-run-controller.php
## Endpoint: `/wp-abilities/v1/abilities/{name}/run`
## Methods: GET, POST, DELETE

---

## Overview

This test suite was automatically generated from the PHP controller file.

**Generated Tests:**

- Execute with correct method
- Execute with wrong method (405)
- Execute invalid action (404)
- Execute unauthorized (401)

---

## Running Tests

```bash
# Run all tests for this endpoint
pytest api-tests/generated/test-ability-run.py -v

# Run specific test
pytest api-tests/generated/test-ability-run.py::test_get_all_ability_run -v
```

---

*Auto-generated from class-wp-rest-abilities-v1-run-controller.php*
