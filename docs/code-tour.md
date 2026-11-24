# Foundry integration code tour

The live demo uses two separate jobs.

Strategy Mosaic defines the numbers. Microsoft Foundry explains the supplied
facts and official guidance. A staff member still checks every suggested action.

## Current path

The public review currently uses the hosted Foundry agent with a governed ADLS
snapshot. It does not depend on a live Strategy Model Context Protocol (MCP)
call.

1. The browser sends one saved scenario and one service area.
2. The review coordinator creates synthetic building review items.
3. The API reads the governed pipeline manifest.
4. The API sends the manifest, review items, and citations to Foundry.
5. The hosted agent returns a short cited briefing.
6. The browser shows the briefing only after the backend receives it.

The Strategy MCP connection, OAuth consent, and Foundry toolbox exist. The
signed-in Strategy user cannot yet see the Heat and Hot Water Review Model.
Until that model is exposed, the public page remains on the governed snapshot.

## 1. The browser starts a bounded review

The frontend never accepts an arbitrary model prompt. It sends a saved
scenario ID, an optional service area, and a random browser session ID.

{{snippet:frontend-request}}

## 2. The API joins practice records with Strategy facts

The API first creates the review list from the selected saved scenario. It then
loads the same pipeline manifest that powers the Strategy KPI cards.

{{snippet:review-route}}

This is the point where the governed values and the synthetic building records
meet. The public endpoint does not read raw ADLS files.

## 3. The backend selects live Foundry or Practice

The briefing provider is deterministic during local testing or CI. In the
deployed environment, a configured `FOUNDRY_AGENT_ENDPOINT` selects the live
hosted agent.

{{snippet:provider-selection}}

Practice output is labeled. A missing Foundry endpoint does not pretend to be a
live model call.

## 4. The API sends governed evidence, not raw source rows

The live provider sends the pipeline contract and review result to the hosted
agent's Responses endpoint. The caller's authorization token comes from Azure
managed or developer credentials.

{{snippet:live-provider}}

The request includes:

- Strategy KPI values and approved object names;
- the rule version and source dates;
- synthetic building review items;
- owner teams and service areas; and
- approved citations.

It does not include a resident name, apartment, address, or raw 311 resolution
text.

## 5. The hosted agent explains the evidence

The agent service exposes the Responses protocol at `/responses`. It keeps the
instructions in code and reads the model deployment from environment
configuration.

{{snippet:agent-instructions}}

{{snippet:agent-live-call}}

The instructions prevent the model from recalculating Strategy metrics or
choosing an enforcement action. The model deployment remains config-driven.

## 6. The API returns one response shape

The Foundry agent returns a Responses payload. The backend extracts the first
assistant text block and combines it with citations from the review items.

{{snippet:response-parser}}

The public UI renders the provider name, output mode, briefing, and citations.
This lets a visitor distinguish Practice from a live Microsoft Foundry response.

## What changes when Strategy MCP is live

The planned branch is small:

1. A Strategy content owner publishes the Heat and Hot Water Review Model to the
   MCP-enabled project.
2. Foundry's `strategy-tools` toolbox is attached to the hosted agent.
3. The agent calls `get_projects`, `get_models` or `get_mosaic_models`,
   `get_semantics`, and `query`.
4. The agent uses the live Mosaic result before any snapshot value.
5. The output names the live MCP query as the source of current counts.

The existing request and response shapes do not need to change. Update the
code-tour screenshots and this page when the real MCP model is available.

## 7. The rest of the data path

`backend/app/ingest_adls.py` reads the three public NYC sources, applies a
privacy allowlist, preserves each source grain, and writes four stable Strategy
CSV folders plus `current/manifest.json` and a dated archive.

`infra/resources.bicep` creates ADLS Gen2 with anonymous access disabled. It
uses Managed Identity for Azure jobs and disables storage shared-key
authentication. Any external Strategy connector is configured by the deployment
operator outside this public repository.

`strategy/mosaic-contract.yaml` defines table grains, the shared model key
`building_id`,
the Borough-to-Building hierarchy, distinct-count measures, and the rule version.

`backend/app/pipeline.py` reads the manifest. The frontend renders all seven
steps: sources, preparation, storage, Strategy meaning, dashboard, Foundry
briefing, and staff review.

## Tests

`backend/tests/test_adls_ingest.py` checks the privacy allowlist, distinct
complaint count, building grain, rule state, and seven-step manifest.

`backend/tests/test_review.py` checks the bounded review request, citation
shape, rate limit, and briefing response.

`frontend/src/App.test.tsx` checks the seven-step path and the visible
Practice or live briefing behavior.
