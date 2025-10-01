# Infrastructure Deployment Guide

Complete guide for deploying Azure infrastructure using Bicep templates.

## 📋 Overview

This project includes Infrastructure as Code (IaC) using Azure Bicep to deploy all required resources with a single command. The deployment is **optimized for demos** with free-tier SKUs, fast setup (~15-20 min), and low cost (~$56-89/month).

### What Gets Deployed

- **Azure AI Language Service** - PII/PHI detection
- **Azure AI Foundry Hub + Project** - AI agent orchestration
- **Bing Search API** - Web grounding capability
- **Storage Account** - AI Foundry storage
- **Key Vault** - Secrets management
- **Application Insights** - Monitoring and logging
- **Log Analytics Workspace** - Centralized logging
- **Azure API Management** (Optional) - AI gateway with policies

## 🚀 Quick Start

### Prerequisites

1. **Azure CLI** installed ([Install guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
2. **Azure subscription** with appropriate permissions
3. **Bash shell** (Linux, macOS, WSL, or Git Bash on Windows)
4. **jq** command-line JSON processor ([Install guide](https://stedolan.github.io/jq/download/))

### One-Command Deployment

```bash
./infrastructure/bicep/deploy.sh
```

The script will:
1. Prompt you to login to Azure (if needed)
2. Prompt for resource group name
3. Validate the Bicep template
4. Deploy all resources (15-20 minutes)
5. Extract configuration values
6. Optionally create `.env` file

**Custom Parameters:**
```bash
# Use custom parameters file
./infrastructure/bicep/deploy.sh path/to/custom-parameters.json
```

## 📁 Infrastructure Structure

```
infrastructure/bicep/
├── main.bicep                      # Main orchestration template
├── modules/
│   ├── ai-language.bicep          # Language Service
│   ├── ai-foundry.bicep           # AI Foundry Hub + Project
│   ├── bing-search.bicep          # Bing Search API
│   ├── apim.bicep                 # API Management (optional)
│   └── monitoring.bicep           # Logging and monitoring
├── parameters.json                # Default demo configuration
├── parameters.example.json        # Template for customization
├── deploy.sh                      # Deployment script
└── cleanup.sh                     # Cleanup script
```

## ⚙️ Configuration

### Parameter Files

Two parameter files are provided:

1. **parameters.json** - Default demo configuration
   - Free-tier SKUs where available (Language Service F0, APIM Consumption)
   - APIM enabled by default with Consumption tier
   - Optimized for low cost (~$56-89/month)
   - Ready to use out of the box

2. **parameters.example.json** - Template for customization
   - Contains placeholder values
   - Copy and customize for specific needs

### Customizing Parameters

Edit `parameters.json` or create a custom file:

```json
{
  "parameters": {
    "environmentName": { "value": "demo" },
    "baseName": { "value": "healthdemo" },
    "location": { "value": "westus" },
    "deployAPIM": { "value": true },
    "languageServiceSku": { "value": "F0" },
    "bingSearchSku": { "value": "S1" },
    "apimSku": { "value": "Consumption" },
    "apimPublisherName": { "value": "Your Org" },
    "apimPublisherEmail": { "value": "admin@example.com" },
    "tags": {
      "value": {
        "Environment": "Demo",
        "Project": "Healthcare-PII-PHI-Demo"
      }
    }
  }
}
```

**To upgrade performance:**
- Language Service: Change `F0` to `S` (+$200/mo, higher limits)
- APIM: Change `Consumption` to `Developer` (+$50/mo, no SLA) or `Standard` (+$680/mo, production SLA)

## 🔨 Manual Deployment

If you prefer manual control:

### 1. Login to Azure

```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### 2. Create Resource Group

```bash
RESOURCE_GROUP="rg-healthcare-demo-dev"
LOCATION="eastus"

az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### 3. Validate Template

```bash
az deployment group validate \
  --resource-group $RESOURCE_GROUP \
  --template-file infrastructure/bicep/main.bicep \
  --parameters @infrastructure/bicep/parameters.dev.json
```

### 4. Deploy

```bash
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infrastructure/bicep/main.bicep \
  --parameters @infrastructure/bicep/parameters.json \
  --name "healthcare-demo-$(date +%Y%m%d-%H%M%S)"
```

### 5. Get Outputs

```bash
az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name "YOUR_DEPLOYMENT_NAME" \
  --query properties.outputs
```

## 🔑 Retrieving Credentials

### Language Service Key

```bash
LANGUAGE_SERVICE_NAME="lang-healthdemo-dev"

az cognitiveservices account keys list \
  --resource-group $RESOURCE_GROUP \
  --name $LANGUAGE_SERVICE_NAME \
  --query key1 -o tsv
```

### APIM Subscription Key (if deployed)

Already included in deployment outputs - check the `apimSubscriptionKey` output.

## 🎯 Post-Deployment Configuration

### 1. Setup Bing Grounding (Required for Web Search)

**Important:** The old Bing Search v7 API is retired. You must manually set up the new Grounding with Bing Search service.

#### Step 1: Register Bing Provider

```bash
az provider register --namespace 'Microsoft.Bing'
```

#### Step 2: Create Bing Grounding Resource

You must create this resource manually in the Azure portal:

1. Navigate to: [Create Bing Grounding](https://portal.azure.com/#create/Microsoft.BingGroundingSearch)
2. Select the **same resource group** as your AI Foundry project
3. Choose the **same region** as your project
4. Name: `bing-grounding-<your-base-name>`
5. Click **Review + Create**

**Why manual?** The new Bing Grounding resource type doesn't yet have Bicep/ARM template support.

#### Step 3: Create Connection in AI Foundry Portal

1. Navigate to [Azure AI Foundry Portal](https://ai.azure.com)
2. Select your project
3. Go to **Settings** → **Connections**
4. Click **+ New connection**
5. Select **Bing Grounding**
6. Choose your Bing Grounding resource (created in Step 2)
7. Name the connection: `bing-grounding`
8. Click **Add connection**

#### Step 4: Get Connection ID

The connection ID will be in this format:
```
/subscriptions/<sub_id>/resourceGroups/<rg_name>/providers/Microsoft.CognitiveServices/accounts/<account_name>/projects/<project_name>/connections/<connection_name>
```

You can find the connection ID:
- In AI Foundry portal: Settings → Connections → Click on your connection → Copy the ID
- Or run the helper script:

```bash
python scripts/setup-bing-grounding.py
```

This script will guide you through the setup and help locate the connection ID.

#### Step 5: Add to .env File

Add the connection ID to your `.env` file:

```bash
BING_CONNECTION_ID=/subscriptions/YOUR-SUB-ID/resourceGroups/YOUR-RG/providers/Microsoft.CognitiveServices/accounts/YOUR-ACCOUNT/projects/YOUR-PROJECT/connections/bing-grounding
```

### 2. Configure .env File

If the deployment script didn't create it automatically:

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

Fill in the values from deployment outputs:

```env
AZURE_LANGUAGE_ENDPOINT=<from deployment output>
AZURE_LANGUAGE_KEY=<from az cognitiveservices command>
AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING=<from deployment output>
BING_CONNECTION_ID=<from AI Foundry portal or setup script>
```

## 🧪 Validate Deployment

Run the service validation script:

```bash
python scripts/test-services.py
```

This will test:
- Configuration loading
- PII/PHI detection
- AI Foundry connectivity
- End-to-end flow

## 💰 Cost Estimation

### Demo Configuration - Optimized for Low Cost

| Service | SKU | Estimated Cost/Month |
|---------|-----|---------------------|
| Language Service | **F0 (Free)** | **$0** |
| AI Foundry Hub | Basic | ~$50 (minimum charge) |
| Bing Search | S1 | ~$5-20 (usage-based) |
| Storage Account | Standard LRS | ~$1-5 |
| Key Vault | Standard | ~$0-1 |
| Application Insights | Pay-as-you-go | ~$0-5 (low usage) |
| Log Analytics | Pay-as-you-go | ~$0-5 (low usage) |
| API Management | **Consumption** | **~$0-3** (pay-per-call) |
| **Total** | | **~$56-89/month** |

### Free Tier Limits (Important for Demos)

**Language Service F0:**
- 5,000 text records/month
- 1 request/second
- **Perfect for demos** - if you need more, upgrade to S tier (+$200/mo)

**APIM Consumption:**
- No base cost
- $3.50 per million calls
- **Perfect for demos** - only pay for what you use

### Alternative: Higher Performance

If free tier limits are too restrictive:
- **Language Service S**: +$200/month (20M characters/month, 1000 requests/min)
- **APIM Developer**: +$50/month (no SLA, good for dev/test)

**Note:**
- Costs vary by region and actual usage
- Free tiers have usage limits suitable for demos
- Tear down resources after demos to minimize costs
- Use [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for accurate estimates

## 🧹 Cleanup

### Option 1: Using Script

```bash
./infrastructure/bicep/cleanup.sh
```

The script will:
- Find resource groups with demo tags
- Prompt for confirmation
- Delete selected resource groups

### Option 2: Manual Cleanup

```bash
az group delete --name rg-healthcare-demo-dev --yes --no-wait
```

**Warning:** This deletes ALL resources in the resource group permanently!

## 🔒 Security Considerations

### Managed Identities

The deployment uses system-assigned managed identities for:
- AI Foundry Hub access to Storage and Key Vault
- APIM access to Language Service (if deployed)

### RBAC Assignments

The following role assignments are created:
- **Storage Blob Data Contributor** - AI Hub → Storage Account
- **Key Vault Administrator** - AI Hub → Key Vault
- **Cognitive Services User** - APIM → Language Service (if APIM deployed)

### Network Access

Default deployment:
- **Public network access enabled** for all services
- Suitable for demo/dev environments

For production:
- Configure private endpoints
- Restrict network access
- Enable Azure Private Link

## 🔄 Updating Infrastructure

To update existing deployment:

1. Modify Bicep templates or parameters
2. Re-run deployment script (resources will be updated, not recreated)

```bash
./infrastructure/bicep/deploy.sh
```

Bicep will perform incremental deployment, only changing what's needed.

## 🐛 Troubleshooting

### Deployment Fails with "Resource Already Exists"

If resource names conflict:
1. Delete existing resources
2. Change `baseName` parameter
3. Redeploy

### APIM Deployment Takes Too Long

APIM can take 30-45 minutes to deploy. This is normal. To avoid:
- Set `deployAPIM: false` for dev environments
- Deploy APIM separately if needed

### Bing Grounding Not Working

1. **Verify resource created:** Check Azure portal for Bing Grounding resource
2. **Check connection:** Go to AI Foundry portal → Settings → Connections
3. **Verify connection ID:** Ensure `BING_CONNECTION_ID` is set in `.env`
4. **Run setup script:** `python scripts/setup-bing-grounding.py` for diagnostics
5. **Check logs:** Look for Bing Grounding connection warnings in app logs

Common issues:
- Bing Grounding resource not in same resource group as AI Foundry project
- Connection not created in AI Foundry portal
- Connection ID incorrectly formatted in `.env`
- `enable_web_grounding=False` in configuration

### Permission Errors

Ensure you have:
- **Owner** or **Contributor** role on subscription
- Permission to create service principals
- Permission to assign RBAC roles

## 📚 Additional Resources

- [Azure Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [Azure AI Language Services](https://learn.microsoft.com/en-us/azure/ai-services/language-service/)
- [Azure API Management](https://learn.microsoft.com/en-us/azure/api-management/)

---

**Need Help?** Open an issue in the repository or consult Azure documentation.
