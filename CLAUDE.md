# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Azure AI Foundry Healthcare Demo showcasing **PII/PHI detection and redaction** with **web-grounded AI responses**. The system detects Protected Health Information (PHI) in queries, redacts it, then sends sanitized queries to Azure AI Foundry Agent Service with Bing Grounding for safe web search.

**Architecture Flow:**
```
User Query → PII/PHI Detection → Redact/Reject → AI Foundry Agent + Bing Grounding → Response
```

## Environment Setup

### First-Time Setup

```bash
# 1. Deploy Azure infrastructure (15-20 min)
./infrastructure/bicep/deploy.sh

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with Azure credentials (auto-created by deploy.sh)

# 4. Run the application
streamlit run app/streamlit_app.py
```

### Manual Environment Setup

If `.env` not auto-created:
```bash
cp .env.example .env
```

Required environment variables:
- `AZURE_LANGUAGE_ENDPOINT` - Azure AI Language Service endpoint
- `AZURE_LANGUAGE_KEY` - Language Service API key
- `AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING` - AI Foundry connection string
- `PII_DETECTION_MODE` - "redact" or "reject"
- `PII_CONFIDENCE_THRESHOLD` - 0.0 to 1.0 (default: 0.8)
- `ENABLE_WEB_GROUNDING` - Enable Bing grounding

## Common Commands

### Running the Application

```bash
# Run Streamlit UI (default port 8501)
streamlit run app/streamlit_app.py

# Specify custom port
streamlit run app/streamlit_app.py --server.port 8502
```

### Infrastructure Management

```bash
# Deploy infrastructure (interactive)
./infrastructure/bicep/deploy.sh

# Validate Bicep template only
az deployment group validate \
  --resource-group rg-healthcare-demo-dev \
  --template-file infrastructure/bicep/main.bicep \
  --parameters @infrastructure/bicep/parameters.dev.json

# Deploy specific environment
az deployment group create \
  --resource-group rg-healthcare-demo-dev \
  --template-file infrastructure/bicep/main.bicep \
  --parameters @infrastructure/bicep/parameters.dev.json \
  --name "deploy-$(date +%Y%m%d-%H%M%S)"

# Clean up all resources
./infrastructure/bicep/cleanup.sh
# Or manually:
az group delete --name rg-healthcare-demo-dev --yes --no-wait
```

### Testing

```bash
# Validate Azure service connectivity
python scripts/test-services.py

# Run unit tests (when available)
pytest tests/

# Run with coverage
pytest --cov=src --cov=app tests/
```

## Code Architecture

### Core Components

**`src/pii_detector.py`** - PII/PHI Detection
- `PIIDetector` class uses Azure AI Language Service with `domain="phi"` for healthcare-specific entity detection
- Two modes: "redact" (replace with placeholders) or "reject" (block queries with PII)
- Returns `PIIDetectionResult` with entities, confidence scores, and redacted text
- Key method: `detect_and_process(text: str) -> PIIDetectionResult`

**`src/ai_foundry_client.py`** - AI Foundry Agent with Bing Grounding
- `AIFoundryClient` manages Azure AI Foundry Agent Service integration
- Creates agents with `BingGroundingTool()` for web search capabilities
- Thread-based conversation management
- Key method: `query(prompt: str, thread_id: str | None) -> GroundedResponse`
- Returns responses with citations from web sources

**`app/config.py`** - Configuration Management
- Pydantic-based settings validation
- Loads from `.env` file
- Validates Azure AI Foundry connection (connection string OR endpoint+key+project)
- Use `get_settings()` to access singleton configuration

**`app/streamlit_app.py`** - Streamlit UI
- Interactive demo interface
- PII visualization with side-by-side comparison
- Grounded response display with citations
- Configurable detection mode, threshold, and grounding toggle

### Infrastructure (Bicep Modules)

**`infrastructure/bicep/main.bicep`** - Main orchestration template
- `targetScope = 'resourceGroup'` - all resources in single RG
- Default region: **West US**
- Demo-optimized configuration

**Module Structure:**
- `modules/ai-language.bicep` - Language Service for PII detection
- `modules/ai-foundry.bicep` - AI Foundry Hub + Project with Storage, Key Vault, App Insights
- `modules/bing-search.bicep` - Bing Search API for web grounding
- `modules/apim.bicep` - API Management with AI gateway policies (optional)
- `modules/monitoring.bicep` - Log Analytics and Application Insights

**Parameter Files:**
- `parameters.json` - Default demo configuration (APIM disabled, optimized for cost)
- `parameters.example.json` - Template with placeholders for customization

### Key Design Patterns

**PII Processing Flow:**
1. User submits query via Streamlit UI
2. `PIIDetector.detect_and_process()` analyzes text
3. If PII found:
   - **Redact mode**: Replace entities with `[CATEGORY]` placeholders
   - **Reject mode**: Block query and show error
