// Main Bicep template for Healthcare Demo Infrastructure
// Deploys all required Azure resources for PII/PHI detection and web grounding

targetScope = 'resourceGroup'

// ============================================================================
// PARAMETERS
// ============================================================================

@description('Environment name (e.g., dev, test, prod)')
@allowed([
  'dev'
  'test'
  'prod'
])
param environmentName string = 'dev'

@description('Base name for all resources (will be combined with environment)')
@minLength(3)
@maxLength(15)
param baseName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Deploy Azure API Management (optional, adds cost and deployment time)')
param deployAPIM bool = false

@description('SKU for Language Service')
@allowed([
  'F0'
  'S'
])
param languageServiceSku string = 'S'

@description('SKU for Bing Search')
@allowed([
  'F1'
  'S1'
  'S2'
  'S3'
])
param bingSearchSku string = 'S1'

@description('SKU for API Management (only used if deployAPIM is true)')
@allowed([
  'Consumption'
  'Developer'
  'Basic'
  'Standard'
  'Premium'
])
param apimSku string = 'Developer'

@description('Publisher name for APIM (required if deployAPIM is true)')
param apimPublisherName string = 'Healthcare Demo'

@description('Publisher email for APIM (required if deployAPIM is true)')
param apimPublisherEmail string = 'admin@example.com'

@description('Model deployments for Azure OpenAI')
param openAIModelDeployments array = [
  {
    name: 'gpt-4o'
    model: {
      name: 'gpt-4o'
      version: '2024-11-20'
    }
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
]

@description('Tags to apply to all resources')
param tags object = {
  Environment: environmentName
  Project: 'Healthcare-PII-PHI-Demo'
  ManagedBy: 'Bicep'
}

// ============================================================================
// VARIABLES
// ============================================================================

var resourceSuffix = '${baseName}-${environmentName}'
var languageServiceName = 'lang-${resourceSuffix}-${take(uniqueString(resourceGroup().id), 6)}'
var bingSearchName = 'bing-${resourceSuffix}'
var openAIServiceName = 'oai-${resourceSuffix}-${take(uniqueString(resourceGroup().id), 6)}'
var aiHubName = 'hub-${resourceSuffix}'
var aiProjectName = 'project-${resourceSuffix}'
var storageAccountName = 'st${baseName}${take(uniqueString(resourceGroup().id), 8)}'
var keyVaultName = 'kv-${baseName}-${take(uniqueString(resourceGroup().id), 8)}'
var logAnalyticsName = 'log-${resourceSuffix}'
var appInsightsName = 'appi-${resourceSuffix}'
var apimName = 'apim-${resourceSuffix}'

// ============================================================================
// MODULES
// ============================================================================

// Monitoring - Deploy first as it's needed by other resources
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-deployment'
  params: {
    logAnalyticsName: logAnalyticsName
    appInsightsName: appInsightsName
    location: location
    tags: tags
  }
}

// Azure AI Language Service
module languageService 'modules/ai-language.bicep' = {
  name: 'language-service-deployment'
  params: {
    languageServiceName: languageServiceName
    location: location
    sku: languageServiceSku
    tags: tags
  }
}

// Azure OpenAI Service with GPT-4o model deployment
module openAIService 'modules/azure-openai.bicep' = {
  name: 'openai-service-deployment'
  params: {
    openAIServiceName: openAIServiceName
    location: location
    sku: 'S0'
    modelDeployments: openAIModelDeployments
    tags: tags
  }
}

// Bing Search - DISABLED: Old Bing Search v7 API is retired
// Bing Grounding must be configured manually in AI Foundry portal
// See: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding
// module bingSearch 'modules/bing-search.bicep' = {
//   name: 'bing-search-deployment'
//   params: {
//     bingSearchName: bingSearchName
//     location: 'global'
//     sku: bingSearchSku
//     tags: tags
//   }
// }

// Azure AI Foundry (Hub + Project)
module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'ai-foundry-deployment'
  params: {
    hubName: aiHubName
    projectName: aiProjectName
    storageAccountName: storageAccountName
    keyVaultName: keyVaultName
    appInsightsName: monitoring.outputs.appInsightsName
    bingSearchName: '' // Bing Search module disabled
    location: location
    tags: tags
  }
  dependsOn: [
    monitoring
  ]
}

