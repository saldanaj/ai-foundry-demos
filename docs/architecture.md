# Architecture - Azure AI Foundry Healthcare Demo

This document provides a detailed technical overview of the Azure AI Foundry Healthcare Demo architecture, components, and data flow.

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                      (Streamlit Web App)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ User Query
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer (Python)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              PII/PHI Detection Module                     │  │
│  │              (src/pii_detector.py)                        │  │
│  └─────────────────────────┬────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Azure AI Language Service                     │
│            (PII Detection with domain="phi")                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ Redacted Text or Rejection
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer (Python)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Azure AI Foundry Client Module                    │  │
│  │         (src/ai_foundry_client.py)                        │  │
│  └─────────────────────────┬────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              Azure AI Foundry Agent Service                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Agent (GPT-4/GPT-4o) + Bing Grounding Tool              │  │
│  └─────────────────────────┬────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│           Bing Grounding (Grounding with Bing Search)            │
│              (Retrieves current web information)                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ Grounded Response + Citations
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│              (Display Response with Citations)                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Component Details

### 1. User Interface Layer

**Technology:** Streamlit

**Responsibilities:**
- Accept user queries via text input
- Display PII/PHI detection results
- Show side-by-side comparison (original vs redacted text)
- Present grounded responses with citations
- Provide configuration controls (mode, threshold, etc.)
- Maintain conversation history

**Key Files:**
- `app/streamlit_app.py` - Main UI application
- `app/config.py` - Configuration management

**Features:**
- Real-time PII entity highlighting
- Toggle between redact/reject modes
- Confidence threshold adjustment
- Sample prompt selection
- Conversation history tracking

---

### 2. PII/PHI Detection Module

**Technology:** Azure AI Language Service SDK

**Responsibilities:**
- Detect PII/PHI entities in user queries
- Classify entities by type (Person, MRN, SSN, etc.)
- Redact sensitive information with placeholders
- Provide confidence scores for each detection
- Support both general PII and healthcare-specific PHI

**Key Files:**
- `src/pii_detector.py` - PII detection logic

**Entity Types Detected:**
- Person names
- Medical Record Numbers (MRN)
- Social Security Numbers (SSN)
- Dates (DOB, appointment dates)
- Phone numbers
- Email addresses
- Physical addresses
- Organization names
- And 15+ additional PHI types

**Detection Process:**

```python
# Pseudo-code
def detect_and_process(text):
    # 1. Call Azure AI Language Service
    response = client.recognize_pii_entities(
        documents=[text],
        domain_filter="phi",  # Healthcare-specific
        language="en"
    )

    # 2. Filter by confidence threshold
    entities = [e for e in response.entities
                if e.confidence_score >= threshold]

    # 3. Generate redacted text
    redacted_text = response.redacted_text

    # 4. Return result
    return PIIDetectionResult(
        original_text=text,
        redacted_text=redacted_text,
        entities=entities,
        has_pii=len(entities) > 0,
        should_reject=(mode == "reject" and len(entities) > 0)
    )
```

---

### 3. Azure AI Language Service

**Service:** Azure Cognitive Services - Language

**API Used:** PII Detection with PHI domain

**Capabilities:**
- Named Entity Recognition (NER) for PII/PHI
- Healthcare-optimized detection with `domain=phi`
- Automatic redaction with entity type placeholders
- Multi-language support (using English in this demo)
- Confidence scoring for each detected entity

**Compliance:**
- HIPAA compliant
- SOC 1, SOC 2, SOC 3 certified
- ISO 27001, ISO 27018 certified
- Processes data within Azure compliance boundary

**API Endpoint:**
```
POST {endpoint}/language/:analyze-text?api-version=2023-04-01
```

**Request Example:**
```json
{
  "kind": "PiiEntityRecognition",
  "parameters": {
    "domain": "phi",
    "modelVersion": "latest"
  },
  "analysisInput": {
    "documents": [
      {
        "id": "1",
        "text": "Patient John Doe, MRN 12345, has diabetes.",
        "language": "en"
      }
    ]
  }
}
```

