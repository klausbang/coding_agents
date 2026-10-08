# Infrastructure

Owned by the devops-engineer. There is one Terraform (or Bicep) stack per environment (`dev`, `staging`, `prod`), and the stacks differ only in their variables.

Each environment needs at least:
- a container service running the app image;
- managed PostgreSQL with automated backups and point-in-time restore;
- a secret store, injected as environment variables;
- a `/health` health check;
- log aggregation.
