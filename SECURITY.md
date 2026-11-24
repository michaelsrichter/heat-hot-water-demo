# Security Policy

This repository is a **template** for EPS AI partner-facing demos. Repos
generated from it are provided for demonstration purposes only and are not
official Microsoft products.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report suspected vulnerabilities to the Microsoft Security Response Center
(MSRC) at <https://msrc.microsoft.com/create-report> or by email to
[secure@microsoft.com](mailto:secure@microsoft.com). See the
[MSRC guidance](https://www.microsoft.com/msrc) for more detail.

For non-security bugs specific to a demo, open a normal GitHub issue in that
demo's repo.

## Security posture required of every demo built from this template

Per [`.github/skills/eps-demo-cost-security`](.github/skills/eps-demo-cost-security/SKILL.md)
and [`eps-demo-architecture`](.github/skills/eps-demo-architecture/SKILL.md):

- **Managed Identity** for all Azure dependencies that support it. No keys or
  connection strings committed to source.
- Any unavoidable third-party credential lives in **Azure Key Vault** (RBAC),
  never committed.
- **Content filters** enabled by default on any AI service.
- **No PII** collected; state (if any) uses an anonymous alias + GUID local
  profile.
- **Private Link** is the production-grade default; if a demo ships without it
  to move fast, that gap must be documented (see `docs/README.md`'s
  standards-compliance table) — not silently skipped.

Each generated demo documents its actual threat model, auth posture, secrets
handling, rate limiting, and privacy stance under `docs/security/` once
scaffolded (see [`eps-demo-docs`](.github/skills/eps-demo-docs/SKILL.md)).
