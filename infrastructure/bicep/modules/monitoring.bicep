// Monitoring Resources
// Log Analytics Workspace and Application Insights for monitoring

@description('Name of the Log Analytics Workspace')
param logAnalyticsName string

@description('Name of the Application Insights')
param appInsightsName string

@description('Location for monitoring resources')
param location string = resourceGroup().location

@description('Retention period in days for Log Analytics')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

@description('Tags to apply to resources')
param tags object = {}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
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
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
  tags: tags
}

// Outputs
@description('Log Analytics Workspace ID')
output logAnalyticsId string = logAnalytics.id

@description('Log Analytics Workspace name')
output logAnalyticsName string = logAnalytics.name

@description('Log Analytics Workspace resource ID for linking')
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId

@description('Application Insights ID')
output appInsightsId string = appInsights.id

@description('Application Insights name')
output appInsightsName string = appInsights.name

@description('Application Insights instrumentation key')
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey

@description('Application Insights connection string')
output appInsightsConnectionString string = appInsights.properties.ConnectionString
