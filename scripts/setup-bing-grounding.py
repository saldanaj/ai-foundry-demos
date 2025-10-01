#!/usr/bin/env python3
"""
Setup Bing Grounding for Azure AI Foundry Project

This script helps configure Bing Grounding connection after infrastructure deployment.
It verifies the AI Foundry project exists and provides instructions for manual setup.

Requirements:
- Azure AI Foundry project deployed
- Bing Grounding resource created manually in Azure portal
- Azure CLI logged in OR DefaultAzureCredential configured

Usage:
    python scripts/setup-bing-grounding.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


def main():
    """Main setup script"""
    print("=" * 70)
    print("Azure AI Foundry - Bing Grounding Setup")
    print("=" * 70)
    print()

    # Load environment variables
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment from {env_file}")
    else:
        print(f"⚠ No .env file found at {env_file}")
        print("  Please ensure your Azure AI Foundry project is configured.")

    print()

    # Get project connection string
    project_connection = os.getenv("AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING")

    if not project_connection:
        print("❌ Error: AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING not found")
        print()
        print("Please ensure your .env file contains:")
        print("  AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING=<your_connection_string>")
        print()
        sys.exit(1)

    print(f"✓ Found AI Foundry project connection string")
    print()

    # Connect to project
    try:
        print("Connecting to Azure AI Foundry project...")
        credential = DefaultAzureCredential()
        project_client = AIProjectClient.from_connection_string(
            conn_str=project_connection,
            credential=credential
        )
        print("✓ Successfully connected to AI Foundry project")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to AI Foundry project: {e}")
        print()
        print("Please ensure:")
        print("  1. You're logged in to Azure (run: az login)")
        print("  2. Your connection string is correct")
        print("  3. You have access to the project")
        print()
        sys.exit(1)

    # Check for Bing connection
    print("=" * 70)
    print("Bing Grounding Connection Setup")
    print("=" * 70)
    print()
    print("⚠ IMPORTANT: Bing Grounding resource must be created manually")
    print()
    print("Steps to create Bing Grounding resource:")
    print()
    print("1. Register the Bing namespace (if not already done):")
    print("   az provider register --namespace 'Microsoft.Bing'")
    print()
    print("2. Create Bing Grounding resource in Azure Portal:")
    print("   URL: https://portal.azure.com/#create/Microsoft.BingGroundingSearch")
    print()
    print("3. Important:")
    print("   - Create in the SAME resource group as your AI Foundry project")
    print("   - Note the resource name after creation")
    print()
    print("4. In Azure AI Foundry portal (https://ai.azure.com):")
    print("   a. Navigate to your project")
    print("   b. Go to Settings → Connections")
    print("   c. Click '+ New connection'")
    print("   d. Select 'Bing Grounding'")
    print("   e. Choose your Bing Grounding resource")
    print("   f. Name the connection (e.g., 'bing-grounding')")
    print("   g. Click 'Add connection'")
    print()
    print("5. After creating the connection, get the connection ID:")
    print("   - The connection ID will be in this format:")
    print("     /subscriptions/<sub>/resourceGroups/<rg>/providers/")
    print("     Microsoft.CognitiveServices/accounts/<account>/projects/")
    print("     <project>/connections/<connection_name>")
    print()
    print("6. Add to your .env file:")
    print("   BING_CONNECTION_ID=<your_connection_id>")
    print()
    print("=" * 70)
    print()

    bing_connection_id = os.getenv("BING_CONNECTION_ID")

    if bing_connection_id:
        print("✓ Found BING_CONNECTION_ID in environment")
        print(f"  Connection ID: {bing_connection_id}")
        print()
        print("Your application should now be able to use Bing Grounding!")
    else:
        print("⚠ BING_CONNECTION_ID not found in .env file")
        print("  Please complete the steps above and add the connection ID to .env")

    print()
    print("=" * 70)
    print("Setup Instructions Complete")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Follow the instructions above to create Bing Grounding resource")
    print("2. Add BING_CONNECTION_ID to your .env file")
    print("3. Run your Streamlit application:")
    print("   streamlit run app/streamlit_app.py")
    print()


if __name__ == "__main__":
    main()
