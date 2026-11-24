# Azure services

| Service | Purpose | Status |
|---|---|---|
| ADLS Gen2 Storage | Stores stable current files and dated archives for Strategy | Implemented in Bicep |
| Azure Container Apps | Hosts the review API and public Practice page | Prepared |
| Azure Container Registry | Stores the application image | Prepared |
| Application Insights | Records safe app operations | Prepared |
| Log Analytics | Stores storage, app, and deployment diagnostics | Prepared |
| Azure Budget | Sends actual and forecast cost alerts | Prepared |
| Microsoft Foundry project | Hosts the cited HPD briefing agent and model deployment | Deployed |

## Foundry briefing

The `hpd-review-agent` is a code-deployed hosted agent. It uses the Responses
protocol and the configured `gpt-5.4-mini` deployment.

Strategy Mosaic remains the source of metric definitions. The agent cannot
recalculate a Strategy metric. It can explain the supplied evidence, unknowns,
suggested follow-up, and linked HPD guidance.

The deployed demo calls `hpd-review-agent` through `FOUNDRY_AGENT_ENDPOINT`.
Local tests use the deterministic Practice provider. That fallback is visible
in the user interface and never pretends to be a live model response.

The agent is deployed as an active hosted agent version and the public app is
authorized with the Foundry Agent Consumer role. The agent identity has the
separate Cognitive Services OpenAI User role needed to call the model.

## ADLS controls

- Hierarchical namespace is enabled.
- Anonymous blob access is disabled.
- Shared storage key access is disabled.
- The app and developer receive Storage Blob Data Contributor only where they
  need to write.
- External Strategy connector credentials are configured outside the repository.

