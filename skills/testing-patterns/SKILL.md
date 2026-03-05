---
name: testing-patterns
description: >
  This skill MUST be invoked when user says "write test", "test", "TDD", "unit test", "test coverage".
  SHOULD also invoke when creating any test file or test function.
  Do NOT use for 1C-specific testing — use 1c-test-runner skill instead.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Testing Patterns

Framework-agnostic principles for writing useful tests.

## AAA Structure

Every test: Arrange → Act → Assert. One assertion concept per test.

```python
def test_invoice_total_includes_tax():
    # Arrange
    invoice = Invoice(items=[Item(price=100)], tax_rate=0.2)
    # Act
    total = invoice.calculate_total()
    # Assert
    assert total == 120
```

## What to test

- **Happy path**: normal input, expected output
- **Edge cases**: empty input, zero, max value, single item
- **Error handling**: invalid input raises correct exception, error messages are meaningful
- **Boundary values**: off-by-one, type boundaries (int overflow, empty string vs None)

## What NOT to test

- Implementation details (private methods, internal state)
- Framework behavior (don't test that Django saves to DB — test your logic)
- Trivial getters/setters with no logic

## Test naming

Name describes behavior, not implementation:
- `test_user_cannot_login_with_wrong_password` — good
- `test_login_fail` — bad
- `test_check_password_method` — bad (tests implementation)

## Test isolation

- No shared mutable state between tests
- Each test sets up its own fixtures
- Tests must pass in any order
- Mock external I/O (HTTP, DB, filesystem) — test logic, not infrastructure

## Anti-patterns to avoid

- Brittle assertions: `assert result == "exact string with timestamp"`
- Sleep in tests: use mocks or event waiting instead
- Giant test functions: one behavior per test
- Commented-out tests: delete them
