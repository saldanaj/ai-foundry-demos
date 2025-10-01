"""
PII/PHI Detection using Azure AI Language Service
"""
import logging
from dataclasses import dataclass
from typing import Literal

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential


logger = logging.getLogger(__name__)


@dataclass
class PIIEntity:
    """Detected PII/PHI entity"""
    text: str
    category: str
    subcategory: str | None
    confidence_score: float
    offset: int
    length: int


@dataclass
class PIIDetectionResult:
    """Result of PII/PHI detection"""
    original_text: str
    redacted_text: str
    entities: list[PIIEntity]
    has_pii: bool
    should_reject: bool


class PIIDetector:
    """Detects and redacts PII/PHI using Azure AI Language Service"""

    def __init__(
        self,
        endpoint: str,
        key: str,
        mode: Literal["redact", "reject"] = "redact",
        confidence_threshold: float = 0.8,
        domain: str = "phi"  # Use "phi" for healthcare-specific detection
    ):
        """
        Initialize PII/PHI detector

        Args:
            endpoint: Azure AI Language Service endpoint
            key: Azure AI Language Service API key
            mode: "redact" to redact PII, "reject" to reject prompts with PII
            confidence_threshold: Minimum confidence score to consider (0.0-1.0)
            domain: "phi" for protected health information, "none" for general PII
        """
        self.endpoint = endpoint
        self.mode = mode
        self.confidence_threshold = confidence_threshold
        self.domain = domain

        credential = AzureKeyCredential(key)
        self.client = TextAnalyticsClient(
            endpoint=endpoint,
            credential=credential
        )

        logger.info(
            f"PII Detector initialized: mode={mode}, "
            f"threshold={confidence_threshold}, domain={domain}"
        )

    def detect_and_process(self, text: str) -> PIIDetectionResult:
        """
        Detect PII/PHI in text and process according to mode

        Args:
            text: Input text to analyze

        Returns:
            PIIDetectionResult with detected entities and processed text
        """
        try:
            logger.debug(f"Analyzing text for PII/PHI (length: {len(text)})")

            # Call Azure AI Language Service for PII detection
            response = self.client.recognize_pii_entities(
                documents=[text],
                domain_filter=self.domain if self.domain != "none" else None,
                language="en"
            )

            result = response[0]

            if result.is_error:
                logger.error(f"PII detection error: {result.error}")
                raise Exception(f"PII detection failed: {result.error}")

            # Extract entities above confidence threshold
            entities = []
            for entity in result.entities:
                if entity.confidence_score >= self.confidence_threshold:
                    entities.append(PIIEntity(
                        text=entity.text,
                        category=entity.category,
                        subcategory=entity.subcategory,
                        confidence_score=entity.confidence_score,
                        offset=entity.offset,
                        length=entity.length
                    ))

            has_pii = len(entities) > 0
            should_reject = has_pii and self.mode == "reject"

            # Get redacted text
            redacted_text = result.redacted_text if has_pii else text

            logger.info(
                f"PII detection complete: {len(entities)} entities found, "
                f"has_pii={has_pii}, should_reject={should_reject}"
            )

            return PIIDetectionResult(
                original_text=text,
                redacted_text=redacted_text,
                entities=entities,
                has_pii=has_pii,
                should_reject=should_reject
            )

        except Exception as e:
            logger.error(f"Error during PII detection: {str(e)}", exc_info=True)
            raise

    def get_entity_summary(self, result: PIIDetectionResult) -> dict:
        """
        Get summary of detected entities by category

        Args:
            result: PIIDetectionResult

        Returns:
            Dictionary mapping category to count
        """
        summary = {}
        for entity in result.entities:
            category = entity.category
            summary[category] = summary.get(category, 0) + 1
        return summary

    def highlight_entities(self, result: PIIDetectionResult) -> str:
        """
        Create highlighted version of text showing detected entities

        Args:
            result: PIIDetectionResult

        Returns:
            Text with entities highlighted using markdown
        """
        if not result.entities:
            return result.original_text

        # Sort entities by offset in reverse to avoid offset shifting
        sorted_entities = sorted(
            result.entities,
            key=lambda e: e.offset,
            reverse=True
        )

        highlighted = result.original_text
        for entity in sorted_entities:
            start = entity.offset
            end = entity.offset + entity.length
            original = highlighted[start:end]

            # Highlight with category label
            replacement = f"**[{original}]({entity.category})**"
            highlighted = highlighted[:start] + replacement + highlighted[end:]

        return highlighted