---

### 4. AI Foundry Client Module

**Technology:** Azure AI Projects SDK

**Responsibilities:**
- Manage agent lifecycle (create, query, delete)
- Handle conversation threads
- Submit queries to agents
- Extract responses and citations
- Manage grounding tool configuration

**Key Files:**
- `src/ai_foundry_client.py` - AI Foundry integration

**Agent Configuration:**

```python
agent = client.create_agent(
    model="gpt-4o",
    name="HealthcareAssistant",
    instructions="""
    You are a healthcare assistant with access to current
    medical information via web search. Provide evidence-based
    responses with citations.
    """,
    tools=[BingGroundingTool(connection_id=bing_connection_id)]
)
```

**Query Flow:**

```python
# 1. Create or reuse thread
thread = client.create_thread()

# 2. Add user message (redacted query)
message = client.create_message(
    thread_id=thread.id,
    role=MessageRole.USER,
    content=redacted_text
)

# 3. Run agent
run = client.create_and_process_run(
    thread_id=thread.id,
    agent_id=agent.id
)

# 4. Extract response and citations
response = client.get_messages(thread.id)
```

---

### 5. Azure AI Foundry Agent Service

**Service:** Azure AI Foundry (formerly Azure AI Studio)

**Components:**
- **Agent Runtime:** Executes AI agent logic
- **LLM Integration:** Uses OpenAI GPT-4/GPT-4o models
- **Tool Orchestration:** Manages grounding tools
- **Thread Management:** Maintains conversation context

**Bing Grounding Tool:**

The Bing Grounding Tool enables agents to:
1. Determine when web search is needed
2. Generate search queries from user prompts
3. Execute Bing searches via Grounding with Bing Search resource
4. Retrieve relevant web content
5. Synthesize information into responses
6. Provide citations to source material

**Important:** Requires a Bing Grounding resource and connection:
- Bing Search v7 API is retired (August 11, 2025 shutdown)
- New "Grounding with Bing Search" resource must be created manually in Azure portal
- Connection must be established in AI Foundry portal (Settings → Connections)
- Connection ID passed to `BingGroundingTool(connection_id=...)`

**Agent Instructions (System Prompt):**

```
You are a knowledgeable healthcare assistant helping users find
information about medical topics, treatments, and clinical guidelines.
You have access to web search capabilities to provide up-to-date,
evidence-based information.

When answering:
1. Prioritize recent, authoritative sources
2. Clearly cite your sources
3. Distinguish between general information and medical advice
4. Remind users to consult healthcare professionals
5. Use clear, accessible language

Note: All PII has been redacted from user queries for privacy.
```

---

### 6. Bing Grounding (Web Search)

**Service:** Grounding with Bing Search (via Azure AI Foundry integration)

**Deployment:**
- **Resource Type:** Microsoft.Bing/accounts (Grounding with Bing Search)
- **Setup:** Manual creation in Azure portal (no Bicep/ARM support yet)
- **Connection:** Created in AI Foundry portal (Settings → Connections)
- **Integration:** Connection ID passed to BingGroundingTool

**Capabilities:**
- Real-time web search
- Healthcare and medical content indexing
- Relevance ranking
- Citation extraction

**Setup Process:**
1. Register Microsoft.Bing provider: `az provider register --namespace 'Microsoft.Bing'`
2. Create Bing Grounding resource in Azure portal
3. Create connection in AI Foundry portal
4. Get connection ID from AI Foundry
5. Pass connection ID to application via `BING_CONNECTION_ID` environment variable

**Important Compliance Note:**

⚠️ **Bing Search operates outside the Azure compliance boundary.**

- Search queries are sent to Microsoft Bing service
- Subject to Bing's terms and privacy policies
- Does **not** have the same HIPAA/compliance certifications as Azure AI services
- This is why PII/PHI redaction is critical before grounding

