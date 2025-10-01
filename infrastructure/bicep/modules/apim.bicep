// Azure API Management
// AI Gateway with policies for Language Service and AI Foundry

@description('Name of the API Management instance')
param apimName string

@description('Location for API Management')
param location string = resourceGroup().location

@description('SKU for API Management')
@allowed([
  'Consumption'
  'Developer'
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Developer'

@description('Publisher name for APIM')
param publisherName string

@description('Publisher email for APIM')
param publisherEmail string

@description('Language Service endpoint')
param languageServiceEndpoint string

@description('Language Service name for backend')
param languageServiceName string

@description('AI Foundry endpoint')
param aiFoundryEndpoint string = ''

@description('Application Insights instrumentation key')
param appInsightsInstrumentationKey string = ''

@description('Tags to apply to the resource')
param tags object = {}

// API Management Instance
resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: apimName
  location: location
  sku: {
    name: sku
    capacity: sku == 'Consumption' ? 0 : 1
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
    customProperties: {
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Ssl30': 'False'
    }
  }
  tags: tags
}

// Application Insights Logger (if instrumentation key provided)
resource apimLogger 'Microsoft.ApiManagement/service/loggers@2023-05-01-preview' = if (!empty(appInsightsInstrumentationKey)) {
  parent: apim
  name: 'applicationinsights'
  properties: {
    loggerType: 'applicationInsights'
    credentials: {
      instrumentationKey: appInsightsInstrumentationKey
    }
    isBuffered: true
    resourceId: ''
  }
}

// Backend for Language Service
resource languageServiceBackend 'Microsoft.ApiManagement/service/backends@2023-05-01-preview' = {
  parent: apim
  name: 'language-service-backend'
  properties: {
    protocol: 'http'
    url: languageServiceEndpoint
    description: 'Azure AI Language Service for PII/PHI Detection'
    credentials: {
      header: {
        'Ocp-Apim-Subscription-Key': []
      }
    }
  }
}

// Language Service API
resource languageServiceAPI 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'language-service-api'
  properties: {
    displayName: 'Azure AI Language Service - PII Detection'
    description: 'API for detecting and redacting PII/PHI using Azure AI Language Service'
    serviceUrl: languageServiceEndpoint
    path: 'language'
    protocols: [
      'https'
    ]
    subscriptionRequired: true
    subscriptionKeyParameterNames: {
      header: 'Ocp-Apim-Subscription-Key'
      query: 'subscription-key'
    }
  }
}

// PII Detection Operation
resource piiDetectionOperation 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  parent: languageServiceAPI
  name: 'pii-detection'
  properties: {
    displayName: 'Detect and Redact PII/PHI'
    method: 'POST'
    urlTemplate: '/language/:analyze-text'
    description: 'Analyze text for PII/PHI entities and return redacted version'
    request: {
      queryParameters: [
        {
          name: 'api-version'
          type: 'string'
          required: true
          values: [
            '2023-04-01'
          ]
          defaultValue: '2023-04-01'
        }
      ]
      headers: [
        {
          name: 'Content-Type'
          type: 'string'
          required: true
          values: [
            'application/json'
          ]
        }
      ]
    }
    responses: [
      {
        statusCode: 200
        description: 'Success'
        representations: [
          {
            contentType: 'application/json'
          }
        ]
      }
    ]
  }
}

// Policy for Language Service API with rate limiting and logging
resource languageServiceAPIPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  parent: languageServiceAPI
  name: 'policy'
  properties: {
    value: '''
      <policies>
        <inbound>
          <base />
          <!-- Rate limiting per subscription -->
          <rate-limit-by-key calls="100" renewal-period="60" counter-key="@(context.Subscription.Id)" />

          <!-- Quota per subscription (daily) -->
          <quota-by-key calls="10000" renewal-period="86400" counter-key="@(context.Subscription.Id)" />

          <!-- Set backend service -->
          <set-backend-service backend-id="language-service-backend" />

          <!-- Use managed identity for authentication -->
          <authentication-managed-identity resource="https://cognitiveservices.azure.com" />

          <!-- Add custom headers -->
          <set-header name="X-Request-ID" exists-action="override">
            <value>@(context.RequestId)</value>
          </set-header>
        </inbound>
        <backend>
          <base />
        </backend>
        <outbound>
          <base />
          <!-- Add response headers for tracking -->
          <set-header name="X-APIM-Request-ID" exists-action="override">
            <value>@(context.RequestId)</value>
          </set-header>
        </outbound>
        <on-error>
          <base />
        </on-error>
      </policies>
    '''
    format: 'xml'
  }
}

// Named Values for configuration
resource tokenLimitNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-05-01-preview' = {
  parent: apim
  name: 'ai-token-limit'
  properties: {
    displayName: 'AI Token Limit (per minute)'
    value: '10000'
    secret: false
  }
}

// Product for Healthcare Demo
resource healthcareProduct 'Microsoft.ApiManagement/service/products@2023-05-01-preview' = {
  parent: apim
  name: 'healthcare-demo'
  properties: {
    displayName: 'Healthcare Demo APIs'
    description: 'APIs for the Healthcare PII/PHI Detection and Web Grounding Demo'
    subscriptionRequired: true
    approvalRequired: false
    state: 'published'
  }
}

// Add Language Service API to Product
resource productAPI 'Microsoft.ApiManagement/service/products/apis@2023-05-01-preview' = {
  parent: healthcareProduct
  name: languageServiceAPI.name
}

// Subscription for demo use
resource demoSubscription 'Microsoft.ApiManagement/service/subscriptions@2023-05-01-preview' = {
  parent: apim
  name: 'demo-subscription'
  properties: {
    displayName: 'Demo Subscription'
    scope: '/products/${healthcareProduct.id}'
    state: 'active'
  }
}

// Outputs
@description('API Management resource ID')
output apimId string = apim.id

@description('API Management name')
output apimName string = apim.name

@description('API Management gateway URL')
output apimGatewayUrl string = apim.properties.gatewayUrl

@description('API Management principal ID (for RBAC)')
output apimPrincipalId string = apim.identity.principalId

@description('Demo subscription primary key')
output demoSubscriptionKey string = demoSubscription.listSecrets().primaryKey

@description('Language Service API path')
output languageServiceAPIPath string = '${apim.properties.gatewayUrl}/${languageServiceAPI.properties.path}'
