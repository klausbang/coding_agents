# Tests: one folder per V-model level

| Folder | V-level | Owner | Marker |
|---|---|---|---|
| `unit/` | R4 | backend-developer (`unit/ui/`: frontend-developer, `unit/models/`: database-engineer) | none |
| `integration/` | R3 | verification-engineer | `@pytest.mark.integration` |
| `contract/` | R3 | verification-engineer | `@pytest.mark.contract` |
| `system/` | R2 | verification-engineer | `@pytest.mark.system` |
| `security/` | R2 | security-engineer | `@pytest.mark.security` |
| `acceptance/` | R1 | validation-engineer | Gherkin tags `@VAL-NNN @AC-NNN.N` |

Traceability: mark each test with the acceptance criterion it verifies, `@pytest.mark.ac("AC-<story>.<n>")`, and, for verification tests, with its test case ID, `@pytest.mark.tc("TC-<nnn>")`. `python tools/trace_check.py` builds the matrix from these markers.
