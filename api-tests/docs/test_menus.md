# Test Cases - Menus

## Source Information
- **Controller:** WP_REST_Menus_Controller
- **Source File:** class-wp-rest-menus-controller.php
- **Endpoint:** `/wp/v2/menus`
- **Methods:** GET, HEAD
- **Type:** collection

## Generated Tests

This test suite was automatically generated from the PHP controller.

### Test Coverage

- Test Case 1: Retrieve all items
- Test Case 2: Unauthorized access
- Test Case 3: Pagination
- Test Case 4: Response Schema Validation
- Test Case 5: Response Content Type
- Test Case 6: Response Structure Validation
- Test Case 7: HEAD request (if supported)

## Running Tests

```bash
pytest api-tests/generated/test_menus.py -v
```

## Test Details

Each test case validates:
- HTTP status codes
- Response structure and schema
- Authentication and authorization
- Error handling
- Content type validation

---

*Auto-generated from class-wp-rest-menus-controller.php*
