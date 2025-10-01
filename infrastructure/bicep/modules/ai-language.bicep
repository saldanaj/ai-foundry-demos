// Azure AI Language Service
// Provides PII/PHI detection capabilities

@description('Name of the Language Service resource')
param languageServiceName string

@description('Location for the Language Service')
param location string = resourceGroup().location

@description('SKU for the Language Service')
@allowed([
  'F0'  // Free tier
  'S'   // Standard tier
])
param sku string = 'S'

@description('Tags to apply to the resource')
param tags object = {}

// Language Service (Cognitive Services - Text Analytics)
resource languageService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: languageServiceName
  location: location
  sku: {
    name: sku
  }
  kind: 'TextAnalytics'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: languageServiceName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    disableLocalAuth: false
  }
  tags: tags
}

// Outputs
@description('Language Service resource ID')
output languageServiceId string = languageService.id

@description('Language Service endpoint')
output languageServiceEndpoint string = languageService.properties.endpoint

@description('Language Service name')
output languageServiceName string = languageService.name

@description('Language Service principal ID (for RBAC)')
output languageServicePrincipalId string = languageService.identity.principalId
