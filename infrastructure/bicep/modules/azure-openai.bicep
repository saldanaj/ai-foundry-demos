// Azure OpenAI Service with GPT-4o Model Deployment
// Provides LLM capabilities for AI Foundry Agents

@description('Name of the Azure OpenAI Service')
param openAIServiceName string

@description('Location for Azure OpenAI Service')
param location string = resourceGroup().location

@description('SKU for Azure OpenAI Service')
@allowed([
  'S0'  // Standard tier
])
param sku string = 'S0'

@description('Model deployments configuration')
param modelDeployments array = [
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

@description('Tags to apply to the resource')
param tags object = {}

// Azure OpenAI Service (Cognitive Services - OpenAI)
resource openAIService 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: openAIServiceName
  location: location
  sku: {
    name: sku
  }
  kind: 'OpenAI'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: openAIServiceName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    disableLocalAuth: false
  }
  tags: tags
}

// Model Deployments
// Note: Using @batchSize(1) to deploy models sequentially to avoid quota conflicts
@batchSize(1)
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = [
  for deployment in modelDeployments: {
    name: deployment.name
    parent: openAIService
    sku: {
      name: deployment.sku.name
      capacity: deployment.sku.capacity
    }
    properties: {
      model: {
        format: 'OpenAI'
        name: deployment.model.name
        version: deployment.model.version
      }
      versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
      raiPolicyName: 'Microsoft.Default'
    }
  }
]

// Outputs
@description('Azure OpenAI Service resource ID')
output openAIServiceId string = openAIService.id

@description('Azure OpenAI Service endpoint')
output openAIServiceEndpoint string = openAIService.properties.endpoint

@description('Azure OpenAI Service name')
output openAIServiceName string = openAIService.name

@description('Azure OpenAI Service principal ID (for RBAC)')
output openAIServicePrincipalId string = openAIService.identity.principalId

@description('Deployed model names')
output deployedModels array = [for (deployment, i) in modelDeployments: {
  name: deployment.name
  modelName: deployment.model.name
  modelVersion: deployment.model.version
  deploymentName: modelDeployment[i].name
}]
