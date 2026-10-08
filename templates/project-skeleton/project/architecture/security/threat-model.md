# Threat model — {{PROJECT_NAME}}

<!-- Owned by the security-engineer. Add one section per feature or sprint. -->

## Baseline controls
| Control | Status |
|---|---|
| CSRF on state-changing forms | planned |
| Session cookies Secure / HttpOnly / SameSite=Lax | configured in `app/config.py` |
| Security headers (CSP, HSTS, nosniff, frame-ancestors) | planned |
| Rate limiting on authentication | planned |
| Secrets only from environment / key vault | in place |