**Alternatives for Strict Compliance:**
- Use Azure AI Search with your own data (enterprise data grounding)
- Use SharePoint grounding tool (stays within M365 compliance boundary)
- Disable web grounding entirely for PII-sensitive scenarios

**Migration from Bing Search v7:**
- Old Bing Search v7 API retired August 11, 2025
- New Grounding with Bing Search provides better AI agent integration
- Requires manual resource creation (not yet supported in IaC templates)

---

## 🔄 Data Flow Diagram

### Scenario 1: Safe Query (No PII)

```
User: "What are the latest treatments for diabetes?"
  ↓
Streamlit UI
  ↓
PII Detector
  ↓ Analysis
Azure AI Language: No PII detected
  ↓
PII Detector: Pass through original text
  ↓
AI Foundry Client
  ↓
Azure AI Foundry Agent
  ↓ Uses Bing Grounding Tool
Bing Search: "latest diabetes treatments"
  ↓ Returns web results
Azure AI Foundry Agent: Synthesize response
  ↓
AI Foundry Client: Extract response + citations
  ↓
Streamlit UI: Display response with citations
```

### Scenario 2: Query with PII (Redact Mode)

```
User: "Patient John Doe (MRN 12345) has diabetes. What treatments?"
  ↓
Streamlit UI
  ↓
PII Detector
  ↓ Analysis
Azure AI Language: Detected [Person: John Doe], [MRN: 12345]
  ↓ Redaction
Azure AI Language: "Patient [PERSON] (MRN [MEDICAL_RECORD_NUMBER]) has diabetes. What treatments?"
  ↓
PII Detector: Return redacted text
  ↓
AI Foundry Client: Send redacted query
  ↓
Azure AI Foundry Agent
  ↓ Uses Bing Grounding Tool
Bing Search: "diabetes treatments" (no PII sent!)
  ↓ Returns web results
Azure AI Foundry Agent: Synthesize response
  ↓
AI Foundry Client: Extract response + citations
  ↓
Streamlit UI: Display original, redacted, and response
```

### Scenario 3: Query with PII (Reject Mode)

```
User: "Patient with SSN 123-45-6789 needs cardiac care."
  ↓
Streamlit UI
  ↓
PII Detector
  ↓ Analysis
Azure AI Language: Detected [SSN: 123-45-6789]
  ↓
PII Detector: should_reject = True
  ↓
Streamlit UI: Display rejection message
  ↓
[STOP - Query not sent to AI Foundry]
```

---

## 🔐 Security Architecture

### Authentication & Authorization

1. **Azure Services:**
   - Uses `DefaultAzureCredential` for managed identity or service principal
   - API keys stored in environment variables (`.env`)
   - Never hardcoded in source code

2. **Streamlit App:**
   - Runs locally (no external access by default)
   - Environment variables loaded via `python-dotenv`
   - Configuration validated on startup

### Data Protection

1. **PII/PHI Redaction:**
   - All queries analyzed before external calls
   - Redaction happens client-side (in application layer)
   - Original text never leaves Azure compliance boundary

2. **In-Transit:**
   - All Azure service calls use HTTPS
   - TLS 1.2+ encryption

3. **At-Rest:**
   - Azure AI Language: Data not stored long-term
   - Azure AI Foundry: Thread data stored according to retention policy
   - Local app: No persistent storage of queries (in-memory only)

### Compliance Considerations

| Component | HIPAA | SOC 2 | ISO 27001 | Notes |
|-----------|-------|-------|-----------|-------|
| Azure AI Language | ✅ | ✅ | ✅ | Within compliance boundary |
| Azure AI Foundry | ✅ | ✅ | ✅ | Agent service is compliant |
| Bing Search | ❌ | ❌ | ❌ | **Outside compliance boundary** |
| Streamlit App | N/A | N/A | N/A | Customer-managed |

