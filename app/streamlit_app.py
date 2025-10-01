"""
Azure AI Foundry Healthcare Demo - Streamlit UI
PII/PHI Detection and Web Grounding Demo
"""
import sys
import time
from pathlib import Path

import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pii_detector import PIIDetector, PIIDetectionResult
from src.ai_foundry_client import AIFoundryClient, GroundedResponse
from src.utils import (
    setup_logging,
    format_entity_for_display,
    create_citation_markdown,
    estimate_tokens
)
from app.config import get_settings


# Page configuration
st.set_page_config(
    page_title="Azure AI Foundry Healthcare Demo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logging
setup_logging()


def init_session_state():
    """Initialize Streamlit session state"""
    if 'settings' not in st.session_state:
        try:
            st.session_state.settings = get_settings()
        except Exception as e:
            st.error(f"Configuration error: {str(e)}")
            st.info("Please ensure .env file is configured with required Azure credentials")
            st.stop()

    if 'pii_detector' not in st.session_state:
        st.session_state.pii_detector = None

    if 'ai_client' not in st.session_state:
        st.session_state.ai_client = None

    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = None

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []


def initialize_clients():
    """Initialize Azure service clients"""
    settings = st.session_state.settings

    # Initialize PII Detector
    if st.session_state.pii_detector is None:
        with st.spinner("Initializing PII/PHI detector..."):
            st.session_state.pii_detector = PIIDetector(
                endpoint=settings.azure_language_endpoint,
                key=settings.azure_language_key,
                mode=settings.pii_detection_mode,
                confidence_threshold=settings.pii_confidence_threshold,
                domain="phi"
            )

    # Initialize AI Foundry Client
    if st.session_state.ai_client is None:
        with st.spinner("Initializing Azure AI Foundry..."):
            st.session_state.ai_client = AIFoundryClient(
                connection_string=settings.azure_ai_foundry_project_connection_string,
                endpoint=settings.azure_ai_foundry_endpoint,
                api_key=settings.azure_ai_foundry_api_key,
                project_name=settings.azure_ai_foundry_project_name,
                enable_grounding=settings.enable_web_grounding,
                bing_connection_id=settings.bing_connection_id
            )


def render_sidebar():
    """Render sidebar with configuration and info"""
    with st.sidebar:
        st.title("🏥 Healthcare Demo")
        st.markdown("---")

        st.subheader("Configuration")

        # PII Detection Mode
        mode = st.radio(
            "PII/PHI Handling",
            options=["redact", "reject"],
            index=0 if st.session_state.settings.pii_detection_mode == "redact" else 1,
            help="Redact: Replace PII/PHI with placeholders\nReject: Block queries containing PII/PHI"
        )
        st.session_state.settings.pii_detection_mode = mode

        # Confidence Threshold
        threshold = st.slider(
            "Detection Confidence",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.settings.pii_confidence_threshold,
            step=0.05,
            help="Minimum confidence score to detect PII/PHI entities"
        )
        st.session_state.settings.pii_confidence_threshold = threshold

        # Web Grounding Toggle
        grounding = st.checkbox(
            "Enable Web Grounding",
            value=st.session_state.settings.enable_web_grounding,
            help="Use Bing to search for current information"
        )
        st.session_state.settings.enable_web_grounding = grounding

        st.markdown("---")

        # Reset conversation
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.thread_id = None
            st.session_state.conversation_history = []
            st.rerun()

        st.markdown("---")

        # Info
        st.subheader("About")
        st.markdown("""
        This demo showcases:
        - **PII/PHI Detection** using Azure AI Language
        - **Web Grounding** via Azure AI Foundry + Bing
        - **Privacy Protection** for healthcare queries

        All personal health information is detected and redacted before
        sending queries to web search.
        """)


def render_pii_analysis(result: PIIDetectionResult):
    """Render PII detection analysis"""
    st.subheader("🔍 PII/PHI Detection Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Entities Detected", len(result.entities))

    with col2:
        status = "🔴 Contains PII/PHI" if result.has_pii else "🟢 Safe"
        st.metric("Status", status)

    with col3:
        action = "❌ Rejected" if result.should_reject else "✅ Processed"
        st.metric("Action", action)

    if result.entities:
        # Entity summary
        entity_summary = {}
        for entity in result.entities:
            entity_summary[entity.category] = entity_summary.get(entity.category, 0) + 1

        st.write("**Detected Entity Types:**")
        st.write(format_entity_for_display(entity_summary))

        # Show comparison
        st.markdown("---")
        col_a, col_b = st.columns(2)

        with col_a:
            st.write("**Original Text:**")
            # Highlight entities in original text
            highlighted = result.original_text
            for entity in sorted(result.entities, key=lambda e: e.offset, reverse=True):
                start = entity.offset
                end = entity.offset + entity.length
                original_part = highlighted[start:end]
                highlighted = (
                    highlighted[:start] +
                    f"**:red[{original_part}]**" +
                    highlighted[end:]
                )
            st.markdown(highlighted)

        with col_b:
            st.write("**Redacted Text:**")
            st.markdown(result.redacted_text)


def render_grounded_response(response: GroundedResponse):
    """Render grounded response with citations"""
    st.subheader("💬 Response")

    st.markdown(response.answer)

    if response.citations:
        st.markdown("---")
        st.markdown(create_citation_markdown(response.citations))
    elif response.grounding_used:
        st.info("Web grounding was used, but no specific citations were returned.")
    else:
        st.info("Response generated without web grounding.")


def process_query(prompt: str):
    """Process user query through PII detection and AI Foundry"""
    start_time = time.time()

    # Step 1: PII/PHI Detection
    with st.spinner("Analyzing for PII/PHI..."):
        pii_result = st.session_state.pii_detector.detect_and_process(prompt)

    render_pii_analysis(pii_result)

    # Step 2: Check if should reject
    if pii_result.should_reject:
        st.error(
            "⛔ This query contains PII/PHI and has been rejected. "
            "Please remove personal health information and try again."
        )
        return

    # Step 3: Query AI Foundry with redacted text
    text_to_send = pii_result.redacted_text

    with st.spinner("Getting grounded response..."):
        response = st.session_state.ai_client.query(
            prompt=text_to_send,
            thread_id=st.session_state.thread_id
        )

        # Save thread ID for conversation continuity
        if st.session_state.thread_id is None:
            st.session_state.thread_id = response.thread_id

    # Step 4: Display response
    render_grounded_response(response)

    # Metrics
    end_time = time.time()
    processing_time = end_time - start_time

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Processing Time", f"{processing_time:.2f}s")

    with col2:
        tokens = estimate_tokens(prompt) + estimate_tokens(response.answer)
        st.metric("Est. Tokens", tokens)

    with col3:
        st.metric("Citations", len(response.citations))

    # Add to conversation history
    st.session_state.conversation_history.append({
        'prompt': prompt,
        'redacted_prompt': text_to_send,
        'pii_detected': pii_result.has_pii,
        'response': response.answer,
        'citations': len(response.citations)
    })


def main():
    """Main application"""
    # Initialize
    init_session_state()
    render_sidebar()

    # Header
    st.title("🏥 Azure AI Foundry Healthcare Demo")
    st.markdown(
        "Secure healthcare queries with **PII/PHI detection** and **web grounding**"
    )

    # Initialize clients
    try:
        initialize_clients()
    except Exception as e:
        st.error(f"Failed to initialize services: {str(e)}")
        st.info("Please check your configuration in .env file")
        st.stop()

    st.success("✅ Services initialized and ready!")

    # Main input area
    st.markdown("---")
    st.subheader("Ask a Healthcare Question")

    # Sample prompts
    with st.expander("💡 Try these sample prompts"):
        samples = [
            "What are the latest treatments for diabetes?",
            "What are the 2025 AHA guidelines for cardiac arrest?",
            "Are there interactions between metformin and common blood pressure medications?",
            "What are the current COVID-19 treatment protocols?",
            "Patient John Doe (MRN 12345) has diabetes. What are the latest treatments?"
        ]
        for sample in samples:
            if st.button(sample, key=f"sample_{hash(sample)}"):
                st.session_state.current_prompt = sample

    # Input
    prompt = st.text_area(
        "Enter your healthcare query:",
        height=100,
        placeholder="Example: What are the latest treatments for type 2 diabetes?",
        value=st.session_state.get('current_prompt', '')
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        submit = st.button("🔍 Analyze & Query", type="primary", use_container_width=True)

    if submit and prompt.strip():
        st.markdown("---")
        try:
            process_query(prompt)
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            st.exception(e)

    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        with st.expander(f"📜 Conversation History ({len(st.session_state.conversation_history)} queries)"):
            for i, conv in enumerate(reversed(st.session_state.conversation_history), 1):
                st.markdown(f"**Query {len(st.session_state.conversation_history) - i + 1}:**")
                st.write(f"Original: {conv['prompt'][:100]}...")
                if conv['pii_detected']:
                    st.write(f"Redacted: {conv['redacted_prompt'][:100]}...")
                st.write(f"Citations: {conv['citations']}")
                st.markdown("---")


if __name__ == "__main__":
    main()
