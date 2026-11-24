# Telemetry

`events.md` must enumerate **every event** the app sends, per
[`eps-demo-docs`](../../.github/skills/eps-demo-docs/SKILL.md):

- Event name
- Trigger
- Properties (and whether each is scrubbed/anonymous)
- Destination (App Insights, Clarity, etc.)

App Insights + Log Analytics are already provisioned in
[`infra/resources.bicep`](../../infra/resources.bicep) — wire whatever
compute gets added to send telemetry there. Baseline events expected by
`eps-demo-repo-hygiene`: page view, AI call, model selection.
