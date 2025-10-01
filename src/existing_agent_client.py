"""
AI Foundry client that uses existing agent with Bing grounding
"""
import logging
from dataclasses import dataclass
from typing import Any
import os
from dotenv import load_dotenv

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    MessageRole,
    RunStatus
)
from azure.identity import DefaultAzureCredential

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class GroundedResponse:
    """Response from AI Foundry Agent with grounding information"""
    answer: str
    citations: list[dict[str, Any]]
    thread_id: str
    run_id: str
    grounding_used: bool


class ExistingAgentClient:
    """Client for using existing Azure AI Foundry agent with Bing grounding"""

    def __init__(
        self,
        connection_string: str | None = None,
        agent_id: str | None = None,
        bing_connection_id: str | None = None
    ):
        """
        Initialize client for existing agent

        Args:
            connection_string: Azure AI Foundry project connection string
            agent_id: Existing agent ID from the portal
            bing_connection_id: Bing Grounding connection ID
        """
        self.agent_id = agent_id or os.getenv('AZURE_AI_FOUNDRY_AGENT_ID')
        self.bing_connection_id = bing_connection_id or os.getenv('BING_CONNECTION_ID')
        
        if not self.agent_id:
            raise ValueError("Agent ID must be provided or set in AZURE_AI_FOUNDRY_AGENT_ID")
        
        # Initialize client based on connection string
        if connection_string:
            # Parse connection string to extract endpoint
            parts = dict(item.split('=', 1) for item in connection_string.split(';') if '=' in item)
            endpoint = parts.get('endpoint')
            if not endpoint:
                raise ValueError("Connection string must contain 'endpoint' parameter")
            
            self.project_client = AIProjectClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )
        else:
            raise ValueError("Must provide connection_string")

        logger.info(f"ExistingAgentClient initialized: agent_id={self.agent_id}, bing_connection={self.bing_connection_id}")

    def create_thread(self):
        """Create a new conversation thread"""
        try:
            thread = self.project_client.agents.threads.create()
            logger.debug(f"Thread created: {thread.id}")
            return thread
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}", exc_info=True)
            raise

    def query(
        self,
        prompt: str,
        thread_id: str | None = None,
        agent_id: str | None = None
    ) -> GroundedResponse:
        """
        Send a query to the existing agent and get grounded response

        Args:
            prompt: User query (should be redacted if contains PII)
            thread_id: Optional existing thread ID
            agent_id: Optional override for agent ID

        Returns:
            GroundedResponse with answer and citations
        """
        try:
            # Use the configured agent ID
            target_agent_id = agent_id or self.agent_id
            
            # Create or use existing thread
            if thread_id:
                try:
                    thread = self.project_client.agents.threads.get(thread_id)
                except:
                    # If thread doesn't exist, create new one
                    thread = self.create_thread()
            else:
                thread = self.create_thread()

            # Add user message to thread
            message = self.project_client.agents.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=prompt
            )
            logger.debug(f"Message added to thread {thread.id}")

            # Run the agent
            run = self.project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=target_agent_id
            )

            logger.info(f"Run completed: {run.id}, status={run.status}")

            # Check run status
            if run.status == RunStatus.FAILED:
                error_msg = f"Run failed: {getattr(run, 'last_error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Get messages from thread
            messages = self.project_client.agents.messages.list(thread_id=thread.id)

            # Extract the latest assistant message
            assistant_messages = [
                msg for msg in messages
                if msg.role == MessageRole.ASSISTANT
            ]

            if not assistant_messages:
                raise Exception("No response from assistant")

            latest_message = assistant_messages[0]

            # Extract text content
            answer = ""
            for content in latest_message.content:
                if hasattr(content, 'text'):
                    answer += content.text.value

            # Extract citations if grounding was used
            citations = []
            grounding_used = False

            # Check if message has annotations (citations)
            for content in latest_message.content:
                if hasattr(content, 'text') and hasattr(content.text, 'annotations'):
                    for annotation in content.text.annotations:
                        if hasattr(annotation, 'url'):
                            citations.append({
                                'text': annotation.text,
                                'url': annotation.url,
                                'title': getattr(annotation, 'title', 'Web Source')
                            })
                            grounding_used = True

            logger.info(
                f"Query processed: {len(citations)} citations, "
                f"grounding_used={grounding_used}"
            )

            return GroundedResponse(
                answer=answer,
                citations=citations,
                thread_id=thread.id,
                run_id=run.id,
                grounding_used=grounding_used
            )

        except Exception as e:
            logger.error(f"Error during query: {str(e)}", exc_info=True)
            raise

    def delete_thread(self, thread_id: str):
        """Delete a thread"""
        try:
            self.project_client.agents.threads.delete(thread_id)
            logger.debug(f"Thread deleted: {thread_id}")
        except Exception as e:
            logger.error(f"Error deleting thread: {str(e)}", exc_info=True)
            raise