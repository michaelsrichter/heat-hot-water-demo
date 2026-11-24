# Contributing

This repo is either the **EPS demo template** itself, or a partner demo
generated from it — either way, it's an **EPS AI partner-facing "vibe-coded"
demo**. Before contributing, read [AGENTS.md](AGENTS.md) and the skills under
[.github/skills/](.github/skills/) — they are the authoritative standards.
Once a demo is scaffolded, full documentation lives in
[docs/](docs/README.md).

## Starting a new demo

If you're working from a fresh clone of the template (no `backend/`,
`frontend/`, or infra resources yet), open GitHub Copilot Chat and run
**`/new-demo`**, or just describe what you want to build. See the "Starting a
brand-new demo" section of [AGENTS.md](AGENTS.md) — Copilot interviews you
first, then scaffolds in a fixed order (docs → infra → backend → frontend →
devx → CI).

For an end-to-end build, select the **EPS Demo Builder** under
`.github/agents/`. Before handoff, run the **EPS Demo Release Reviewer** for a
read-only conformance and live-readiness verdict.

## Uniform CLI

Every EPS demo exposes the same four verbs:

```bash
make dev      # run the full stack locally
make test     # run all tests with coverage (sets FAKE_AI=1)
make lint     # lint + format check
make deploy   # azd up — deploy via Bicep
```

In VS Code, the **Run All** task (`.vscode/tasks.json`) starts the stack, and
**Debug All** (`.vscode/launch.json`, added once services exist) attaches
debuggers to every service.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/cli/azure/) + [azd](https://aka.ms/azd), signed in (`az login`)
- [GitHub CLI](https://cli.github.com/), signed in (`gh auth login`)
- Node.js, Python, and/or .NET — whichever the scaffolded stack uses

There are **no local emulators** — local dev hits real (dev-tier) Azure
resources via Managed Identity. Secrets come from Key Vault, never from
`.env` files.

## Workflow

1. Branch from `main`.
2. Make surgical changes — no drive-by refactors.
3. `make lint && make test` must pass locally. `make lint` also validates skill
   front matter, custom-agent discovery, `/new-demo` coverage, and local
   Markdown links.
4. Coverage gates once code exists: **backend ≥ 70%**, **frontend ≥ 60%**. CI
   enforces them.
5. CI runs with `FAKE_AI=1` so no real AI calls are made in pipelines.
6. Open a PR. CODEOWNERS review is required.

## Design rules (per `eps-demo-testing-solid`)

- Dependency-inject every external dependency (HTTP, storage, AI client,
  clock, randomness). No `new SomeClient()` inside business logic.
- Every AI call must be routable through the `FAKE_AI=1` fake.
- No hardcoded model names — model selection is config-driven
  (`config/models.json`).
- No secrets in source. Managed Identity first, Key Vault second.

## Commits & branches

- Small, focused commits with clear messages.
- Cite the skill you are complying with when it clarifies intent
  (e.g., "per `eps-demo-architecture`, ...").

## Architecture Decision Records

Material decisions — including deviations from a skill's default — are
captured as ADRs under `docs/adr/`. Add one when you knowingly diverge; see
[docs/adr/](docs/adr/) for the format and the template's own founding
decisions.
