# Operations

Fill in as the demo is scaffolded and deployed. Required per
[`eps-demo-docs`](../../.github/skills/eps-demo-docs/SKILL.md):

- **deploy.md** — today: `make deploy` runs `azd up` (see
  [adr/0002](../adr/0002-azd-as-deploy-standard.md)); update once
  `azure.yaml` lists real services.
- **custom-domain.md** — exact DNS records and Azure Container Apps certificate
  steps for `strategy-heat.eps-demos.site`.
- **rollback.md** — how to revert a bad deploy.
- **troubleshooting.md** — common local-dev and deploy issues, including how
  to get RBAC access to any shared dev Azure resources.
- **strategy-mcp-setup.md** — enable Strategy's read-only Mosaic MCP token and
  connect it to the Foundry toolbox.

## CI/CD status

`.github/workflows/ci.yml` has guarded placeholder jobs (bicep validation,
secret scanning, a `frontend` job gated on `frontend/package.json`, a
`backend-dotnet` job gated on a `.sln`/`.csproj`) — flesh these out, or
swap `backend-dotnet` for the equivalent Python/Node job, once the stack is
chosen. `.github/workflows/deploy.yml` is inert until
`vars.AZURE_ENV_NAME` and federated OIDC credentials are configured
(`azd pipeline config` — see https://aka.ms/azd-github-actions).
