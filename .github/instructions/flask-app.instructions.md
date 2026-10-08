---
applyTo: "app/**/*.py"
---

# Flask application code

- Layering: `app/blueprints/` holds HTTP only (parse and validate, call a service, map to a response). `app/services/` holds business rules and transactions, with no `flask.request` in services. `app/models/` holds persistence and is owned by the database-engineer.
- Responses and status codes follow `project/interfaces/openapi.yaml` exactly. Errors use the `Problem` schema (RFC 9457).
- Validate all input at the HTTP edge and reject unknown fields. Check authorization in the service layer against `project/architecture/security/authz.md`.
- Use the SQLAlchemy ORM or `text()` with bound parameters. Never build SQL with string formatting.
- Read configuration through `app/config.py` (environment variables). No hard-coded secrets or URLs.
- Use UTC time (`datetime.now(UTC)`). Log with `current_app.logger`, never with secrets or personal data.
- Use type hints on public functions. Code must be clean under `ruff` and `mypy`.
