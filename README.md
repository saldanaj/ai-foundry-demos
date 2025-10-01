# Azure AI Foundry Healthcare Demo

A demonstration application showcasing **PII/PHI detection and redaction** with **web-grounded AI responses** using Azure AI services. This demo is specifically designed for healthcare scenarios where protecting patient privacy is critical.

## 🎯 Features

- **PII/PHI Detection**: Automatically detects and redacts Protected Health Information using Azure AI Language Services
- **Web Grounding**: Retrieves current medical information using Azure AI Foundry Agent Service with Bing Grounding
- **Privacy-First**: Ensures PII/PHI is redacted before sending queries to web search
- **Interactive UI**: Streamlit-based interface for easy demonstration and testing
- **Flexible Modes**: Choose between redacting PII/PHI or rejecting queries containing sensitive information
- **Healthcare-Focused**: Optimized for clinical and medical queries

## 🏗️ Architecture

```
User Query (Streamlit UI)
    ↓
Azure AI Language Service (PII/PHI Detection)
    ↓
Redact or Reject based on configuration
    ↓
Azure AI Foundry Agent + Bing Grounding
    ↓
Grounded Response with Citations
```

### Key Components

1. **Azure AI Language Service**: Detects PII/PHI entities with `domain=phi` for healthcare-specific detection
2. **Azure AI Foundry Agent Service**: Provides intelligent responses using OpenAI models with Bing grounding
3. **Streamlit UI**: Interactive interface for demonstrations
4. **Optional APIM**: Azure API Management can be added as a gateway layer for additional control

## 📋 Prerequisites

- Python 3.10+
- Azure subscription with the following resources:
  - Azure AI Language Service
  - Azure AI Foundry project with Bing Grounding enabled
  - (Optional) Azure API Management instance

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

**One-command deployment** of all Azure infrastructure optimized for demos:

```bash
# Deploy Azure infrastructure with Bicep (15-20 min)
./infrastructure/bicep/deploy.sh

# Script will:
# 1. Deploy all Azure resources
# 2. Automatically create .env file with credentials
```

Then setup Bing Grounding and run the app:

```bash
# Install dependencies
pip install -r requirements.txt

# Setup Bing Grounding (provides instructions)
python scripts/setup-bing-grounding.py

# Run the application
streamlit run app/streamlit_app.py
```

**Note:** This deploys demo-optimized infrastructure with free-tier SKUs (~$10-40/month) including APIM gateway.

See [Infrastructure Deployment Guide](docs/infrastructure-deployment.md) for details.

### Option 2: Manual Setup

If you prefer to provision Azure resources manually or already have them:

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-foundry-demos
```

#### 2. Provision Azure Resources

Manually create these resources in Azure Portal:
- Azure AI Language Service
- Azure AI Foundry project with Bing Grounding enabled
- (Optional) Azure API Management instance

See [Setup Guide](docs/setup-guide.md) for detailed instructions.

#### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Azure credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Azure service credentials:

```env
# Azure AI Language Service
AZURE_LANGUAGE_ENDPOINT=https://your-language-service.cognitiveservices.azure.com/
AZURE_LANGUAGE_KEY=your_language_service_key_here

# Azure AI Foundry
AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING=your_project_connection_string_here

