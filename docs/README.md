# Documentation

The **`docs/` folder is the single source of truth** for a demo's
documentation, per
[`eps-demo-docs`](../.github/skills/eps-demo-docs/SKILL.md). The root
[README](../README.md) is only a short on-ramp.

Write every page in plain language, per
[`eps-demo-plain-language`](../.github/skills/eps-demo-plain-language/SKILL.md):
short sentences, each term defined on first use, the "why" explained, and a
concrete example where it helps. Keep the technical accuracy.

This template ships `docs/` pre-structured but mostly empty — `/new-demo`
(or you, by hand) fills each area in as the demo is scaffolded. Don't delete
sections for parts the demo doesn't use; write a line explaining why it's
not applicable instead, so the map stays complete.

## Served HTML guides

The frontend build generates these public pages from this folder and the current
source files:

| Page | Purpose |
|---|---|
| [Azure architecture](/docs/architecture.html) | data path, Azure services, and Strategy boundary |
| [Foundry integration](/docs/foundry-integration.html) | hosted agent and planned Strategy MCP path |
| [Strategy interface views](/docs/strategy-screenshots.html) | model, dashboard, and refresh rebuilds |
| [Security and networking](/docs/security-networking.html) | identity, data, secrets, and known network gaps |
| [Azure and AI costs](/docs/azure-ai-costs.html) | current cost drivers and scale measures |
| [Code tour](/docs/code-tour.html) | source-extracted request and Foundry response path |

## Map

| Area | Contents |
|---|---|
| [architecture/overview.md](architecture/overview.md) | Strategy-first ADLS data path and limits |
| [security/threat-model.md](security/threat-model.md) | threat model, identity, secrets, and privacy |
| [api/](api/README.md) | optional OpenAPI contract |
| [cost/](cost/README.md) | cost to run today, cost at scale |
| [operations/](operations/README.md) | deploy, rollback, troubleshooting |
| [adr/](adr/) | Architecture Decision Records — includes this template's own founding decisions |
| [telemetry/](telemetry/README.md) | every event the app emits |
| [health/](health/README.md) | dependency status, probe semantics, caching, readiness |
| [code-tour.md](code-tour.md) | request paths, trust boundaries, current source excerpts, and tests |
| [build-journal.md](build-journal.md) | decisions, dead ends, known gaps (optional) |
| [demo-script.md](demo-script.md) | presenter-ready business walkthrough from Strategy to Foundry and owner plans |

## Standards compliance at a glance

Fill this in honestly as the demo takes shape — per AGENTS.md, a rule can be
knowingly deferred but never silently. Start from the template's own
defaults (see `docs/adr/`) and update the status as the real app diverges.

| Standard | Status | Notes |
|---|---|---|
| Hosted in Azure | ✅ | The Foundry agent and public Container App are deployed in the demo resource group |
| Bicep IaC | ✅ | [`infra/`](../infra/) — resource group, tags, budget, App Insights |
| Telemetry and dashboards in Azure Monitor | ⚠️ | Starter workbook in [`infra/dashboards/`](../infra/dashboards/demo-overview.workbook.json); add OpenTelemetry and diagnostic settings as the stack is built, per [`eps-demo-observability`](../.github/skills/eps-demo-observability/SKILL.md) |
| Foundry Evaluations (opt-in) | — | Not built by default. Add only when asked, per [`eps-demo-evaluations`](../.github/skills/eps-demo-evaluations/SKILL.md) |
| Managed Identity, no keys | ✅ | Azure ingestion uses Managed Identity, anonymous Blob access is disabled, and shared-key storage authentication is disabled |
| Config-driven models | ✅ | `config/models.json` defines the Foundry briefing role; agent code reads the deployment from the environment |
| Content filters on | ✅ | The Foundry model deployment uses the platform `Microsoft.DefaultV2` policy |
| Alias + GUID, no PII | — | N/A until the app has state |
| "Demo only" indicator | ✅ | Visible above the fold and in the footer |
| `/docs` single source of truth | ✅ | This folder |
| Private Link | ⚠️ | The public app uses public Azure endpoints; all data access still requires Microsoft Entra authorization |
| Rate limiting | ⚠️ | Local in-memory Practice limit exists; shared production storage is required |
| CI coverage gates (BE ≥ 70% / FE ≥ 60%) | ✅ | Backend and frontend thresholds are enforced in the test configuration |
| Budget alerts in Bicep | ✅ | `Microsoft.Consumption/budgets` in `infra/resources.bicep` |
| Long-lived production readiness | ⚠️ | Apply [`eps-demo-production-readiness`](../.github/skills/eps-demo-production-readiness/SKILL.md) when a generated demo is shared or long-lived |
| Plain-language public UI and docs | ✅ | Public labels and docs use short, direct language |
| Strategy-first governed data path | ✅ | ADLS refresh, Strategy relationships, KPI semantics, and the public process are configured |
| Cited Foundry briefing | ✅ | Hosted agent version 4 is active and the public app returns live cited owner plans |

## Architecture Decision Records

ADRs use the tiny format from `eps-demo-docs`:

```
# ADR NNNN: <title>
- Status: accepted | superseded by ADR-XXXX
- Date: YYYY-MM-DD
- Context: 2–4 sentences
- Decision: 1–2 sentences
- Consequences: bullets — both good and bad
```

| ADR | Title | Status |
|---|---|---|
| [0001](adr/0001-use-bicep.md) | Use Bicep for IaC | accepted |
| [0002](adr/0002-azd-as-deploy-standard.md) | Azure Developer CLI (azd) as the deploy standard | accepted |
| [0003](adr/0003-private-link-opt-in-by-default.md) | Private Link opt-in by default, documented gap otherwise | accepted |
| [0004](adr/0004-stack-agnostic-template.md) | Template stays stack-agnostic — no prebuilt app or compute | accepted |
| [0005](adr/0005-public-repo-by-default.md) | Demo repos are public by default | accepted |
| [0006](adr/0006-long-lived-demo-readiness.md) | Long-lived demos require an operational readiness baseline | accepted |
| [0007](adr/0007-fabric-fallback-evaluation.md) | Evaluate Fabric and keep an external SaaS fallback | superseded |
| [0008](adr/0008-adls-strategy-data-path.md) | Use ADLS Gen2 as the Strategy data source | accepted |
| [0009](adr/0009-strategy-shared-key-fallback.md) | Historical Strategy Shared Key fallback | superseded by [0011](adr/0011-managed-identity-only-public-infrastructure.md) |
| [0010](adr/0010-foundry-briefing-agent.md) | Use a hosted agent that cannot recalculate Strategy metrics | accepted |
| [0011](adr/0011-managed-identity-only-public-infrastructure.md) | Keep the public deployment identity-only | accepted |

Add one per material decision your demo makes — especially anywhere it
diverges from a skill default.
