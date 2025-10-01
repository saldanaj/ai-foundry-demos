#!/bin/bash

##############################################################################
# Healthcare Demo - Azure Infrastructure Deployment Script
#
# This script deploys all required Azure resources using Bicep templates
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Healthcare Demo - Infrastructure Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first:"
    echo "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

print_success "Azure CLI found"

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Running 'az login'..."
    az login
fi

print_success "Logged in to Azure"

# Get current subscription
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_info "Current subscription: ${SUBSCRIPTION_NAME} (${SUBSCRIPTION_ID})"

# Set default parameters file
PARAMETERS_FILE="${SCRIPT_DIR}/parameters.json"

# Allow custom parameters file via command line argument
if [ ! -z "$1" ]; then
    PARAMETERS_FILE="$1"
fi

if [ ! -f "$PARAMETERS_FILE" ]; then
    print_error "Parameters file not found: ${PARAMETERS_FILE}"
    print_info "Please ensure parameters.json exists or provide path to custom file"
    print_info "Usage: ./deploy.sh [path/to/parameters.json]"
    exit 1
fi

print_success "Using parameters file: ${PARAMETERS_FILE}"
ENVIRONMENT=$(jq -r '.parameters.environmentName.value' "$PARAMETERS_FILE")

# Prompt for resource group
echo ""
read -p "Enter resource group name (will be created if doesn't exist): " RESOURCE_GROUP

if [ -z "$RESOURCE_GROUP" ]; then
    print_error "Resource group name cannot be empty"
    exit 1
fi

# Prompt for location (default from parameters file)
DEFAULT_LOCATION=$(jq -r '.parameters.location.value' "$PARAMETERS_FILE")
read -p "Enter location [${DEFAULT_LOCATION}]: " LOCATION
LOCATION=${LOCATION:-$DEFAULT_LOCATION}

# Check if resource group exists
if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Resource group ${RESOURCE_GROUP} already exists"
    read -p "Continue with deployment? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        print_info "Deployment cancelled"
        exit 0
    fi
else
    print_info "Creating resource group: ${RESOURCE_GROUP} in ${LOCATION}"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    print_success "Resource group created"
fi

# Deployment name with timestamp
DEPLOYMENT_NAME="healthcare-demo-$(date +%Y%m%d-%H%M%S)"

echo ""
print_info "=== Deployment Summary ==="
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  Location: ${LOCATION}"
echo "  Environment: ${ENVIRONMENT}"
echo "  Parameters: ${PARAMETERS_FILE}"
echo "  Deployment: ${DEPLOYMENT_NAME}"
echo ""

read -p "Proceed with deployment? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    print_info "Deployment cancelled"
    exit 0
fi

# Validate Bicep template
echo ""
print_info "Validating Bicep template..."
if az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "${SCRIPT_DIR}/main.bicep" \
    --parameters "@${PARAMETERS_FILE}" \
    --output none; then
    print_success "Template validation passed"
else
    print_error "Template validation failed"
    exit 1
fi

# Deploy infrastructure
echo ""
print_info "Starting deployment (this may take 15-20 minutes)..."
print_warning "APIM deployment can take 30-45 minutes if included"
echo ""

DEPLOYMENT_START=$(date +%s)

if az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --template-file "${SCRIPT_DIR}/main.bicep" \
    --parameters "@${PARAMETERS_FILE}" \
    --output none; then

    DEPLOYMENT_END=$(date +%s)
    DEPLOYMENT_TIME=$((DEPLOYMENT_END - DEPLOYMENT_START))

    print_success "Deployment completed in ${DEPLOYMENT_TIME} seconds!"
else
    print_error "Deployment failed"
    exit 1
fi

# Get deployment outputs
echo ""
print_info "Retrieving deployment outputs..."

OUTPUTS=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs \
    --output json)

# Extract key values
LANGUAGE_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.languageServiceEndpoint.value')
LANGUAGE_NAME=$(echo "$OUTPUTS" | jq -r '.languageServiceName.value')
AI_PROJECT_CONNECTION=$(echo "$OUTPUTS" | jq -r '.aiProjectConnectionString.value')
APIM_GATEWAY=$(echo "$OUTPUTS" | jq -r '.apimGatewayUrl.value // empty')

# Get Language Service key
print_info "Retrieving Language Service key..."
LANGUAGE_KEY=$(az cognitiveservices account keys list \
    --resource-group "$RESOURCE_GROUP" \
    --name "$LANGUAGE_NAME" \
    --query key1 -o tsv)

# Display summary
echo ""
print_success "=== Deployment Complete ==="
echo ""
echo "Language Service:"
echo "  Endpoint: ${LANGUAGE_ENDPOINT}"
echo "  Key: ${LANGUAGE_KEY}"
echo ""
echo "AI Foundry:"
echo "  Connection String: ${AI_PROJECT_CONNECTION}"
echo ""

if [ -n "$APIM_GATEWAY" ]; then
    APIM_KEY=$(echo "$OUTPUTS" | jq -r '.apimSubscriptionKey.value')
    echo "API Management:"
    echo "  Gateway URL: ${APIM_GATEWAY}"
    echo "  Subscription Key: ${APIM_KEY}"
    echo ""
fi

# Offer to create .env file
echo ""
read -p "Create/update .env file with these values? (y/n): " CREATE_ENV
if [ "$CREATE_ENV" = "y" ]; then
    ENV_FILE="${PROJECT_ROOT}/.env"

    print_info "Creating .env file at ${ENV_FILE}"

    cat > "$ENV_FILE" << EOF
# Auto-generated by deploy.sh on $(date)
# Deployment: ${DEPLOYMENT_NAME}

# Azure AI Language Service
AZURE_LANGUAGE_ENDPOINT=${LANGUAGE_ENDPOINT}
AZURE_LANGUAGE_KEY=${LANGUAGE_KEY}

# Azure AI Foundry
AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING=${AI_PROJECT_CONNECTION}

# Application Configuration
PII_DETECTION_MODE=redact
PII_CONFIDENCE_THRESHOLD=0.8
ENABLE_WEB_GROUNDING=true
LOG_LEVEL=INFO
EOF

    if [ -n "$APIM_GATEWAY" ]; then
        cat >> "$ENV_FILE" << EOF

# Azure API Management
AZURE_APIM_ENDPOINT=${APIM_GATEWAY}
AZURE_APIM_SUBSCRIPTION_KEY=${APIM_KEY}
EOF
    fi

    print_success ".env file created"
fi

# Next steps
echo ""
print_info "=== Next Steps ==="
echo "1. Configure Bing Grounding in AI Foundry Portal:"
echo "   - Visit: https://ai.azure.com"
echo "   - Navigate to your project"
echo "   - Enable Bing Search tool in agent settings"
echo ""
echo "2. Install dependencies:"
echo "   cd ${PROJECT_ROOT}"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Run the demo:"
echo "   streamlit run app/streamlit_app.py"
echo ""
echo "4. To tear down all resources:"
echo "   az group delete --name ${RESOURCE_GROUP} --yes --no-wait"
echo ""

print_success "Deployment script completed!"