# Configuration
PII_DETECTION_MODE=redact  # or "reject"
PII_CONFIDENCE_THRESHOLD=0.8
ENABLE_WEB_GROUNDING=true
```

#### 5. Run the Application

```bash
streamlit run app/streamlit_app.py
```

The application will open in your browser at `http://localhost:8501`

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_LANGUAGE_ENDPOINT` | Azure AI Language Service endpoint | Required |
| `AZURE_LANGUAGE_KEY` | Azure AI Language Service API key | Required |
| `AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING` | Azure AI Foundry connection string | Required |
| `PII_DETECTION_MODE` | `redact` or `reject` | `redact` |
| `PII_CONFIDENCE_THRESHOLD` | Confidence threshold (0.0-1.0) | `0.8` |
| `ENABLE_WEB_GROUNDING` | Enable Bing grounding | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

### PII Detection Modes

- **Redact Mode**: Replaces detected PII/PHI with entity type placeholders (e.g., `[PERSON]`, `[SSN]`)
- **Reject Mode**: Blocks queries containing PII/PHI and prompts user to remove sensitive information

## 💡 Usage Examples

### Safe Query (No PII)

**Input:**
```
What are the latest treatments for type 2 diabetes?
```

**Process:**
- ✅ No PII detected
- ✅ Sent to web grounding as-is
- ✅ Returns current treatment information with citations

### Query with PII (Redact Mode)

**Input:**
```
Patient John Doe (MRN 12345) has diabetes. What are treatment options?
```

**Process:**
- 🔴 PII detected: `John Doe` (Person), `12345` (Medical Record Number)
- ✏️ Redacted to: `Patient [PERSON] (MRN [MEDICAL_RECORD_NUMBER]) has diabetes. What are treatment options?`
- ✅ Redacted query sent to web grounding
- ✅ Returns treatment information without exposing PII

### Query with PII (Reject Mode)

**Input:**
```
Patient SSN 123-45-6789 needs cardiac care recommendations.
```

**Process:**
- 🔴 PII detected: `123-45-6789` (SSN)
- ❌ Query rejected due to PII
- User prompted to remove sensitive information

## 📂 Project Structure

```
/
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore file
│
├── app/
│   ├── __init__.py
│   ├── streamlit_app.py           # Main Streamlit UI
│   └── config.py                   # Configuration management
│
├── src/
│   ├── __init__.py
│   ├── pii_detector.py            # PII/PHI detection module
│   ├── ai_foundry_client.py       # Azure AI Foundry client
│   └── utils.py                    # Helper utilities
│
├── tests/
│   ├── __init__.py
│   ├── sample_prompts.json        # Test prompts with/without PII
│   └── test_pii_detector.py       # Unit tests (to be added)
│
├── infrastructure/                 # Infrastructure as Code
│   └── bicep/
│       ├── main.bicep             # Main orchestration template
│       ├── modules/               # Bicep modules
│       │   ├── ai-language.bicep
│       │   ├── ai-foundry.bicep
│       │   ├── bing-search.bicep
│       │   ├── apim.bicep
│       │   └── monitoring.bicep
│       ├── parameters.json        # Default demo configuration
│       ├── parameters.example.json # Template for customization
│       ├── deploy.sh              # Deployment script
│       └── cleanup.sh             # Cleanup script
│
├── scripts/                        # Automation scripts
│   ├── test-services.py           # Service validation
│   └── setup-demo.sh              # End-to-end setup
│
└── docs/
    ├── architecture.md               # Detailed architecture
    ├── setup-guide.md                # Manual step-by-step setup
    ├── infrastructure-deployment.md  # IaC deployment guide
    └── demo-script.md                # Customer demo walkthrough
