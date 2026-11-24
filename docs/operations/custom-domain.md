# Custom domain

## Target

The production hostname is `strategy-heat.eps-demos.site`. It points to the
deployed Azure Container App. Deployment resource names and Azure resource IDs
stay in the authorized Azure subscription and are not committed.

## Current state

The custom domain is live as of 2026-11-24. Namecheap returns the required
CNAME and TXT records. Azure reports the managed certificate as `Succeeded` and
the hostname binding as `SniEnabled`.

The public HTTPS certificate is for `strategy-heat.eps-demos.site`. It was
issued by DigiCert and expires on 2027-05-24. The root page returns HTTP 200.
The health route returns the expected `available` practice status. HTTP returns
301 and redirects to HTTPS.

`eps-demos.site` is managed by Namecheap. It uses the
`dns1.registrar-servers.com` and `dns2.registrar-servers.com` name servers.
The custom name is a subdomain, so it needs a CNAME record. Public DNS checks
found no CAA record. No CAA change is needed now.

## Namecheap records

Create these records in the DNS provider for `eps-demos.site`:

| Type | Host | Value |
|---|---|---|
| CNAME | `strategy-heat` | Container App's generated FQDN |
| TXT | `asuid.strategy-heat` | Container App's custom-domain verification ID |

Use Namecheap's automatic time-to-live (TTL) value. Do not add an A or AAAA
record for `strategy-heat`. A CNAME must point directly to the Azure target.
Cloudflare proxying or another intermediate CNAME can prevent certificate
creation and renewal.

Read the generated values from Azure. Do not commit the resulting values to
the repository.

```powershell
$resourceGroup = azd env get-value RESOURCE_GROUP_NAME
$appName = azd env get-value SERVICE_APP_NAME
$environmentId = az containerapp show `
  --resource-group $resourceGroup `
  --name $appName `
  --query "properties.environmentId" `
  --output tsv
$environmentName = ($environmentId -split '/')[-1]

az containerapp show `
  --resource-group $resourceGroup `
  --name $appName `
  --query "properties.configuration.ingress.fqdn" `
  --output tsv

az containerapp show `
  --resource-group $resourceGroup `
  --name $appName `
  --query "properties.customDomainVerificationId" `
  --output tsv
```

## Check DNS

To recheck the public records:

```powershell
Resolve-DnsName strategy-heat.eps-demos.site CNAME
Resolve-DnsName asuid.strategy-heat.eps-demos.site TXT
```

## Add and bind the certificate

Bind a managed certificate after both records resolve. A managed certificate
is renewed by Azure. The app must stay running for creation and renewal checks.

```powershell
az containerapp hostname add `
  --resource-group $resourceGroup `
  --name $appName `
  --hostname "strategy-heat.eps-demos.site"

az containerapp hostname bind `
  --resource-group $resourceGroup `
  --name $appName `
  --hostname "strategy-heat.eps-demos.site" `
  --environment $environmentName `
  --validation-method CNAME
```

Save the certificate ID in the azd environment. This lets Bicep restore the
same binding in later deployments:

```powershell
$certificateId = az containerapp env certificate list `
  --resource-group $resourceGroup `
  --name $environmentName `
  --query "[?properties.subjectName=='strategy-heat.eps-demos.site'].id | [0]" `
  --output tsv

if ([string]::IsNullOrWhiteSpace($certificateId)) {
  throw "Azure has not issued the managed certificate yet."
}

azd env set AZURE_APP_CUSTOM_DOMAIN_NAME "strategy-heat.eps-demos.site"
azd env set AZURE_APP_CUSTOM_DOMAIN_CERTIFICATE_ID $certificateId
```

Also set the non-secret GitHub repository variable
`AZURE_APP_CUSTOM_DOMAIN_CERTIFICATE_ID` to the same value. The deploy workflow
stops if this value is missing. That protects the live binding from being
removed by a production deployment. Configure the value only in the production
repository's variable settings. Do not commit it.

## Verify

Check the Azure binding:

```powershell
az containerapp hostname list `
  --resource-group $resourceGroup `
  --name $appName `
  --output table
```

Then check public HTTPS:

```powershell
curl.exe --fail --show-error --location `
  "https://strategy-heat.eps-demos.site/health"
```

The custom domain is complete when public DNS matches the table, Azure shows
an `SniEnabled` binding, and the HTTPS health route returns an available
practice status.
