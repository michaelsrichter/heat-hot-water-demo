using 'main.bicep'

// AZURE_ENV_NAME / AZURE_LOCATION are set automatically by azd. AZURE_BUDGET_EMAIL
// is derived by infra/hooks/preprovision.* if not already set in the azd
// environment — see that script before assuming it's unset. (That hook also
// derives AZURE_PRINCIPAL_ID in advance, ready for the day this file grows a
// `principalId` param — see resources.bicep's header comment.)
param environmentName = readEnvironmentVariable('AZURE_ENV_NAME')
param location = readEnvironmentVariable('AZURE_LOCATION')
param budgetContactEmail = readEnvironmentVariable('AZURE_BUDGET_EMAIL')
param principalId = readEnvironmentVariable('AZURE_PRINCIPAL_ID')
param appCustomDomainName = readEnvironmentVariable(
  'AZURE_APP_CUSTOM_DOMAIN_NAME',
  'strategy-heat.eps-demos.site'
)
param appCustomDomainCertificateId = readEnvironmentVariable(
  'AZURE_APP_CUSTOM_DOMAIN_CERTIFICATE_ID',
  ''
)
