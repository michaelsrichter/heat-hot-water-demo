# Architecture

Fill in once the demo's stack is chosen. Required per
[`eps-demo-docs`](../../.github/skills/eps-demo-docs/SKILL.md):

- **overview.md** — what the app does, the value to the partner, the audience.
- **diagram.md** — at least one C4-style (or equivalent) diagram showing
  components, trust boundaries, and Azure services in use. Mermaid in
  markdown is preferred (renders on GitHub); use Excalidraw for richer
  diagrams and check in the `.excalidraw` file alongside an exported PNG.
- **azure-services.md** — what's used and why.
- **data-flow.md** — how data moves through the system.

Today this repo only has the guardrails in [`infra/`](../../infra/)
(resource group, tags, budget, App Insights/Log Analytics) — see
[adr/0004](../adr/0004-stack-agnostic-template.md). There's nothing to
diagram yet.
