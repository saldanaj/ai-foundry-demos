# Demo Script - Azure AI Foundry Healthcare Demo

This script provides a step-by-step walkthrough for demonstrating the PII/PHI detection and web grounding capabilities to customers.

## 🎯 Demo Objectives

By the end of this demo, the customer should understand:

1. How Azure AI Language Services detects and redacts PII/PHI in healthcare scenarios
2. How Azure AI Foundry enables web-grounded responses with current information
3. The privacy-first architecture that protects patient data
4. How these services can be integrated into their healthcare applications

## ⏱️ Estimated Duration

**15-20 minutes** (full demo with Q&A)

## 🎬 Pre-Demo Checklist

- [ ] Azure services are provisioned and configured
- [ ] `.env` file is properly configured
- [ ] Application is running (`streamlit run app/streamlit_app.py`)
- [ ] Browser window is ready at `http://localhost:8501`
- [ ] Sample prompts are prepared
- [ ] Architecture diagram is available (optional)

## 📋 Demo Flow

### 1. Introduction (2 minutes)

**What to say:**

> "Today I'll demonstrate a solution that addresses a critical challenge in healthcare AI: how to leverage powerful language models and web search while protecting patient privacy and complying with regulations like HIPAA."

**Show:**
- Open the Streamlit application
- Point out the three main areas: input, PII detection, and grounded response

**Key points:**
- Healthcare organizations need up-to-date medical information
- Must protect PII/PHI at all times
- Solution uses Azure AI Language + AI Foundry + Bing Grounding

---

### 2. Safe Query - No PII (3 minutes)

**What to say:**

> "Let's start with a typical clinical query that doesn't contain any patient information."

**Steps:**

1. Enter query:
   ```
   What are the latest treatments for type 2 diabetes?
   ```

2. Click "Analyze & Query"

3. **Point out:**
   - ✅ **PII Detection**: "0 Entities Detected" - Safe to process
   - 🔍 **Processing**: Query sent as-is to Azure AI Foundry
   - 💬 **Response**: Current, evidence-based information returned
   - 🔗 **Citations**: Web sources are automatically cited

**What to say:**

> "Notice how the system confirms no PII was detected. The query goes directly to Azure AI Foundry Agent, which uses Bing to ground the response with current medical information. The citations show the sources used, ensuring transparency and credibility."

---

### 3. Query with PII - Redact Mode (5 minutes)

**What to say:**

> "Now let's see what happens when a query accidentally includes patient information - a common scenario in healthcare settings."

**Steps:**

1. Ensure sidebar shows: **PII/PHI Handling = Redact**

2. Enter query:
   ```
   Patient John Doe (MRN 12345) has been diagnosed with hypertension. What are the treatment options?
   ```

3. Click "Analyze & Query"

4. **Point out - PII Detection Section:**
   - 🔴 **Status**: "Contains PII/PHI"
   - **Entities Detected**: 2 (Person, Medical Record Number)
   - **Original Text**: Shows "John Doe" and "12345" highlighted in red
   - **Redacted Text**: Shows `[PERSON]` and `[MEDICAL_RECORD_NUMBER]` placeholders

**What to say:**

> "The Azure AI Language Service detected two PHI entities: a patient name and medical record number. Using the healthcare-specific PHI detection model, it automatically redacts this information before sending the query to web search."

5. **Point out - Response Section:**
   - ✅ **Action**: "Processed" (not rejected)
   - The grounded response is about hypertension treatments
   - No patient information was sent to Bing

**What to say:**

> "Critically, the redacted version was sent for web grounding - protecting patient privacy while still getting relevant clinical information. The response is about hypertension treatment, not about John Doe specifically."

---

### 4. Query with PII - Reject Mode (3 minutes)

**What to say:**

> "Some organizations may prefer to reject queries containing PII entirely rather than redacting. Let's demonstrate that mode."

**Steps:**

1. **In Sidebar**: Change "PII/PHI Handling" to **Reject**

2. Enter query:
   ```
   Review the case of patient with SSN 123-45-6789 who has diabetes complications.
   ```

3. Click "Analyze & Query"

4. **Point out:**
   - 🔴 **Status**: "Contains PII/PHI"
   - **Entity**: Social Security Number detected
   - ❌ **Action**: "Rejected"
   - **Error message**: Query blocked with explanation

**What to say:**

> "In reject mode, any query containing PII/PHI is blocked entirely. This is useful in scenarios where you want to enforce strict data governance and require users to remove all patient information before proceeding."

---

### 5. Advanced Query - Multiple PHI Types (3 minutes)

**What to say:**

> "Let's try a more complex scenario with multiple types of PHI."

**Steps:**

1. **In Sidebar**: Switch back to **Redact** mode

2. Enter query:
   ```
   Patient Sarah Williams, DOB 05/22/1978, phone 555-0123, presenting with cardiac symptoms. What diagnostic tests are recommended?
   ```

3. Click "Analyze & Query"

4. **Point out:**
   - **Multiple entity types**: Person, Date, Phone Number
   - **Entity Summary**: Shows breakdown by category
   - **Comprehensive redaction**: All PHI replaced with placeholders
   - **Useful response**: Still gets relevant diagnostic information

**What to say:**

> "Even with multiple PHI elements, the system comprehensively identifies and redacts everything. The resulting query focuses on the clinical question - diagnostic tests for cardiac symptoms - without exposing any patient information."

