# Test Cases - Abilities Run

## Source Information
- **Controller:** WP_REST_Abilities_V1_Run_Controller
- **Source File:** class-wp-rest-abilities-v1-run-controller.php
- **Endpoint:** `/wp-abilities/v1/abilities/{name}/run`
- **Methods:** GET, POST, DELETE
- **Type:** action

## Generated Tests

This test suite was automatically generated from the PHP controller.

### Test Coverage

- Test Case 1: Execute readonly ability
- Test Case 2: Execute with wrong HTTP method
- Test Case 3: Execute invalid ability
- Test Case 4: Unauthorized execution
- Test Case 5: Response Schema Validation
- Test Case 6: Response Structure Validation

## Running Tests

```bash
pytest api-tests/generated/test_abilities-run.py -v
```

## Test Details

Each test case validates:
- HTTP status codes
- Response structure and schema
- Authentication and authorization
- Error handling
- Content type validation

---

*Auto-generated from class-wp-rest-abilities-v1-run-controller.php*
