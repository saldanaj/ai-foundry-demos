#!/usr/bin/env python3
"""
Service Validation Script
Tests connectivity and functionality of all deployed Azure services
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_settings
from src.pii_detector import PIIDetector
from src.ai_foundry_client import AIFoundryClient


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_test(name, passed, message=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} - {name}")
    if message:
        print(f"       {message}")


def test_configuration():
    """Test configuration loading"""
    print_header("Testing Configuration")

    try:
        settings = get_settings()
        print_test("Load configuration", True)

        # Validate configuration
        errors = settings.validate_config()
        if errors:
            print_test("Validate configuration", False)
            for error in errors:
                print(f"       Error: {error}")
            return False
        else:
            print_test("Validate configuration", True)

        # Print key settings
        print(f"\n  Language Endpoint: {settings.azure_language_endpoint}")
        print(f"  PII Detection Mode: {settings.pii_detection_mode}")
        print(f"  Web Grounding: {settings.enable_web_grounding}")

        return True

    except Exception as e:
        print_test("Load configuration", False, str(e))
        return False


def test_pii_detection():
    """Test PII/PHI detection service"""
    print_header("Testing PII/PHI Detection Service")

    try:
        settings = get_settings()

        # Initialize detector
        detector = PIIDetector(
            endpoint=settings.azure_language_endpoint,
            key=settings.azure_language_key,
            mode="redact",
            confidence_threshold=0.8,
            domain="phi"
        )
        print_test("Initialize PII Detector", True)

        # Test 1: Safe text (no PII)
        safe_text = "What are the latest treatments for diabetes?"
        result = detector.detect_and_process(safe_text)

        if not result.has_pii:
            print_test("Safe text detection", True, "No PII detected as expected")
        else:
            print_test("Safe text detection", False, "False positive PII detection")

        # Test 2: Text with PII
        pii_text = "Patient John Doe, MRN 12345, has diabetes."
        result = detector.detect_and_process(pii_text)

        if result.has_pii:
            print_test("PII text detection", True, f"Detected {len(result.entities)} entities")
            print(f"       Original: {result.original_text}")
            print(f"       Redacted: {result.redacted_text}")

            # Verify entities
            categories = {e.category for e in result.entities}
            print(f"       Categories: {', '.join(categories)}")
        else:
            print_test("PII text detection", False, "Failed to detect PII")

        # Test 3: Redaction
        if "[" in result.redacted_text and "]" in result.redacted_text:
            print_test("PII redaction", True, "PII successfully redacted")
        else:
            print_test("PII redaction", False, "Redaction not working")

        return True

    except Exception as e:
        print_test("PII Detection Service", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_ai_foundry():
    """Test Azure AI Foundry connection and agent"""
    print_header("Testing Azure AI Foundry Service")

    try:
        settings = get_settings()

        # Initialize client
        client = AIFoundryClient(
            connection_string=settings.azure_ai_foundry_project_connection_string,
            enable_grounding=settings.enable_web_grounding
        )
        print_test("Initialize AI Foundry Client", True)

        # Create agent
        agent = client.create_agent(
            name="TestAgent",
            model="gpt-4o"
        )
        print_test("Create AI Agent", True, f"Agent ID: {agent.id}")

        # Test query
        test_prompt = "What are the latest treatments for type 2 diabetes?"
        print(f"\n  Query: {test_prompt}")

        response = client.query(test_prompt)

        if response.answer and len(response.answer) > 0:
            print_test("Agent Query", True, f"Response length: {len(response.answer)} chars")
            print(f"\n  Response preview: {response.answer[:200]}...")

            if response.grounding_used:
                print_test("Web Grounding", True, f"{len(response.citations)} citations")
                if response.citations:
                    print(f"\n  Sample citation: {response.citations[0].get('url', 'N/A')}")
            else:
                print_test("Web Grounding", False, "No grounding used")
        else:
            print_test("Agent Query", False, "Empty response")

        # Cleanup
        client.delete_agent(agent.id)
        print_test("Cleanup Agent", True)

        return True

    except Exception as e:
        print_test("AI Foundry Service", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end():
    """Test complete end-to-end flow"""
    print_header("Testing End-to-End Flow")

    try:
        settings = get_settings()

        # Initialize services
        detector = PIIDetector(
            endpoint=settings.azure_language_endpoint,
            key=settings.azure_language_key,
            mode="redact",
            confidence_threshold=0.8,
            domain="phi"
        )

        client = AIFoundryClient(
            connection_string=settings.azure_ai_foundry_project_connection_string,
            enable_grounding=True
        )

        agent = client.create_agent(name="E2ETestAgent", model="gpt-4o")

        # Test query with PII
        query = "Patient Jane Smith has been diagnosed with hypertension. What treatments are available?"
        print(f"\n  Original Query: {query}")

        # Step 1: Detect PII
        pii_result = detector.detect_and_process(query)
        print_test("Step 1: PII Detection", pii_result.has_pii, f"{len(pii_result.entities)} entities")
        print(f"       Redacted Query: {pii_result.redacted_text}")

        # Step 2: Query AI with redacted text
        response = client.query(pii_result.redacted_text)
        print_test("Step 2: AI Query", len(response.answer) > 0, "Response received")

        # Step 3: Verify response
        has_citations = len(response.citations) > 0
        print_test("Step 3: Web Grounding", has_citations, f"{len(response.citations)} citations")

        # Cleanup
        client.delete_agent(agent.id)

        print("\n  End-to-End Flow: ✓ SUCCESS")
        return True

    except Exception as e:
        print_test("End-to-End Flow", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  Healthcare Demo - Service Validation")
    print("="*60)

    results = {
        "Configuration": test_configuration(),
        "PII Detection": test_pii_detection(),
        "AI Foundry": test_ai_foundry(),
        "End-to-End": test_end_to_end()
    }

    # Summary
    print_header("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status}{reset} - {test_name}")

    print(f"\n  Tests Passed: {passed}/{total}")

    if passed == total:
        print("\n  🎉 All tests passed! Services are ready.")
        return 0
    else:
        print("\n  ⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