---

### 6. Configuration Options (2 minutes)

**What to say:**

> "The solution is highly configurable to meet different organizational needs."

**Show in Sidebar:**

1. **Detection Confidence Slider**
   - Adjust threshold (e.g., from 0.8 to 0.6)
   - Explain: Lower threshold = more sensitive detection

2. **Web Grounding Toggle**
   - Turn off to disable Bing grounding
   - Explain: Useful if you only want PII detection

**What to say:**

> "Organizations can tune the confidence threshold based on their risk tolerance. They can also disable web grounding if they only need the PII detection capability."

---

### 7. Architecture Overview (2-3 minutes)

**Show architecture diagram or describe:**

```
User Input (Streamlit UI)
    ↓
Azure AI Language Service (PII/PHI Detection with domain=phi)
    ↓
Decision: Redact or Reject
    ↓
Azure AI Foundry Agent (GPT-4 with Bing Grounding Tool)
    ↓
Response with Citations
```

**What to say:**

> "The architecture is straightforward but powerful:
>
> 1. **Azure AI Language Service** analyzes every query using the PHI detection model
> 2. Based on configuration, PII is either redacted or the query is rejected
> 3. **Azure AI Foundry Agent Service** processes the safe query, using Bing Grounding to search for current medical information
> 4. Responses include citations to source materials
>
> Optionally, you can add **Azure API Management** as a gateway layer for additional security, rate limiting, and token management."

---

### 8. Conversation History (1 minute)

**Show:**

1. Expand "Conversation History" section at bottom
2. Point out tracking of:
   - Multiple queries in session
   - Which ones had PII detected
   - Citation counts

**What to say:**

> "The system maintains conversation history, tracking which queries contained PII and how they were handled. This can be extended for audit logging and compliance reporting."

---

### 9. Use Cases & Value Proposition (2 minutes)

**Discuss real-world applications:**

1. **Clinical Research**: Healthcare providers researching latest treatments
2. **Telemedicine Platforms**: Chat systems that need to protect patient info
3. **Medical Documentation**: Assistants that help with clinical notes
4. **Drug Safety**: Checking interactions without exposing patient data
5. **Clinical Decision Support**: Evidence-based recommendations with privacy

**What to say:**

> "This solution enables healthcare organizations to:
> - ✅ Leverage AI and web search safely
> - ✅ Maintain HIPAA compliance through PII/PHI protection
> - ✅ Access current medical information (not just training data)
> - ✅ Provide transparency through citations
> - ✅ Configure policies based on organizational requirements"

---

### 10. Q&A and Next Steps

**Common Questions:**

**Q: What PHI entities can be detected?**
A: Person names, medical record numbers, SSN, dates, phone numbers, addresses, emails, organization names, and more. Azure AI Language Service supports 20+ PHI entity types.

**Q: Does this comply with HIPAA?**
A: Azure AI Language Service is HIPAA compliant. However, be aware that Bing Grounding operates outside the Azure compliance boundary. For strict HIPAA compliance, consider using only document grounding or disabling web grounding.

**Q: Can we customize what gets redacted?**
A: Yes, you can configure which entity types to detect and set confidence thresholds.

**Q: How accurate is the PII detection?**
A: Azure AI Language Service achieves high accuracy, especially with the PHI-specific model. You can tune the confidence threshold based on your needs.

**Q: Can this work with our existing systems?**
A: Absolutely. The core services expose REST APIs that can integrate with any application. This demo uses Python, but .NET, Java, and other languages are supported.

**Q: What about cost?**
A: Costs are based on:
- Azure AI Language: Per text record analyzed
- Azure AI Foundry: Token usage + Bing grounding API calls
- Azure API Management (optional): API calls and gateway hours

**Next Steps:**

1. **Pilot**: Start with a limited pilot in a development environment
2. **Integration**: Connect to your existing healthcare applications
3. **Compliance Review**: Work with your compliance team to validate the approach
4. **Expand**: Add features like audit logging, RBAC, and custom grounding sources
5. **Production**: Deploy to production with monitoring and governance

---

## 📝 Demo Tips

### Do's ✅

- **Practice beforehand**: Run through the demo 2-3 times
- **Engage the customer**: Ask about their specific use cases
- **Show real scenarios**: Use healthcare examples relevant to their business
- **Highlight privacy**: Emphasize the privacy-first approach
- **Show flexibility**: Demonstrate configuration options
- **Provide documentation**: Share the README and setup guide

### Don'ts ❌

- **Don't rush**: Take time to explain each component
- **Don't skip PII examples**: The PII detection is the key differentiator
- **Don't ignore errors**: If something fails, explain why (good learning opportunity)
- **Don't over-promise**: Be clear about Bing compliance boundaries
- **Don't forget Q&A**: Leave time for questions

---

## 🎁 Leave-Behind Materials

Provide the customer with:

1. ✅ GitHub repository access or code bundle
2. ✅ README with setup instructions
3. ✅ Architecture diagram
4. ✅ Sample prompts (safe and with PII)
5. ✅ Links to Azure documentation
6. ✅ Cost estimation worksheet (if available)

---

## 📞 Follow-Up

After the demo:

1. Send thank you email with materials
2. Schedule technical deep-dive if interested
3. Offer to help with pilot setup
4. Connect them with Azure support resources

---

**Good luck with your demo!** 🚀
