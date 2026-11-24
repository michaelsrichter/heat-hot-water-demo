# Deploy

The source of truth for Azure resources is `infra/main.bicep`.

```bash
make deploy
```

The target Azure environment creates:

- ADLS Gen2 with hierarchical namespace;
- the `heat-hot-water` container;
- Storage Blob role-based access for the app and developer;
- a storage diagnostic setting;
- Storage shared-key access disabled;
- Container Registry and Container Apps;
- Log Analytics and Application Insights; and
- a resource-group budget;
- a Microsoft Foundry account and project; and
- the configured `gpt-5.4-mini` model deployment.

## Custom domain

The production hostname is `https://strategy-heat.eps-demos.site`. Azure
Container Apps uses a free managed certificate. The certificate is bound only
after the public DNS records exist and Azure has issued the certificate.

The Bicep configuration reads the hostname and certificate resource ID from
`AZURE_APP_CUSTOM_DOMAIN_NAME` and
`AZURE_APP_CUSTOM_DOMAIN_CERTIFICATE_ID`. Production deployment stops if the
certificate ID is missing. This prevents a later deployment from removing the
live HTTPS binding.

See [Custom domain](custom-domain.md) for the exact DNS records, certificate
commands, and verification steps.

After deployment:

```bash
make ingest
```

`make ingest` writes:

- stable `current/` CSV files;
- `current/manifest.json`; and
- matching `archive/<date>/` copies.

Then complete the Strategy ADLS connector steps in
`manual-strategy-setup.md`.

## Deploy the briefing agent

Use the Azure Developer CLI with the same tenant and subscription as Azure CLI:

1. Provision the Foundry account, project, and model.
2. Deploy the `hpd-review-agent` code service.
3. Copy the generated `AGENT_HPD_REVIEW_AGENT_RESPONSES_ENDPOINT` value into
   `FOUNDRY_AGENT_ENDPOINT` for the public app.
4. Clear `FAKE_AI=1` in the deployed app only after a live health and citation
   smoke test succeeds.

The current environment is live. The Foundry project, model deployment, hosted
agent, and public app are deployed. The live public API review returns
`briefing.mode: live`.

## Storage authentication

The public deployment uses Microsoft Entra managed identity. The storage
account does not allow shared-key authentication. Any external Strategy
connector must be configured and governed outside the public repository.