```

## 🔐 Security & Privacy Considerations

1. **PII/PHI Protection**: All detected personal health information is redacted before web queries
2. **Compliance Boundary**: Be aware that Bing grounding operates outside Azure's compliance boundary
3. **Audit Logging**: Consider implementing audit logs for HIPAA compliance
4. **Access Control**: Use Azure RBAC to control access to Language Service and AI Foundry
5. **Data Retention**: Review data retention policies for your Azure services

## 🏥 Healthcare Use Cases

1. **Clinical Research Queries**: Find latest treatments while protecting patient identity
2. **Drug Interaction Checks**: Search for medication interactions safely
3. **Clinical Guidelines**: Access current medical protocols and guidelines
4. **Treatment Options**: Research evidence-based treatment approaches
5. **Diagnostic Information**: Gather information about symptoms and conditions

## 🧪 Testing

Sample prompts are provided in `tests/sample_prompts.json` covering:

- Safe queries (no PII)
- Queries with various PII types
- Clinical scenarios
- Edge cases

To test manually:

1. Start the application
2. Use sample prompts from the dropdown
3. Observe PII detection and redaction
4. Review grounded responses with citations

## 📊 Metrics & Monitoring

The UI displays:

- **Entities Detected**: Number of PII/PHI entities found
- **Detection Status**: Safe or Contains PII/PHI
- **Processing Action**: Processed or Rejected
- **Processing Time**: Total time for detection + grounding
- **Estimated Tokens**: Rough token count
- **Citations**: Number of web sources cited

## 🏗️ Infrastructure as Code

This project includes complete **Bicep templates** for automated infrastructure deployment:

- **One-command deployment** of all Azure resources
- **Demo-optimized** configuration for quick setup and lower cost
- **Optional Azure API Management** with AI gateway policies
- **Monitoring and logging** with Application Insights
- **RBAC assignments** and managed identities

### Quick Deploy

```bash
./infrastructure/bicep/deploy.sh

# Or with custom parameters:
./infrastructure/bicep/deploy.sh path/to/custom-parameters.json
```

See [Infrastructure Deployment Guide](docs/infrastructure-deployment.md) for full details.

### What Gets Deployed

| Resource | Purpose | Included |
|----------|---------|----------|
| Azure AI Language Service | PII/PHI Detection | ✅ |
| Azure AI Foundry Hub + Project | AI Agent orchestration | ✅ |
| Bing Grounding | Web grounding | 🔧 Manual setup required |
| Storage Account | AI Foundry storage | ✅ |
| Key Vault | Secrets management | ✅ |
| Application Insights | Monitoring | ✅ |
| Log Analytics | Logging | ✅ |
| Azure API Management | AI Gateway | ✅ |

**Note:** All services use free or low-cost tiers optimized for demos. Total estimated cost: **$10-40/month** (excluding Bing Grounding, which is pay-per-use).

### Cleanup

```bash
./infrastructure/bicep/cleanup.sh
```

## 🔄 Future Enhancements

- [ ] Add unit and integration tests
- [ ] Add audit logging for compliance
- [ ] Support multi-turn conversations with context
- [ ] Export conversation transcripts (redacted)
- [ ] Integration with FHIR resources
- [ ] Role-based access control (RBAC)
- [ ] Performance optimization and caching

## 🐛 Troubleshooting

### Configuration Errors

If you see configuration errors:
1. Verify `.env` file exists and is properly formatted
2. Check that all required Azure credentials are correct
3. Ensure Azure services are properly provisioned

### PII Detection Issues

If PII detection isn't working:
1. Verify Azure AI Language Service endpoint and key
2. Check that the service supports the `phi` domain
3. Review confidence threshold setting

### Grounding Issues

If web grounding isn't working:
1. Verify Azure AI Foundry connection string
2. Ensure Bing Grounding is enabled in your project
3. Check that the agent was created successfully

## 📚 Documentation

### Project Documentation

- [Architecture Guide](docs/architecture.md) - Detailed technical architecture and data flow
- [Infrastructure Deployment](docs/infrastructure-deployment.md) - IaC deployment with Bicep
- [Setup Guide](docs/setup-guide.md) - Manual Azure resource provisioning
- [Demo Script](docs/demo-script.md) - Customer presentation walkthrough

### Azure Resources

- [Azure AI Language Services - PII Detection](https://learn.microsoft.com/en-us/azure/ai-services/language-service/personally-identifiable-information/overview)
- [Azure AI Foundry - Bing Grounding](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding)
- [Azure API Management - AI Gateway](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities)
- [Azure Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

For questions or issues, please open an issue in the repository.

---

**Built with Azure AI Services** | **Privacy-First Healthcare AI**
