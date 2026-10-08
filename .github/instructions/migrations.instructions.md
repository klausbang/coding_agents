---
applyTo: "migrations/**"
---

# Alembic migrations

- Only the database-engineer writes migrations. Generate them with `flask --app wsgi db migrate -m "<message>"`, then review and edit the result.
- Every migration has a working `downgrade()`. Verify the round trip upgrade → downgrade → upgrade on a fresh PostgreSQL.
- Expand → migrate → contract: add columns as nullable, backfill, then add the constraint. The previous app version must keep working during a deploy.
- Destructive changes (drop or rename, narrowing a type) need explicit approval at gate G2.
- No environment-dependent values or `now()` evaluated in Python at migration time.
