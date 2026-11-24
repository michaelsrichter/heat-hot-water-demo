// Resource-group-scoped guardrails: budget + observability. Add compute
// (Static Web Apps + Functions, Container Apps, etc.) and data services here
// once the demo's stack is chosen — see AGENTS.md / eps-demo-architecture.
//
// When you add the first Azure resource with data-plane RBAC (storage,
// Cosmos, AI Foundry, ...): add a `principalId` / `principalType` /
// `grantDeveloperAccess` param trio here and on main.bicep (wire from
// AZURE_PRINCIPAL_ID — already derived by infra/hooks/preprovision.*), plus a
// shared role-assignment module invoked once for the app's managed identity
// and once for the developer principal, so the two grants can never drift
// (eps-demo-architecture). Keep Private Link opt-in by default on whatever
// you add (docs/adr/0003-private-link-opt-in-by-default.md).
targetScope = 'resourceGroup'

@description('Location for all resources.')
param location string

@description('Tags applied to every resource (demo/owner/partner/cost-center + azd-env-name).')
param tags object

@description('Monthly budget (USD) for this resource group.')
param monthlyBudgetUsd int

@description('Email for budget + cost alerts.')
param budgetContactEmail string

@description('Microsoft Entra object ID for the signed-in developer.')
param principalId string

@description('Grant the developer the same AcrPull access as the deployed app when true.')
param grantDeveloperAccess bool = true

@description('Desired production hostname for the app.')
param appCustomDomainName string = ''

@description('Managed-certificate resource ID. Leave empty until DNS validation is complete.')
param appCustomDomainCertificateId string = ''

@description('Start date for the budget period (first of month). Left as a param so it is computed once at first deploy, not recomputed (and invalidated) on every redeploy.')
param budgetStartDate string = utcNow('yyyy-MM-01')

var resourceToken = uniqueString(resourceGroup().id)
var appInsightsName = 'appi-${resourceToken}'
var logAnalyticsName = 'log-${resourceToken}'
var registryName = 'acr${resourceToken}'
var appIdentityName = 'id-app-${resourceToken}'
var containerEnvironmentName = 'cae-${resourceToken}'
var containerAppName = 'ca-${resourceToken}'
var storageAccountName = 'st${resourceToken}'
var dataContainerName = 'heat-hot-water'
var aiAccountName = 'aif-${resourceToken}'
var aiProjectName = 'hpd-heat-hot-water'
var appCustomDomainBound = !empty(appCustomDomainName) && !empty(appCustomDomainCertificateId)
var acrPullRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7f951dda-4ed3-4680-a7ca-43fe172d538d'
)
var storageBlobContributorRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)
var cognitiveServicesOpenAIUserRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
)
var foundryAgentConsumerRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'eed3b665-ab3a-47b6-8f48-c9382fb1dad6'
)

// ------------------------------------------------------------------ Budget
// Cost guardrail per eps-demo-cost-security — wired up regardless of what
// else this demo needs.
resource budget 'Microsoft.Consumption/budgets@2023-05-01' = {
  name: 'budget-${resourceGroup().name}'
  properties: {
    category: 'Cost'
    amount: monthlyBudgetUsd
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: budgetStartDate
    }
    notifications: {
      actual_80pct: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: [budgetContactEmail]
      }
      forecasted_100pct: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: [budgetContactEmail]
      }
    }
  }
}

// ------------------------------------------------------------ Observability
// App Insights + Log Analytics are compute-agnostic — point whatever compute
// gets added (Functions, Container Apps, App Service, ...) at these
// (eps-demo-repo-hygiene: "App Insights with PII scrubbed").
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ------------------------------------------------------------ Microsoft Foundry
resource aiAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: aiAccountName
  location: location
  tags: tags
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: aiAccountName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  name: aiProjectName
  parent: aiAccount
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'HPD Heat and Hot Water'
    description: 'Plain-language heat and hot-water complaint review demo.'
  }
  dependsOn: [
    aiModel
  ]
}

resource aiModel 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  name: 'gpt-5-4-mini'
  parent: aiAccount
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-5.4-mini'
      version: '2026-03-17'
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: appIdentityName
  location: location
  tags: tags
}

// ADLS Gen2 is the system of record for generated Strategy files.
// The app uses Microsoft Entra authorization and a managed identity.
resource dataStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    isHnsEnabled: true
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

resource dataBlobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: dataStorage
}

resource dataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: dataContainerName
  parent: dataBlobService
  properties: {
    publicAccess: 'None'
    metadata: {
      purpose: 'strategy-file-storage-source'
      ruleVersion: 'adls-strategy-0.1'
    }
  }
}

