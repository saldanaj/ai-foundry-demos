#!/bin/bash

##############################################################################
# Healthcare Demo - Complete Setup Script
#
# This script performs end-to-end setup:
# 1. Deploy Azure infrastructure
# 2. Install Python dependencies
# 3. Validate services
# 4. Launch demo
##############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ ${1}${NC}"; }
print_success() { echo -e "${GREEN}✓ ${1}${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ ${1}${NC}"; }
print_error() { echo -e "${RED}✗ ${1}${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Healthcare Demo - Complete Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Deploy Infrastructure
print_info "Step 1: Deploy Azure Infrastructure"
echo ""
read -p "Deploy Azure infrastructure now? (y/n): " DEPLOY_INFRA

if [ "$DEPLOY_INFRA" = "y" ]; then
    "${PROJECT_ROOT}/infrastructure/bicep/deploy.sh"
    print_success "Infrastructure deployed"
else
    print_warning "Skipping infrastructure deployment"
    print_info "Make sure .env file exists with Azure credentials"
fi

# Step 2: Check .env file
echo ""
print_info "Step 2: Verify Configuration"

ENV_FILE="${PROJECT_ROOT}/.env"
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found"
    print_info "Please create .env file from .env.example"
    exit 1
fi

print_success ".env file found"

# Step 3: Python Environment
echo ""
print_info "Step 3: Setup Python Environment"

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
print_info "Python version: ${PYTHON_VERSION}"

# Check for virtual environment
if [ -d "${PROJECT_ROOT}/venv" ]; then
    print_info "Virtual environment found"
else
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv "${PROJECT_ROOT}/venv"
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source "${PROJECT_ROOT}/venv/bin/activate"
print_success "Virtual environment activated"

# Step 4: Install Dependencies
echo ""
print_info "Step 4: Install Python Dependencies"

pip install --upgrade pip -q
pip install -r "${PROJECT_ROOT}/requirements.txt" -q

print_success "Dependencies installed"

# Step 5: Validate Services
echo ""
print_info "Step 5: Validate Azure Services"
echo ""

if $PYTHON_CMD "${SCRIPT_DIR}/test-services.py"; then
    print_success "Service validation passed"
else
    print_error "Service validation failed"
    print_warning "Review errors above before continuing"
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
fi

# Step 6: Configure Bing Grounding (Manual)
echo ""
print_warning "=== Manual Configuration Required ==="
print_info "Before running the demo, configure Bing Grounding:"
echo ""
echo "1. Open Azure AI Foundry Portal: https://ai.azure.com"
echo "2. Navigate to your project"
echo "3. Go to 'Settings' → 'Tools'"
echo "4. Enable 'Bing Search' tool"
echo "5. Create an agent with Bing Grounding enabled"
echo ""
read -p "Have you completed Bing Grounding setup? (y/n): " BING_SETUP

if [ "$BING_SETUP" != "y" ]; then
    print_warning "Please complete Bing setup before running demo"
    print_info "You can run the demo later with: streamlit run app/streamlit_app.py"
    exit 0
fi

# Step 7: Launch Demo
echo ""
print_info "Step 7: Launch Demo Application"
echo ""
print_success "=== Setup Complete ==="
print_info "Starting Streamlit demo..."
echo ""

cd "${PROJECT_ROOT}"
streamlit run app/streamlit_app.py
