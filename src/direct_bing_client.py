"""
Direct Bing Search + Azure OpenAI client to provide web grounding
This bypasses the Azure AI Foundry Agents API and provides similar functionality
"""
import logging
import requests
import os
from dataclasses import dataclass
from typing import Any, List, Dict
from dotenv import load_dotenv

from openai import AzureOpenAI

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class GroundedResponse:
    """Response with web grounding information"""
    answer: str
    citations: list[dict[str, Any]]
    thread_id: str
    run_id: str
    grounding_used: bool


class DirectBingClient:
    """Client that combines Bing Search + Azure OpenAI for web grounding"""

    def __init__(
        self,
        azure_openai_endpoint: str | None = None,
        azure_openai_key: str | None = None,
        azure_openai_deployment: str | None = None,
        bing_search_key: str | None = None,
        bing_search_endpoint: str = "https://api.bing.microsoft.com/v7.0/search"
    ):
        """
        Initialize the client with Azure OpenAI and Bing Search
        
        Args:
            azure_openai_endpoint: Azure OpenAI endpoint
            azure_openai_key: Azure OpenAI API key
            azure_openai_deployment: Azure OpenAI deployment name
            bing_search_key: Bing Search API key
            bing_search_endpoint: Bing Search endpoint
        """
        # Azure OpenAI configuration
        self.aoai_endpoint = azure_openai_endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
        self.aoai_key = azure_openai_key or os.getenv('AZURE_OPENAI_API_KEY')
        self.aoai_deployment = azure_openai_deployment or os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        
        # Bing Search configuration
        self.bing_key = bing_search_key or os.getenv('BING_SEARCH_API_KEY')
        self.bing_endpoint = bing_search_endpoint
        
        # Initialize Azure OpenAI client
        if not all([self.aoai_endpoint, self.aoai_key, self.aoai_deployment]):
            raise ValueError("Azure OpenAI credentials not properly configured")
        
        self.openai_client = AzureOpenAI(
            azure_endpoint=self.aoai_endpoint,
            api_key=self.aoai_key,
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
        )
        
        logger.info(f"DirectBingClient initialized with deployment: {self.aoai_deployment}")

    def search_bing(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Search Bing for current information
        
        Args:
            query: Search query
            count: Number of results to return
            
        Returns:
            List of search results with title, url, snippet
        """
        if not self.bing_key:
            logger.warning("Bing Search API key not configured - no web grounding available")
            return []
        
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.bing_key,
                'User-Agent': 'HealthcareDemo/1.0'
            }
            
            params = {
                'q': query,
                'count': count,
                'responseFilter': 'webpages',
                'textDecorations': True,
                'textFormat': 'HTML'
            }
            
            response = requests.get(
                self.bing_endpoint,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'webPages' in data and 'value' in data['webPages']:
                for item in data['webPages']['value']:
                    results.append({
                        'title': item.get('name', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('snippet', ''),
                        'dateLastCrawled': item.get('dateLastCrawled', '')
                    })
            
            logger.info(f"Bing search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []

    def query(
        self,
        prompt: str,
        thread_id: str | None = None,
        enable_grounding: bool = True
    ) -> GroundedResponse:
        """
        Process query with optional web grounding
        
        Args:
            prompt: User query (should be redacted if contains PII)
            thread_id: Optional thread ID for conversation continuity
            enable_grounding: Whether to use web search for grounding
            
        Returns:
            GroundedResponse with answer and citations
        """
        citations = []
        grounding_used = False
        context = ""
        
        # Step 1: Web search if grounding is enabled
        if enable_grounding and self.bing_key:
            search_results = self.search_bing(prompt)
            
            if search_results:
                grounding_used = True
                citations = [
                    {
                        'title': result['title'],
                        'url': result['url'],
                        'snippet': result['snippet']
                    }
                    for result in search_results
                ]
                
                # Build context from search results
                context = "\\n\\nRecent information from web search:\\n"
                for i, result in enumerate(search_results, 1):
                    context += f"[{i}] {result['title']}\\n{result['snippet']}\\n"
                context += "\\nPlease use this current information to provide an accurate, up-to-date response.\\n"
        
        # Step 2: Generate response with Azure OpenAI
        system_message = """You are a knowledgeable healthcare assistant helping users find information about
medical topics, treatments, and clinical guidelines.

When answering:
1. Provide evidence-based information from medical literature and guidelines
2. Use clear, accessible language while maintaining medical accuracy
3. Remind users to consult healthcare professionals for personal medical decisions
4. If web search results are provided, prioritize current information from reputable sources
5. Reference specific sources when available

Note: All personally identifiable information has been redacted from user queries for privacy protection."""
        
        try:
            messages = [
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': prompt + context}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self.aoai_deployment,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            # Generate thread ID if none provided
            if thread_id is None:
                thread_id = f"direct_{hash(prompt) % 10000}"
            
            logger.info(
                f"Query processed: grounding_used={grounding_used}, "
                f"citations={len(citations)}"
            )
            
            return GroundedResponse(
                answer=answer,
                citations=citations,
                thread_id=thread_id,
                run_id=response.id,
                grounding_used=grounding_used
            )
            
        except Exception as e:
            logger.error(f"Azure OpenAI query failed: {e}")
            raise