resource storageDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: dataBlobService
  properties: {
    workspaceId: logAnalytics.id
    logAnalyticsDestinationType: 'Dedicated'
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// -------------------------------------------------------------- Container app
resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: registryName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource registryDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: registry
  properties: {
    workspaceId: logAnalytics.id
    logAnalyticsDestinationType: 'Dedicated'
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  tags: union(tags, {
    'azd-service-name': 'app'
  })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
        customDomains: appCustomDomainBound
          ? [
              {
                name: appCustomDomainName
                bindingType: 'SniEnabled'
                certificateId: appCustomDomainCertificateId
              }
            ]
          : null
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: appIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'app'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
            {
              name: 'ADLS_ACCOUNT_URL'
              value: dataStorage.properties.primaryEndpoints.blob
            }
            {
              name: 'ADLS_CONTAINER'
              value: dataContainerName
            }
            {
              name: 'ADLS_MANIFEST_PATH'
              value: 'current/manifest.json'
            }
            {
              name: 'OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT'
              value: 'false'
            }
            {
              name: 'AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED'
              value: 'false'
            }
            {
              name: 'FOUNDRY_AGENT_ENDPOINT'
              value: 'https://${aiAccount.name}.services.ai.azure.com/api/projects/${aiProject.name}/agents/hpd-review-agent/endpoint/protocols/openai/responses?api-version=v1'
            }
            {
              name: 'FAKE_AI'
              value: '0'
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: appIdentity.properties.clientId
            }
            {
              name: 'STRATEGY_MCP_MODE'
              value: 'mock'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }

  }
  dependsOn: [
    appAcrPull
  ]
}

resource appAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, appIdentity.id, acrPullRoleId)
  scope: registry
  properties: {
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRoleId
  }
}

resource developerAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (grantDeveloperAccess) {
  name: guid(registry.id, principalId, acrPullRoleId)
  scope: registry
  properties: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: acrPullRoleId
  }
}

resource appFoundryAgentConsumer 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiAccount.id, appIdentity.id, foundryAgentConsumerRoleId)
  scope: aiAccount
  properties: {
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: foundryAgentConsumerRoleId
  }
}

resource developerAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (grantDeveloperAccess) {
  name: guid(aiAccount.id, principalId, cognitiveServicesOpenAIUserRoleId)
  scope: aiAccount
  properties: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: cognitiveServicesOpenAIUserRoleId
  }
}

resource appStorageAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(dataStorage.id, appIdentity.id, storageBlobContributorRoleId)
  scope: dataStorage
  properties: {
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobContributorRoleId
  }
}

resource developerStorageAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (grantDeveloperAccess) {
  name: guid(dataStorage.id, principalId, storageBlobContributorRoleId)
  scope: dataStorage
  properties: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: storageBlobContributorRoleId
  }
}

// -------------------------------------------------------------- Dashboards
// Starter Azure Workbook (free). infra/dashboards/*.workbook.json is the one
// canonical source: export portal edits back into that file
// (eps-demo-observability). When you add Azure resources, also give each one a
// diagnostic setting that points at logAnalytics.
var workbookJson = replace(
  replace(loadTextContent('dashboards/demo-overview.workbook.json'), '__APP_INSIGHTS_ID__', appInsights.id),
  '__LOG_ANALYTICS_ID__',
  logAnalytics.id
)

resource overviewWorkbook 'Microsoft.Insights/workbooks@2023-06-01' = {
  name: guid(resourceGroup().id, 'demo-overview-workbook')
  location: location
  tags: tags
  kind: 'shared'
  properties: {
    displayName: 'Demo overview'
    category: 'workbook'
    sourceId: appInsights.id
    serializedData: workbookJson
    version: '1.0'
  }
}

output appInsightsConnectionString string = appInsights.properties.ConnectionString
output logAnalyticsWorkspaceId string = logAnalytics.id
output overviewWorkbookId string = overviewWorkbook.id
output containerRegistryEndpoint string = registry.properties.loginServer
output containerAppName string = containerApp.name
output containerAppUri string = appCustomDomainBound
  ? 'https://${appCustomDomainName}'
  : 'https://${containerApp.properties.configuration.ingress.fqdn}'
output appCustomDomainBindingType string = empty(appCustomDomainName)
  ? 'NotConfigured'
  : appCustomDomainBound ? 'SniEnabled' : 'PendingCertificate'
output appCustomDomainVerificationId string = containerApp.properties.customDomainVerificationId
output dataStorageAccountName string = dataStorage.name
output dataStorageDfsEndpoint string = dataStorage.properties.primaryEndpoints.dfs
output dataContainerName string = dataContainer.name
output aiAccountName string = aiAccount.name
output aiProjectName string = aiProject.name
output aiProjectEndpoint string = 'https://${aiAccount.name}.services.ai.azure.com/api/projects/${aiProject.name}'
