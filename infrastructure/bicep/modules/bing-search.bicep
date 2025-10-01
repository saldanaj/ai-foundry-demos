// Bing Search API Resource
// Provides web grounding capabilities for AI Foundry agents

@description('Name of the Bing Search resource')
param bingSearchName string

@description('Location for Bing Search (must be global)')
param location string = 'global'

@description('SKU for Bing Search')
@allowed([
  'F1'  // Free tier (limited transactions)
  'S1'  // Standard tier (3 TPS)
  'S2'  // Standard tier (10 TPS)
  'S3'  // Standard tier (25 TPS)
])
param sku string = 'S1'

@description('Tags to apply to the resource')
param tags object = {}

// Bing Search Resource
resource bingSearch 'Microsoft.Bing/accounts@2020-06-10' = {
  name: bingSearchName
  location: location
  sku: {
    name: sku
  }
  kind: 'Bing.Search.v7'
  properties: {
    statisticsEnabled: false
  }
  tags: tags
}

// Outputs
@description('Bing Search resource ID')
output bingSearchId string = bingSearch.id

@description('Bing Search name')
output bingSearchName string = bingSearch.name

@description('Bing Search endpoint')
output bingSearchEndpoint string = 'https://api.bing.microsoft.com/v7.0/search'
