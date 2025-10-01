# Setup Guide - Azure AI Foundry Healthcare Demo

This guide provides detailed, step-by-step instructions for setting up the Azure AI Foundry Healthcare Demo from scratch.

## 📋 Table of Contents

1. [Azure Resource Provisioning](#azure-resource-provisioning)
2. [Local Development Setup](#local-development-setup)
3. [Configuration](#configuration)
4. [Testing the Setup](#testing-the-setup)
5. [Troubleshooting](#troubleshooting)

---

## Azure Resource Provisioning

### Prerequisites

- Active Azure subscription
- Azure CLI installed ([Install guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- Appropriate permissions to create resources in your subscription
- Owner or Contributor role on the subscription

### Step 1: Login to Azure

```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### Step 2: Create Resource Group

```bash
# Set variables
RESOURCE_GROUP="rg-healthcare-demo"
LOCATION="eastus"  # Choose region that supports all services

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### Step 3: Create Azure AI Language Service

```bash
# Set variables
LANGUAGE_SERVICE_NAME="lang-healthcare-demo-001"

# Create Language Service
az cognitiveservices account create \
  --name $LANGUAGE_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --kind TextAnalytics \
  --sku S \
  --location $LOCATION \
  --yes

# Get endpoint and key
az cognitiveservices account show \
  --name $LANGUAGE_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.endpoint" -o tsv

az cognitiveservices account keys list \
  --name $LANGUAGE_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "key1" -o tsv
```

**Save these values:**
- `AZURE_LANGUAGE_ENDPOINT`: The endpoint URL
- `AZURE_LANGUAGE_KEY`: Key1 value

### Step 4: Create Azure AI Foundry Project

#### Option A: Using Azure Portal (Recommended for First Time)

1. Navigate to [Azure AI Foundry Portal](https://ai.azure.com)

2. **Create a new project:**
   - Click "New project"
   - Project name: `healthcare-demo`
   - Select or create a new hub
   - Choose the same region as your Language Service

3. **Get Connection String:**
   - Go to "Settings" → "Connection strings"
   - Copy the project connection string
   - Save as `AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING`

#### Option B: Using Azure CLI (Advanced)

```bash
# Install the Azure AI extension
az extension add --name azure-ai

# Create AI Hub
HUB_NAME="hub-healthcare-demo"
az ml workspace create \
  --kind hub \
  --resource-group $RESOURCE_GROUP \
  --name $HUB_NAME \
  --location $LOCATION

# Create AI Project
PROJECT_NAME="healthcare-demo"
az ml workspace create \
  --kind project \
  --hub-id /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.MachineLearningServices/workspaces/$HUB_NAME \
  --resource-group $RESOURCE_GROUP \
  --name $PROJECT_NAME \
  --location $LOCATION
```

**Note:** Bing Grounding must be configured separately (see Step 5 below).

### Step 5: Setup Bing Grounding (Required for Web Search)

**Important:** The old Bing Search v7 API is retired. You must set up the new "Grounding with Bing Search" service.

#### Register Bing Provider

```bash
az provider register --namespace 'Microsoft.Bing'
```

#### Create Bing Grounding Resource

Navigate to the Azure Portal: [Create Bing Grounding](https://portal.azure.com/#create/Microsoft.BingGroundingSearch)

1. **Resource group:** Use the SAME resource group as your AI Foundry project
2. **Region:** Match your AI Foundry project region
3. **Name:** `bing-grounding-healthcare-demo`
4. Click **Review + Create**

#### Create Connection in AI Foundry

1. Go to [Azure AI Foundry Portal](https://ai.azure.com)
2. Navigate to your project
3. Go to **Settings** → **Connections**
4. Click **+ New connection**
5. Select **Bing Grounding**
6. Choose your Bing Grounding resource
7. Name: `bing-grounding`
8. Click **Add connection**

#### Get Connection ID

Find the connection ID in the AI Foundry portal or run:

```bash
python scripts/setup-bing-grounding.py
```

The connection ID format:
```
/subscriptions/<sub_id>/resourceGroups/<rg_name>/providers/Microsoft.CognitiveServices/accounts/<account_name>/projects/<project_name>/connections/bing-grounding
```

Save this as `BING_CONNECTION_ID` for later.

### Step 6: (Optional) Create Azure API Management

If you want to use Azure API Management as a gateway:

```bash
APIM_NAME="apim-healthcare-demo"

az apim create \
  --name $APIM_NAME \
  --resource-group $RESOURCE_GROUP \
  --publisher-name "Your Organization" \
  --publisher-email "your-email@example.com" \
  --sku-name Developer \
  --location $LOCATION
```

**Note:** APIM provisioning can take 30-45 minutes.

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd ai-foundry-demos
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected packages:**
- `azure-ai-textanalytics` - Language Service SDK
- `azure-identity` - Azure authentication
- `azure-ai-projects` - AI Foundry SDK
- `streamlit` - Web UI framework
- `pydantic` - Configuration management
- And more (see `requirements.txt`)

### Step 4: Verify Installation

```bash
# Check Python version (should be 3.10+)
python --version

# Verify key packages
python -c "import azure.ai.textanalytics; print('Azure AI Text Analytics: OK')"
python -c "import azure.ai.projects; print('Azure AI Projects: OK')"
python -c "import streamlit; print('Streamlit: OK')"
```

---

## Configuration

### Step 1: Create Environment File

```bash
cp .env.example .env
```

### Step 2: Edit .env File

Open `.env` in your text editor and fill in the values:

```env
# Azure AI Language Service
AZURE_LANGUAGE_ENDPOINT=https://lang-healthcare-demo-001.cognitiveservices.azure.com/
AZURE_LANGUAGE_KEY=your_key_from_step_3

# Azure AI Foundry
AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING=your_connection_string_from_step_4

# Bing Grounding (required for web search)
BING_CONNECTION_ID=your_bing_connection_id_from_step_5

# Application Configuration
PII_DETECTION_MODE=redact
PII_CONFIDENCE_THRESHOLD=0.8
ENABLE_WEB_GROUNDING=true
LOG_LEVEL=INFO
```

### Step 3: Verify Configuration

Run the configuration validator:

```python
# Create test script: verify_config.py
from app.config import get_settings

try:
    settings = get_settings()
    errors = settings.validate_config()

    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid!")
        print(f"  Language Endpoint: {settings.azure_language_endpoint}")
        print(f"  PII Mode: {settings.pii_detection_mode}")
        print(f"  Web Grounding: {settings.enable_web_grounding}")
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
```

Run it:
```bash
python verify_config.py
```

---

## Testing the Setup

### Step 1: Test PII Detection

Create test script: `test_pii.py`

```python
from src.pii_detector import PIIDetector
from app.config import get_settings

settings = get_settings()

# Initialize detector
detector = PIIDetector(
    endpoint=settings.azure_language_endpoint,
    key=settings.azure_language_key,
    mode="redact",
    confidence_threshold=0.8,
    domain="phi"
)

# Test with sample text
test_text = "Patient John Doe, MRN 12345, has diabetes."

result = detector.detect_and_process(test_text)

print(f"Original: {result.original_text}")
print(f"Redacted: {result.redacted_text}")
print(f"Entities found: {len(result.entities)}")
for entity in result.entities:
    print(f"  - {entity.category}: {entity.text}")
```

Run:
```bash
python test_pii.py
```

**Expected output:**
```
Original: Patient John Doe, MRN 12345, has diabetes.
Redacted: Patient [PERSON], MRN [MEDICAL_RECORD_NUMBER], has diabetes.
Entities found: 2
  - Person: John Doe
  - MedicalRecordNumber: 12345
```

### Step 2: Test Azure AI Foundry Connection

Create test script: `test_foundry.py`

```python
from src.ai_foundry_client import AIFoundryClient
from app.config import get_settings

settings = get_settings()

# Initialize client
client = AIFoundryClient(
    connection_string=settings.azure_ai_foundry_project_connection_string,
    enable_grounding=True,
    bing_connection_id=settings.bing_connection_id
)

# Create agent
agent = client.create_agent(
    name="TestAgent",
    model="gpt-4o"
)
print(f"✅ Agent created: {agent.id}")

# Test query
response = client.query("What are the latest treatments for diabetes?")
print(f"✅ Query successful!")
print(f"Answer preview: {response.answer[:100]}...")
print(f"Citations: {len(response.citations)}")

# Cleanup
client.delete_agent(agent.id)
print("✅ Cleanup complete")
```

Run:
```bash
python test_foundry.py
```

### Step 3: Launch Streamlit Application

```bash
streamlit run app/streamlit_app.py
```

**Expected behavior:**
1. Browser opens automatically to `http://localhost:8501`
2. Application displays "Services initialized and ready!"
3. No error messages in terminal or UI

### Step 4: Test End-to-End Flow

In the Streamlit UI:

1. **Test safe query:**
   - Enter: "What are the latest treatments for diabetes?"
   - Click "Analyze & Query"
   - Verify: No PII detected, response with citations

2. **Test query with PII:**
   - Enter: "Patient John Doe has diabetes. What treatments are available?"
   - Click "Analyze & Query"
   - Verify: PII detected and redacted, response still generated

3. **Test reject mode:**
   - Change sidebar to "Reject" mode
   - Enter same query with PII
   - Verify: Query is rejected with error message

---

## Troubleshooting

### Issue: "Configuration error" on startup

**Symptoms:**
```
Configuration error: field required
```

**Solution:**
1. Verify `.env` file exists in project root
2. Check all required fields are filled
3. Ensure no extra spaces around `=` signs
4. Verify keys/endpoints are correct

### Issue: PII detection not working

**Symptoms:**
```
Error during PII detection: 401 Unauthorized
```

**Solution:**
1. Verify `AZURE_LANGUAGE_KEY` is correct
2. Check endpoint URL format (should end with `/`)
3. Ensure Language Service is provisioned in same region
4. Verify service has PII detection capability enabled

### Issue: AI Foundry connection fails

**Symptoms:**
```
Failed to initialize services: connection string invalid
```

**Solution:**
1. Get fresh connection string from AI Foundry portal
2. Ensure Bing Grounding is enabled in project settings
3. Verify you have permissions to the AI Foundry project
4. Check that an agent with grounding tool exists

### Issue: Bing Grounding not working

**Symptoms:**
- Responses generated but no citations
- `grounding_used: false` in response
- Warning: "Bing grounding enabled but no connection ID provided"

**Solution:**
1. Verify `BING_CONNECTION_ID` is set in `.env` file
2. Ensure Bing Grounding resource is created in Azure portal
3. Verify connection exists in AI Foundry portal (Settings → Connections)
4. Run `python scripts/setup-bing-grounding.py` for setup verification
5. Check that `enable_web_grounding=True` in configuration
6. Verify connection ID format is correct (starts with `/subscriptions/...`)

### Issue: Streamlit app won't start

**Symptoms:**
```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution:**
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.10+)

### Issue: Import errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
1. Ensure you're running from project root directory
2. Check that `__init__.py` files exist in `src/` and `app/`
3. Verify Python path includes current directory

---

## Verification Checklist

Before considering setup complete, verify:

- [ ] Azure Language Service is provisioned and accessible
- [ ] Azure AI Foundry project is created with Bing Grounding enabled
- [ ] `.env` file is configured with all required credentials
- [ ] Python dependencies are installed in virtual environment
- [ ] PII detection test passes
- [ ] AI Foundry connection test passes
- [ ] Streamlit app launches without errors
- [ ] End-to-end test with sample prompts works
- [ ] Both redact and reject modes function correctly

---

## Next Steps

Once setup is complete:

1. **Review the demo script**: Read `docs/demo-script.md` for presentation guidance
2. **Customize prompts**: Add your own healthcare-specific test cases
3. **Explore configuration**: Adjust confidence thresholds and detection modes
4. **Review code**: Understand how the components integrate
5. **Plan integration**: Consider how to integrate with your existing systems

---

## Additional Resources

- [Azure AI Language Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/language-service/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Python Azure SDK Documentation](https://learn.microsoft.com/en-us/python/api/overview/azure/)

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review Azure service health in the portal
3. Consult Azure documentation for specific services
4. Open an issue in the repository

---

**Setup Complete!** You're ready to demonstrate the Azure AI Foundry Healthcare Demo. 🎉