// Azure API Management (Optional)
module apim 'modules/apim.bicep' = if (deployAPIM) {
  name: 'apim-deployment'
  params: {
    apimName: apimName
    location: location
    sku: apimSku
    publisherName: apimPublisherName
    publisherEmail: apimPublisherEmail
    languageServiceEndpoint: languageService.outputs.languageServiceEndpoint
    languageServiceName: languageService.outputs.languageServiceName
    appInsightsInstrumentationKey: monitoring.outputs.appInsightsInstrumentationKey
    tags: tags
  }
  dependsOn: [
    languageService
    monitoring
  ]
}

// ============================================================================
// ROLE ASSIGNMENTS
// ============================================================================

// Cognitive Services User role for APIM to call Language Service
resource apimLanguageServiceRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployAPIM) {
  name: guid(resourceGroup().id, languageServiceName, apimName, 'CognitiveServicesUser')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908') // Cognitive Services User
    principalId: apim.outputs.apimPrincipalId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [
    languageService
    apim
  ]
}

// ============================================================================
// OUTPUTS
// ============================================================================

// Language Service Outputs
@description('Language Service endpoint')
output languageServiceEndpoint string = languageService.outputs.languageServiceEndpoint

@description('Language Service name')
output languageServiceName string = languageService.outputs.languageServiceName

@description('Language Service resource ID')
output languageServiceId string = languageService.outputs.languageServiceId

// Azure OpenAI Service Outputs
@description('Azure OpenAI Service endpoint')
output openAIServiceEndpoint string = openAIService.outputs.openAIServiceEndpoint

@description('Azure OpenAI Service name')
output openAIServiceName string = openAIService.outputs.openAIServiceName

@description('Azure OpenAI Service resource ID')
output openAIServiceId string = openAIService.outputs.openAIServiceId

@description('Deployed AI models')
output deployedModels array = openAIService.outputs.deployedModels

// AI Foundry Outputs
@description('AI Foundry Hub name')
output aiHubName string = aiFoundry.outputs.aiHubName

@description('AI Foundry Project name')
output aiProjectName string = aiFoundry.outputs.aiProjectName

@description('AI Foundry Project connection string')
output aiProjectConnectionString string = aiFoundry.outputs.aiProjectConnectionString

// Bing Search Outputs (disabled - APIs retired)
@description('Bing Search name')
output bingSearchName string = 'disabled'

@description('Bing Search endpoint')
output bingSearchEndpoint string = 'disabled'

// Monitoring Outputs
@description('Application Insights instrumentation key')
output appInsightsInstrumentationKey string = monitoring.outputs.appInsightsInstrumentationKey

@description('Application Insights connection string')
output appInsightsConnectionString string = monitoring.outputs.appInsightsConnectionString

// APIM Outputs (if deployed)
@description('APIM gateway URL (empty if not deployed)')
output apimGatewayUrl string = deployAPIM ? apim.outputs.apimGatewayUrl : ''

@description('APIM subscription key (empty if not deployed)')
output apimSubscriptionKey string = deployAPIM ? apim.outputs.demoSubscriptionKey : ''

@description('Language Service API path via APIM (empty if not deployed)')
output apimLanguageServiceAPIPath string = deployAPIM ? apim.outputs.languageServiceAPIPath : ''

// Storage and Key Vault (for reference)
@description('Storage Account name')
output storageAccountName string = aiFoundry.outputs.storageAccountName

@description('Key Vault name')
output keyVaultName string = aiFoundry.outputs.keyVaultName

// Resource Group
@description('Resource Group name')
output resourceGroupName string = resourceGroup().name

@description('Resource Group location')
output resourceGroupLocation string = resourceGroup().location

// Deployment Summary
@description('Deployment summary with key information')
output deploymentSummary object = {
  environment: environmentName
  resourceGroup: resourceGroup().name
  location: location
  languageService: {
    name: languageService.outputs.languageServiceName
    endpoint: languageService.outputs.languageServiceEndpoint
  }
  openAIService: {
    name: openAIService.outputs.openAIServiceName
    endpoint: openAIService.outputs.openAIServiceEndpoint
    deployedModels: openAIService.outputs.deployedModels
  }
  aiFoundry: {
    hubName: aiFoundry.outputs.aiHubName
    projectName: aiFoundry.outputs.aiProjectName
    connectionString: aiFoundry.outputs.aiProjectConnectionString
  }
  bingSearch: {
    name: 'disabled'
    endpoint: 'disabled'
  }
  apim: {
    deployed: deployAPIM
    gatewayUrl: deployAPIM ? apim.outputs.apimGatewayUrl : 'Not deployed'
  }
}
