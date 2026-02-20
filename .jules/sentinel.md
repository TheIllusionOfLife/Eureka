## 2025-11-10 - Missing HSTS Header
**Vulnerability:** The web backend was missing the `Strict-Transport-Security` (HSTS) header.
**Learning:** Security headers are often overlooked in default framework configurations. Middleware setup needs to be explicitly verified against a security checklist (e.g., OWASP).
**Prevention:** Implement automated tests that verify the presence and correct configuration of all recommended security headers (HSTS, CSP, X-Frame-Options, etc.) as part of the CI pipeline.
