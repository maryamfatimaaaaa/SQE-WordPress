# Test Cases - Block-Type

## Source Information
- **Controller:** WP_REST_Block_Types_Controller
- **Source File:** class-wp-rest-block-types-controller.php
- **Endpoint:** `/wp/v2/block-types/{id}`
- **Methods:** GET
- **Type:** single

## Generated Tests

This test suite was automatically generated from the PHP controller.

### Test Coverage

- Test Case 1: Get valid item
- Test Case 2: Get invalid item
- Test Case 3: Unauthorized access
- Test Case 4: Response Schema Validation
- Test Case 5: Response Content Type
- Test Case 6: Response Structure Validation

## Running Tests

```bash
pytest api-tests/generated/test_block-type.py -v
```

## Test Details

Each test case validates:
- HTTP status codes
- Response structure and schema
- Authentication and authorization
- Error handling
- Content type validation

---

*Auto-generated from class-wp-rest-block-types-controller.php*
