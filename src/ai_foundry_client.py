"""
Azure AI Foundry Agent Service client with Bing Grounding
"""
import logging
from dataclasses import dataclass
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    Agent,
    AgentThread,
    MessageRole,
    RunStatus,
    BingGroundingTool
)
from azure.identity import DefaultAzureCredential


logger = logging.getLogger(__name__)


@dataclass
class GroundedResponse:
    """Response from AI Foundry Agent with grounding information"""
    answer: str
    citations: list[dict[str, Any]]
    thread_id: str
    run_id: str
    grounding_used: bool


class AIFoundryClient:
    """Client for Azure AI Foundry Agent Service with Bing Grounding"""

    def __init__(
        self,
        connection_string: str | None = None,
        endpoint: str | None = None,
        api_key: str | None = None,
        project_name: str | None = None,
        enable_grounding: bool = True,
        bing_connection_id: str | None = None
    ):
        """
        Initialize AI Foundry client

        Args:
            connection_string: Azure AI Foundry project connection string
            endpoint: Alternative - Azure AI Foundry endpoint
            api_key: Alternative - Azure AI Foundry API key
            project_name: Alternative - Azure AI Foundry project name
            enable_grounding: Enable Bing web grounding
            bing_connection_id: Bing Grounding connection ID (required if enable_grounding=True)
        """
        self.enable_grounding = enable_grounding
        self.bing_connection_id = bing_connection_id

        # Initialize client based on provided credentials
        if connection_string:
            self.project_client = AIProjectClient.from_connection_string(
                conn_str=connection_string,
                credential=DefaultAzureCredential()
            )
        elif endpoint and api_key and project_name:
            # Alternative initialization method (if needed)
            # This depends on the specific SDK version
            self.project_client = AIProjectClient(
                credential=DefaultAzureCredential(),
                endpoint=endpoint
            )
        else:
            raise ValueError(
                "Must provide either connection_string or "
                "(endpoint, api_key, project_name)"
            )

        self.agent: Agent | None = None
        logger.info(f"AI Foundry client initialized: grounding={enable_grounding}")

    def create_agent(
        self,
        name: str = "HealthcareAssistant",
        instructions: str | None = None,
        model: str = "gpt-4o"
    ) -> Agent:
        """
        Create an agent with Bing grounding capability

        Args:
            name: Agent name
            instructions: System instructions for the agent
            model: Model deployment name to use

        Returns:
            Created Agent instance
        """
        if instructions is None:
            instructions = """
You are a knowledgeable healthcare assistant helping users find information about
medical topics, treatments, and clinical guidelines. You have access to web search
capabilities to provide up-to-date, evidence-based information.

When answering:
1. Prioritize recent, authoritative sources (medical journals, health organizations)
2. Clearly cite your sources
3. Distinguish between general information and specific medical advice
4. Remind users to consult healthcare professionals for personal medical decisions
5. Use clear, accessible language while maintaining medical accuracy

Note: All personally identifiable information has been redacted from user queries
for privacy protection.
"""

        tools = []
        if self.enable_grounding:
            # Add Bing Grounding tool with connection ID
            if self.bing_connection_id:
                tools.append(BingGroundingTool(connection_id=self.bing_connection_id))
                logger.info(f"Bing Grounding enabled with connection: {self.bing_connection_id}")
            else:
                logger.warning("Bing grounding enabled but no connection ID provided. Grounding may not work.")
                tools.append(BingGroundingTool())

        try:
            self.agent = self.project_client.agents.create_agent(
                model=model,
                name=name,
                instructions=instructions,
                tools=tools if tools else None
            )
            logger.info(f"Agent created: {self.agent.id}, name={name}")
            return self.agent

        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            raise

    def get_or_create_agent(self, **kwargs) -> Agent:
        """Get existing agent or create new one"""
        if self.agent is None:
            self.agent = self.create_agent(**kwargs)
        return self.agent

    def create_thread(self) -> AgentThread:
        """Create a new conversation thread"""
        try:
            thread = self.project_client.agents.create_thread()
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
        Send a query to the agent and get grounded response

        Args:
            prompt: User query (should be redacted if contains PII)
            thread_id: Optional existing thread ID
            agent_id: Optional specific agent ID

        Returns:
            GroundedResponse with answer and citations
        """
        try:
            # Ensure we have an agent
            if agent_id:
                agent = self.project_client.agents.get_agent(agent_id)
            else:
                agent = self.get_or_create_agent()

            # Create or use existing thread
            if thread_id:
                thread = self.project_client.agents.get_thread(thread_id)
            else:
                thread = self.create_thread()

            # Add user message to thread
            message = self.project_client.agents.create_message(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=prompt
            )
            logger.debug(f"Message added to thread {thread.id}")

            # Run the agent
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=agent.id
            )

            logger.info(f"Run completed: {run.id}, status={run.status}")

            # Check run status
            if run.status == RunStatus.FAILED:
                error_msg = f"Run failed: {getattr(run, 'last_error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Get messages from thread
            messages = self.project_client.agents.list_messages(thread_id=thread.id)

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

    def delete_agent(self, agent_id: str | None = None):
        """Delete an agent"""
        try:
            target_id = agent_id or (self.agent.id if self.agent else None)
            if target_id:
                self.project_client.agents.delete_agent(target_id)
                logger.info(f"Agent deleted: {target_id}")
                if self.agent and self.agent.id == target_id:
                    self.agent = None
        except Exception as e:
            logger.error(f"Error deleting agent: {str(e)}", exc_info=True)
            raise

    def delete_thread(self, thread_id: str):
        """Delete a thread"""
        try:
            self.project_client.agents.delete_thread(thread_id)
            logger.debug(f"Thread deleted: {thread_id}")
        except Exception as e:
            logger.error(f"Error deleting thread: {str(e)}", exc_info=True)
            raise
