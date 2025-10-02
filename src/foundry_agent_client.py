"""
Simplified Azure AI Foundry Agent Client based on Microsoft documentation patterns.
This follows the official approach for agent integration with web grounding tools.
"""
import os
import logging
import time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)

class FoundryAgentClient:
    """
    Azure AI Foundry Agent Client following Microsoft's recommended patterns.
    This client assumes the agent has been properly configured with Bing grounding tools
    in the Azure AI Foundry portal.
    """
    
    def __init__(self):
        """Initialize the Azure AI Foundry agent client."""
        # Get configuration from environment
        self.connection_string = os.getenv("AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING")
        self.agent_id = os.getenv("AZURE_AI_FOUNDRY_AGENT_ID")
        
        if not self.connection_string:
            raise ValueError("AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING environment variable is required")
        if not self.agent_id:
            raise ValueError("AZURE_AI_FOUNDRY_AGENT_ID environment variable is required")
        
        # Initialize the AI Project client following Microsoft patterns
        try:
            # Parse the connection string to extract endpoint
            # Format: endpoint=https://...;resource_group=...;workspace_name=...;subscription_id=...
            conn_parts = dict(part.split('=', 1) for part in self.connection_string.split(';'))
            endpoint = conn_parts.get('endpoint')
            
            if not endpoint:
                raise ValueError("Invalid connection string format: missing endpoint")
            
            self.project_client = AIProjectClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )
            logger.info("✅ Azure AI Foundry client initialized successfully")
            
            # Create a persistent thread for this session
            self._thread_id = None
            self._create_persistent_thread()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure AI Foundry client: {e}")
            raise
    
    def _create_persistent_thread(self):
        """Create a persistent thread for the session."""
        try:
            agents_client = self.project_client.agents
            thread = agents_client.threads.create()
            self._thread_id = thread.id
            logger.info(f"✅ Created persistent thread: {self._thread_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create thread: {e}")
            raise
    
    def chat(self, message: str) -> str:
        """
        Send a message to the Azure AI Foundry agent and get a response.
        
        Args:
            message (str): The user's message
            
        Returns:
            str: The agent's response with web grounding if available
        """
        try:
            agents_client = self.project_client.agents
            
            # Enhance the message to encourage web search
            enhanced_message = f"{message}\n\nPlease search the web for current information to provide an accurate, up-to-date response."
            
            # Add the user message to the thread
            logger.info(f"📝 Adding message to thread...")
            message_obj = agents_client.messages.create(
                thread_id=self._thread_id,
                role="user",
                content=enhanced_message
            )
            
            # Create a run with the specific agent
            logger.info(f"🚀 Starting agent run...")
            run = agents_client.runs.create(
                thread_id=self._thread_id,
                assistant_id=self.agent_id
            )
            
            # Wait for the run to complete
            logger.info("⏳ Waiting for agent response...")
            max_wait_time = 60  # 60 seconds timeout
            start_time = time.time()
            
            while run.status in ["queued", "in_progress", "requires_action"]:
                if time.time() - start_time > max_wait_time:
                    logger.warning("⏰ Agent response timed out")
                    return "I'm taking longer than expected to respond. Please try again with a simpler question."
                
                time.sleep(2)  # Check every 2 seconds
                
                try:
                    run = agents_client.runs.get(thread_id=self._thread_id, run_id=run.id)
                    logger.debug(f"Run status: {run.status}")
                    
                    # Handle tool calls automatically - Azure AI Foundry manages this
                    if run.status == "requires_action":
                        logger.info("🔧 Agent is using tools (possibly web search)...")
                        
                except Exception as e:
                    logger.warning(f"Error checking run status: {e}")
                    break
            
            # Process the completed run
            if run.status == "completed":
                logger.info("✅ Agent run completed successfully")
                return self._extract_response()
            elif run.status == "failed":
                logger.error(f"❌ Agent run failed: {run.status}")
                error_details = getattr(run, 'last_error', None)
                if error_details:
                    error_message = getattr(error_details, 'message', str(error_details))
                    logger.error(f"Error details: {error_message}")
                return "I encountered an error while processing your request. Please try again."
            else:
                logger.warning(f"⚠️ Unexpected run status: {run.status}")
                return "I'm having trouble processing your request right now. Please try again."
                
        except AzureError as e:
            logger.error(f"❌ Azure API error: {e}")
            return "I'm experiencing connectivity issues. Please try again."
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return "I encountered an unexpected error. Please try again."
    
    def _extract_response(self) -> str:
        """Extract the assistant's response from the thread."""
        try:
            agents_client = self.project_client.agents
            
            # Get all messages from the thread
            messages = agents_client.messages.list(thread_id=self._thread_id)
            
            # Find the latest assistant message
            for message in messages.data:
                if message.role == "assistant":
                    if message.content and len(message.content) > 0:
                        # Extract text content
                        content = message.content[0]
                        
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            response = content.text.value
                            logger.info(f"📄 Response length: {len(response)} characters")
                            
                            # Check for citations (indicates web grounding was used)
                            if hasattr(content.text, 'annotations') and content.text.annotations:
                                logger.info(f"🔗 Response includes {len(content.text.annotations)} web citations")
                                # You could process annotations here to format citations nicely
                            
                            return response
                        elif hasattr(content, 'value'):
                            return content.value
            
            logger.warning("⚠️ No assistant response found in thread")
            return "I processed your request but couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"❌ Error extracting response: {e}")
            return "I generated a response but couldn't retrieve it. Please try again."
    
    def reset_conversation(self):
        """Reset the conversation by creating a new thread."""
        try:
            logger.info("🔄 Resetting conversation...")
            self._create_persistent_thread()
            logger.info("✅ Conversation reset successfully")
        except Exception as e:
            logger.error(f"❌ Failed to reset conversation: {e}")
            raise
    
    def get_thread_id(self) -> str:
        """Get the current thread ID."""
        return self._thread_id