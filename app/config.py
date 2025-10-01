"""
Configuration management for Azure AI Foundry Healthcare Demo
"""
import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Azure AI Language Service
    azure_language_endpoint: str = Field(
        ...,
        description="Azure AI Language Service endpoint"
    )
    azure_language_key: str = Field(
        ...,
        description="Azure AI Language Service API key"
    )

    # Azure AI Foundry
    azure_ai_foundry_project_connection_string: str | None = Field(
        None,
        description="Azure AI Foundry project connection string"
    )
    azure_ai_foundry_endpoint: str | None = Field(
        None,
        description="Azure AI Foundry endpoint (alternative to connection string)"
    )
    azure_ai_foundry_api_key: str | None = Field(
        None,
        description="Azure AI Foundry API key (alternative to connection string)"
    )
    azure_ai_foundry_project_name: str | None = Field(
        None,
        description="Azure AI Foundry project name"
    )
    bing_connection_id: str | None = Field(
        None,
        description="Bing Grounding connection ID (required for web grounding)"
    )

    # Azure API Management (Optional)
    azure_apim_endpoint: str | None = Field(
        None,
        description="Azure API Management endpoint"
    )
    azure_apim_subscription_key: str | None = Field(
        None,
        description="Azure API Management subscription key"
    )

    # Application Configuration
    pii_detection_mode: Literal["redact", "reject"] = Field(
        default="redact",
        description="Mode for handling PII/PHI: redact or reject"
    )
    pii_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for PII detection"
    )
    enable_web_grounding: bool = Field(
        default=True,
        description="Enable Bing web grounding"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Streamlit
    streamlit_server_port: int = Field(
        default=8501,
        description="Streamlit server port"
    )
    streamlit_server_address: str = Field(
        default="localhost",
        description="Streamlit server address"
    )

    def validate_config(self) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Check Azure AI Foundry configuration
        has_connection_string = bool(self.azure_ai_foundry_project_connection_string)
        has_individual_config = all([
            self.azure_ai_foundry_endpoint,
            self.azure_ai_foundry_api_key,
            self.azure_ai_foundry_project_name
        ])

        if not (has_connection_string or has_individual_config):
            errors.append(
                "Azure AI Foundry configuration incomplete. Provide either "
                "AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING or all of "
                "(AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_API_KEY, "
                "AZURE_AI_FOUNDRY_PROJECT_NAME)"
            )

        return errors


def get_settings() -> Settings:
    """Get application settings singleton"""
    return Settings()
