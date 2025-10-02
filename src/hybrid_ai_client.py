"""
Hybrid AI Client with fallback from AI Foundry to direct OpenAI
"""
import logging
from dataclasses import dataclass
from typing import Any
import os
from dotenv import load_dotenv

from openai import AzureOpenAI
from src.ai_foundry_client import AIFoundryClient, GroundedResponse
from .foundry_agent_client import FoundryAgentClient
from src.direct_bing_client import DirectBingClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class SimpleResponse:
    """Simple response format compatible with GroundedResponse"""
    answer: str
    citations: list[dict[str, Any]]
    thread_id: str
    run_id: str
    grounding_used: bool


class HybridAIClient:
    """
    Hybrid AI client that tries AI Foundry first, falls back to direct OpenAI
    """
    
    def __init__(
        self,
        connection_string: str | None = None,
        endpoint: str | None = None,
        api_key: str | None = None,
        project_name: str | None = None,
        enable_grounding: bool = True,
        bing_connection_id: str | None = None,
        agent_id: str | None = None
    ):
        """Initialize hybrid client with multiple options"""
        self.enable_grounding = enable_grounding
        self.use_ai_foundry = True
        self.agent_id = agent_id
        
        # Try DirectBingClient first (most reliable option)
        try:
            self.direct_bing_client = DirectBingClient()
            logger.info("Direct Bing client initialized successfully")
        except Exception as e:
            logger.warning(f"Direct Bing client initialization failed: {e}")
            self.direct_bing_client = None
        
        # Try ExistingAgentClient if agent_id is provided
        if agent_id or os.getenv('AZURE_AI_FOUNDRY_AGENT_ID'):
            try:
                self.foundry_agent_client = FoundryAgentClient()
                logger.info("Existing agent client initialized successfully")
                self.ai_foundry_client = None  # Don't need the old client
            except Exception as e:
                logger.warning(f"Existing agent client initialization failed: {e}")
                self.foundry_agent_client = None
        else:
            self.foundry_agent_client = None
        
        # Try to initialize AI Foundry client as fallback
        if not self.foundry_agent_client:
            try:
                self.ai_foundry_client = AIFoundryClient(
                    connection_string=connection_string,
                    endpoint=endpoint,
                    api_key=api_key,
                    project_name=project_name,
                    enable_grounding=enable_grounding,
                    bing_connection_id=bing_connection_id
                )
                logger.info("AI Foundry client initialized successfully")
            except Exception as e:
                logger.warning(f"AI Foundry client initialization failed: {e}")
                self.ai_foundry_client = None
                self.use_ai_foundry = False
        else:
            self.ai_foundry_client = None
        
        # Initialize direct OpenAI client as fallback
        try:
            self.openai_client = AzureOpenAI(
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
            )
            self.openai_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')
            logger.info("Direct OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Direct OpenAI client initialization failed: {e}")
            self.openai_client = None
    
    def query(
        self,
        prompt: str,
        thread_id: str | None = None,
        agent_id: str | None = None
    ) -> GroundedResponse | SimpleResponse:
        """
        Query with DirectBing first, then existing agent, then AI Foundry, then fallback to direct OpenAI
        """
        # Try DirectBingClient first (most reliable with web grounding)
        if self.direct_bing_client:
            try:
                logger.info("Attempting query with Direct Bing client")
                return self.direct_bing_client.query(prompt, thread_id, self.enable_grounding)
            except Exception as e:
                logger.warning(f"Direct Bing client query failed: {e}")
                # Continue to other fallbacks
        
        # Try existing agent client if available
        if self.foundry_agent_client:
            try:
                logger.info("Attempting query with foundry agent")
                # Convert the simple string response to the expected format
                response_text = self.foundry_agent_client.chat(prompt)
                
                # Create a compatible response object
                return SimpleResponse(
                    answer=response_text,
                    citations=[],  # Citations would be embedded in the response text
                    thread_id=self.foundry_agent_client.get_thread_id(),
                    run_id="foundry_run",
                    grounding_used=True  # Assume grounding was used if agent responded successfully
                )
            except Exception as e:
                logger.warning(f"Foundry agent query failed: {e}")
                # Continue to other fallbacks
        
        # Try AI Foundry client if available and not disabled
        if self.use_ai_foundry and self.ai_foundry_client:
            try:
                logger.info("Attempting query with AI Foundry")
                return self.ai_foundry_client.query(prompt, thread_id, agent_id)
            except Exception as e:
                logger.warning(f"AI Foundry query failed: {e}")
                # Disable AI Foundry for future queries in this session
                self.use_ai_foundry = False
        
        # Fallback to direct OpenAI
        if self.openai_client:
            logger.info("Using direct OpenAI fallback")
            return self._query_openai_direct(prompt, thread_id)
        
        # If both fail, raise error
        raise Exception("Both AI Foundry and direct OpenAI clients are unavailable")
    
    def _query_openai_direct(self, prompt: str, thread_id: str | None = None) -> SimpleResponse:
        """Query using direct OpenAI client"""
        try:
            # Create a healthcare-focused system message
            system_message = """You are a knowledgeable healthcare assistant helping users find information about
medical topics, treatments, and clinical guidelines. 

When answering:
1. Provide evidence-based information from medical literature and guidelines
2. Use clear, accessible language while maintaining medical accuracy
3. Remind users to consult healthcare professionals for personal medical decisions
4. If you're not certain about recent developments, acknowledge the limitation

Note: All personally identifiable information has been redacted from user queries
for privacy protection."""

            response = self.openai_client.chat.completions.create(
                model=self.openai_deployment,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            # Generate a simple thread ID if none provided
            if thread_id is None:
                thread_id = f"openai_{hash(prompt) % 10000}"
            
            return SimpleResponse(
                answer=answer,
                citations=[],  # Direct OpenAI doesn't provide citations
                thread_id=thread_id,
                run_id=response.id,
                grounding_used=False
            )
            
        except Exception as e:
            logger.error(f"Direct OpenAI query failed: {e}")
            raise
    
    def create_agent(self, **kwargs):
        """Try to create agent with AI Foundry, disable if it fails"""
        if self.use_ai_foundry and self.ai_foundry_client:
            try:
                return self.ai_foundry_client.create_agent(**kwargs)
            except Exception as e:
                logger.warning(f"AI Foundry agent creation failed: {e}")
                self.use_ai_foundry = False
                return None
        return None
    
    def get_or_create_agent(self, **kwargs):
        """Get or create agent, fallback gracefully"""
        if self.use_ai_foundry and self.ai_foundry_client:
            try:
                return self.ai_foundry_client.get_or_create_agent(**kwargs)
            except Exception as e:
                logger.warning(f"AI Foundry agent get/create failed: {e}")
                self.use_ai_foundry = False
                return None
        return None