**Recommendation for Production:**
- For strict HIPAA compliance, use document grounding instead of web grounding
- Implement audit logging for all queries
- Deploy app with authentication/authorization
- Use Azure Key Vault for secrets management

---

## 🏗️ Optional: API Management Layer

For enterprise deployments, add Azure API Management as a gateway:

```
User → Streamlit UI → Azure APIM → [Language Service, AI Foundry]
```

**APIM Benefits:**
- Centralized authentication/authorization
- Rate limiting and throttling
- Token usage tracking and quotas
- Request/response logging
- Circuit breaker patterns
- Multiple backend load balancing

**APIM Policies for AI Gateway:**

```xml
<policies>
  <inbound>
    <!-- Authentication -->
    <validate-jwt header-name="Authorization">
      <openid-config url="..." />
    </validate-jwt>

    <!-- Rate limiting by user -->
    <rate-limit-by-key calls="100" renewal-period="60"
                       counter-key="@(context.Request.Headers.GetValueOrDefault("Authorization"))" />

    <!-- Token quota -->
    <azure-openai-token-limit tokens="10000" renewal-period="3600" />
  </inbound>

  <outbound>
    <!-- Emit metrics -->
    <azure-openai-emit-token-metric />
  </outbound>
</policies>
```

---

## 📊 Performance Considerations

### Latency Breakdown (Typical)

| Component | Latency | Notes |
|-----------|---------|-------|
| PII Detection | 200-500ms | Depends on text length |
| Agent Processing | 1-3s | Varies with model/complexity |
| Bing Grounding | +1-2s | When grounding is used |
| **Total** | **2-5s** | End-to-end typical |

### Optimization Strategies

1. **Caching:**
   - Cache PII detection results for identical queries
   - Reuse agent threads for conversation continuity

2. **Parallel Processing:**
   - Could run PII detection and agent query in parallel if PII check is pre-validated

3. **Async Operations:**
   - Use async/await for non-blocking I/O
   - Particularly useful for Streamlit app responsiveness

4. **Model Selection:**
   - GPT-4o is faster than GPT-4
   - Consider GPT-3.5-turbo for lower latency if acceptable

---

## 🔮 Future Architecture Enhancements

1. **Multi-Agent System:**
   - Separate agents for different medical specialties
   - Router agent to direct queries to appropriate specialist

2. **Document Grounding:**
   - Add Azure AI Search for grounding on internal documents
   - Medical literature, clinical guidelines, formularies

3. **Conversation Memory:**
   - Persistent conversation storage
   - User profile management

4. **Audit & Compliance:**
   - Comprehensive logging to Azure Monitor
   - Compliance reporting dashboard
   - Automated PHI detection audits

5. **Multi-Modal Support:**
   - Image analysis for medical imaging questions
   - PDF parsing for medical records

6. **FHIR Integration:**
   - Connect to FHIR servers for patient data
   - Contextual queries based on patient records

---

## 🛠️ Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| **UI** | Streamlit | Interactive web interface |
| **Backend** | Python 3.10+ | Application logic |
| **PII Detection** | Azure AI Language | PHI detection and redaction |
| **AI Agents** | Azure AI Foundry | Agent orchestration |
| **LLM** | GPT-4/GPT-4o | Natural language understanding |
| **Grounding** | Grounding with Bing Search | Current web information |
| **Config** | Pydantic + dotenv | Settings management |
| **Auth** | Azure Identity | Service authentication |

---

## 📚 Architecture Principles

1. **Privacy-First:** PII/PHI never leaves compliance boundary
2. **Defense in Depth:** Multiple layers of security
3. **Configurability:** Flexible modes for different use cases
4. **Transparency:** Citations and entity highlighting
5. **Modularity:** Loosely coupled components
6. **Scalability:** Can add APIM, caching, load balancing
7. **Compliance:** Designed with healthcare regulations in mind

---

**End of Architecture Document**
