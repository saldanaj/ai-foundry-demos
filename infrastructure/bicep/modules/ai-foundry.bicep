// Azure AI Foundry (Hub + Project)
// Provides AI Agent Service with Bing Grounding

@description('Name of the AI Foundry Hub')
param hubName string

@description('Name of the AI Foundry Project')
param projectName string

@description('Location for AI Foundry resources')
param location string = resourceGroup().location

@description('Name of the Storage Account for AI Foundry')
param storageAccountName string

@description('Name of the Key Vault for AI Foundry')
param keyVaultName string

@description('Name of the Application Insights')
param appInsightsName string

@description('Bing Search resource name for grounding')
param bingSearchName string = ''

@description('Tags to apply to resources')
param tags object = {}

// Storage Account for AI Foundry
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
  tags: union(tags, {
    SecurityControl: 'Ignore'
  })
}

// Key Vault for AI Foundry
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
  tags: tags
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
  tags: tags
}

// AI Foundry Hub (AI Studio Hub)
resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: hubName
  location: location
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: hubName
    description: 'AI Foundry Hub for Healthcare Demo'
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id
    publicNetworkAccess: 'Enabled'
  }
  tags: tags
}

// AI Foundry Project
resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: projectName
  location: location
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: projectName
    description: 'Healthcare Demo Project with PII/PHI Protection and Web Grounding'
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Enabled'
  }
  tags: tags
}

// Storage Blob Data Contributor role for Hub
resource hubStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, aiHub.id, 'StorageBlobDataContributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: aiHub.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Key Vault Administrator role for Hub
resource hubKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, aiHub.id, 'KeyVaultAdministrator')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '00482a5a-887f-4fb3-b025-3e41c74aba19') // Key Vault Administrator
    principalId: aiHub.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
@description('AI Hub resource ID')
output aiHubId string = aiHub.id

@description('AI Hub name')
output aiHubName string = aiHub.name

@description('AI Project resource ID')
output aiProjectId string = aiProject.id

@description('AI Project name')
output aiProjectName string = aiProject.name

@description('AI Project connection string (to be used in application)')
output aiProjectConnectionString string = 'Endpoint=${aiProject.properties.discoveryUrl};SubscriptionId=${subscription().subscriptionId};ResourceGroup=${resourceGroup().name};ProjectName=${aiProject.name}'

@description('Storage Account name')
output storageAccountName string = storageAccount.name

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Application Insights name')
output appInsightsName string = appInsights.name

@description('AI Hub principal ID')
output aiHubPrincipalId string = aiHub.identity.principalId

@description('AI Project principal ID')
output aiProjectPrincipalId string = aiProject.identity.principalId
