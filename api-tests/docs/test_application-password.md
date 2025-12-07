# Test Cases - Application Password

## Source Information
- **Controller:** WP_REST_Application_Passwords_Controller
- **Source File:** class-wp-rest-application-passwords-controller.php
- **Endpoint:** `/wp-abilities/v1/application_passwords/{name}`
- **Methods:** GET
- **Type:** single

## Generated Tests

This test suite was automatically generated from the PHP controller.

### Test Coverage
- Authentication tests (401)
- Authorization tests (403)
- Valid requests (200)
- Invalid requests (404)
- Method validation (405)

## Running Tests

```bash
pytest api-tests/generated/test-application-password.py -v
```

---

*Auto-generated from class-wp-rest-application-passwords-controller.php*