4. Sanitized query sent to AI Foundry
5. Agent uses Bing Grounding to retrieve current information
6. Response displayed with citations

**Agent Configuration:**
- Agents are created once and reused (`get_or_create_agent()`)
- Healthcare-focused system instructions emphasize:
  - Authoritative medical sources
  - Clear citations
  - Distinction between info and medical advice
  - Reminder about PII redaction

**Threading:**
- Each conversation can maintain state via `thread_id`
- Current implementation creates new thread per query
- To enable multi-turn: pass `thread_id` from previous response

## Important Implementation Notes

### PII Detection Domain

Always use `domain="phi"` for healthcare-specific entity detection:
```python
PIIDetector(endpoint, key, mode="redact", domain="phi")
```

This enables detection of healthcare-specific entities like:
- Medical Record Numbers (MRN)
- Patient names in clinical context
- Healthcare provider identifiers
- Protected Health Information per HIPAA

### AI Foundry Connection

Two authentication options:
1. **Connection string** (recommended):
   ```python
   AIProjectClient.from_connection_string(
       conn_str=connection_string,
       credential=DefaultAzureCredential()
   )
   ```

2. **Individual components**:
   ```python
   AIProjectClient(
       credential=DefaultAzureCredential(),
       endpoint=endpoint
   )
   ```

### Bing Grounding Setup

**Manual step required after deployment:**
1. Navigate to https://ai.azure.com
2. Select your AI Foundry project
3. Go to Settings → Tools
4. Enable Bing Search tool
5. Create connection to deployed Bing Search resource

The Bicep deployment creates the Bing Search resource but the connection must be configured manually in the portal.

### APIM Configuration

APIM is **enabled by default** using Consumption tier (pay-per-call, no base cost).

APIM includes:
- Rate limiting: 100 calls/minute per key
- Quota: 10,000 calls/day per subscription
- Managed identity authentication to Language Service
- Request/response logging to Application Insights

**Consumption tier:**
- No base cost
- $3.50 per million calls
- ~5 minute deployment time
- Perfect for demos

**To upgrade:** Change `apimSku` to `Developer` ($50/mo) or `Standard` ($680/mo) in `parameters.json`

## Configuration Validation

Settings are validated via Pydantic on load. Check for errors:
```python
from app.config import get_settings

settings = get_settings()
errors = settings.validate_config()
if errors:
    print("Configuration errors:", errors)
```

Common issues:
- Missing Azure AI Foundry connection string
- Invalid confidence threshold (must be 0.0-1.0)
- Incomplete APIM configuration

## Region Configuration

Default deployment region is **West US** (specified in `parameters.json`). To deploy to different region:

1. Edit parameter file: `"location": { "value": "eastus" }`
2. Or override at deployment: `--parameters location=eastus`
3. Or create custom parameters file and pass to deploy.sh

## Testing Approach

Use `tests/sample_prompts.json` for testing various scenarios:
- Safe queries (no PII)
- Queries with patient names
- Queries with MRNs, SSNs
- Clinical scenarios with multiple PII types

The `scripts/test-services.py` validates:
1. Configuration loading
2. PII detection functionality
3. AI Foundry connectivity
4. End-to-end query flow

## Cost Considerations

Demo configuration (~$56-89/month):
- Language Service (F0): $0 (Free tier, 5K records/month)
- AI Foundry Hub: ~$50
- Bing Search (S1): ~$5-20
- APIM (Consumption): ~$0-3 (pay-per-call)
- Storage/Key Vault/App Insights: ~$1-16

**Free tier limits:**
- Language Service F0: 5,000 text records/month, 1 req/sec
- APIM Consumption: $3.50 per million calls

**If free tier is insufficient:**
- Upgrade Language Service to S: +$200/month (20M chars/month, 1000 req/min)
- Upgrade APIM to Developer: +$50/month (no SLA)

**Best practices for demos:**
- Default configuration uses free/low-cost tiers
- Monitor free tier usage limits
- Tear down resources immediately after demos
- Use cleanup.sh script for easy removal

## Security Notes

- All PII is redacted before web search (prevents exposure to Bing)
- Managed identities used for service-to-service auth
- Key Vault stores sensitive configuration (when using connection string)
- RBAC assignments: Storage Blob Data Contributor, Key Vault Administrator
- Default deployment has public network access (enable Private Link for production)
- Do NOT commit `.env` files (already in `.gitignore`)

## Documentation References

Project docs:
- `docs/architecture.md` - Detailed technical architecture
- `docs/infrastructure-deployment.md` - Complete IaC deployment guide
- `docs/setup-guide.md` - Manual Azure resource provisioning
- `docs/demo-script.md` - Customer demo walkthrough

Azure docs:
- [Azure AI Language - PII Detection](https://learn.microsoft.com/en-us/azure/ai-services/language-service/personally-identifiable-information/overview)
- [Azure AI Foundry - Bing Grounding](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding)
- [Azure APIM - AI Gateway](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities)
