// Subscription-scoped azd entrypoint (per eps-demo-architecture): `azd up`
// brings up a brand-new environment from scratch, including the resource
// group itself. Deliberately minimal — compute (Static Web Apps + Functions,
// Container Apps, etc.) and any data services are an architect/demo decision
// made when the app is scaffolded, not something this template presupposes
// (see docs/adr/0004-stack-agnostic-template.md). This file only wires the
// guardrails every demo needs from day one: the resource group, tags, and a
// budget — extended in resources.bicep.
targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('azd environment name — also used to derive resource names.')
param environmentName string

@description('Azure region for all resources.')
param location string

@description('Monthly budget (USD) for the resource group; drives cost alerts (eps-demo-cost-security).')
param monthlyBudgetUsd int = 50

@description('Email for budget + cost alerts (set by infra/hooks/preprovision.*, defaults to the deployer).')
param budgetContactEmail string

@description('Microsoft Entra object ID for the signed-in developer.')
param principalId string

@description('Grant the signed-in developer the same least-privilege roles as the application.')
param grantDeveloperAccess bool = true

@description('Desired production hostname. It is bound after DNS validation and managed-certificate creation.')
param appCustomDomainName string = 'strategy-heat.eps-demos.site'

@description('Optional managed-certificate resource ID. Supplying it enables the Container Apps hostname binding.')
param appCustomDomainCertificateId string = ''

@description('Partner short name, or "none". Never a full partner/customer name — this flows into resource tags only, never the public UI (eps-demo-compliance).')
param partnerName string = 'none'

var ownerAlias = split(budgetContactEmail, '@')[0]

var tags = {
  'azd-env-name': environmentName
  demo: 'true'
  owner: ownerAlias
  partner: partnerName
  'cost-center': 'eps-ai-demos'
}

resource rg 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module resources 'resources.bicep' = {
  name: 'resources'
  scope: rg
  params: {
    location: location
    tags: tags
    monthlyBudgetUsd: monthlyBudgetUsd
    budgetContactEmail: budgetContactEmail
    principalId: principalId
    grantDeveloperAccess: grantDeveloperAccess
    appCustomDomainName: appCustomDomainName
    appCustomDomainCertificateId: appCustomDomainCertificateId
  }
}

output RESOURCE_GROUP_NAME string = rg.name
output AZURE_LOCATION string = location
output APPLICATIONINSIGHTS_CONNECTION_STRING string = resources.outputs.appInsightsConnectionString
output LOG_ANALYTICS_WORKSPACE_ID string = resources.outputs.logAnalyticsWorkspaceId
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.containerRegistryEndpoint
output SERVICE_APP_NAME string = resources.outputs.containerAppName
output SERVICE_APP_URI string = resources.outputs.containerAppUri
output APP_CUSTOM_DOMAIN_NAME string = appCustomDomainName
output APP_CUSTOM_DOMAIN_BINDING_TYPE string = resources.outputs.appCustomDomainBindingType
output APP_CUSTOM_DOMAIN_VERIFICATION_ID string = resources.outputs.appCustomDomainVerificationId
output DATA_STORAGE_ACCOUNT_NAME string = resources.outputs.dataStorageAccountName
output DATA_STORAGE_DFS_ENDPOINT string = resources.outputs.dataStorageDfsEndpoint
output DATA_CONTAINER_NAME string = resources.outputs.dataContainerName
output AZURE_AI_ACCOUNT_NAME string = resources.outputs.aiAccountName
output AZURE_AI_PROJECT_NAME string = resources.outputs.aiProjectName
output AZURE_AI_PROJECT_ENDPOINT string = resources.outputs.aiProjectEndpoint
output FOUNDRY_PROJECT_ENDPOINT string = resources.outputs.aiProjectEndpoint
