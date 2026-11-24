# Connect Strategy Mosaic MCP in Microsoft Foundry

## Values for the Add Model Context Protocol tool dialog

| Foundry field | Value |
|---|---|
| Name | `strategy-mosaic-mcp` |
| Remote MCP Server endpoint | `https://studio.strategy.com/collaboration/mcp/mosaic` |
| Authentication | `OAuth Identity Passthrough` |
| Client ID | The OAuth Client ID supplied by the Strategy environment |
| Client secret | The matching OAuth Client Secret supplied by the Strategy environment |
| Token URL | `https://studio.strategy.com/collaboration/token` |
| Auth URL | `https://studio.strategy.com/collaboration/authorize` |
| Refresh URL | `https://studio.strategy.com/collaboration/token` |
| Scopes | `offline_access mcp:stream` |

Use the user-visible Strategy environment URL
`https://studio.strategy.com` when Foundry asks for a separate Strategy MCP
base address.

Do not use a Strategy user name, password, tenant code, or API token in the
Client ID or Client Secret fields.

## Callback allowlist

The Foundry connection created for this project uses:

`https://global.consent.azure-apim.net/redirect/7562f5510708426eacbf4e931db046ad`

A Strategy administrator should allow that exact URL, or the supported
wildcard:

`https://global.consent.azure-apim.net/redirect/*`

They add it in Strategy Workstation under **Environment Properties > Library >
Model Context Protocol for Agent > Callback URL**, save, and restart the
Library/Collaboration service if required.

`global.consent.azure-apim.net` is Microsoft's OAuth consent broker. It
receives the authorization code from Strategy and passes the resulting
connection token to Foundry. It does not store or query HPD data.

## Foundry connection status

The `strategy-mosaic-mcp` connection and `strategy-tools` toolbox are created.
OAuth consent is complete. Authenticated `tools/list`, `get_projects`, and
`get_models` calls succeed.

The signed-in Strategy user can currently access:

- project: `Strategy Showcase`;
- model: `Retail Orders Sales Performance Model (global)`.

The MCP server does not currently expose the **Heat and Hot Water Review
Model** to this user. A Strategy content owner or administrator must:

1. publish that Mosaic model in the Strategy Showcase project, or move an
   equivalent model there;
2. certify it for MCP access; and
3. grant the consented Strategy user view access to it.

## Verify

From the repository root:

```powershell
$env:AZURE_DEV_USER_AGENT = "microsoft_foundry_skill"
azd ai agent invoke hpd-review-agent --new-session "Use Strategy Mosaic MCP to list the Heat and Hot Water model metrics and return the current Open Complaints and Open Candidate Violations values."
```

A successful response names the **Heat and Hot Water Review Model**, reads its
governed semantics, and cites Mosaic MCP as the source of the current values.

Until the model is exposed, keep the public demo on the governed ADLS snapshot.
The hosted agent remains healthy and uses the snapshot; the Foundry toolbox is
ready for a user-authenticated client.
