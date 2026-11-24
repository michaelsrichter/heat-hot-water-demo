# Rollback

Keep the previous Container App revision and ADLS archive until a new import
passes the live journey.

1. Open the Container App revisions page.
2. Identify the last known-good image and rule version.
3. Route traffic to that revision.
4. Confirm `/health` and the critical practice flow.
5. Record the failed image and trace ID in the build journal.

For data rollback, copy the approved `archive/<date>/` files into `current/`
and refresh Strategy. Restore the same `rule_version`, dashboard, and manifest
together. Never mix an old archive with a new rule version.

