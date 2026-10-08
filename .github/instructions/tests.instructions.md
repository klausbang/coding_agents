---
applyTo: "tests/**"
---

# Tests (right leg of the V)

- Folder = V-level: `unit/` (R4), `integration/` and `contract/` (R3), `system/` and `security/` (R2), `acceptance/` (R1). See `tests/README.md` for who owns each folder.
- Derive tests from the acceptance criteria and the contract, not from the implementation.
- Mark traceability on every test: `@pytest.mark.ac("AC-NNN.N")`. Verification tests also get `@pytest.mark.tc("TC-NNN")`. Gherkin scenarios get the tags `@VAL-NNN @AC-NNN.N`.
- Integration tests run against real PostgreSQL through `TEST_DATABASE_URL`, and skip with a clear reason if it is not set.
- Build test data with the factory-boy factories in `tests/factories.py`. Never use production data.
- Never weaken an assertion or skip a failing test to get a green build. File a `BUG-NNN` instead.
