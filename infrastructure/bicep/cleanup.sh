#!/bin/bash

##############################################################################
# Healthcare Demo - Infrastructure Cleanup Script
#
# This script safely tears down all Azure resources
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Healthcare Demo - Infrastructure Cleanup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Running 'az login'..."
    az login
fi

# Get current subscription
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_info "Current subscription: ${SUBSCRIPTION_NAME}"
echo ""

# List resource groups with healthcare demo resources
print_info "Finding healthcare demo resource groups..."
echo ""

RESOURCE_GROUPS=$(az group list --query "[?tags.Project=='Healthcare-PII-PHI-Demo'].name" -o tsv)

if [ -z "$RESOURCE_GROUPS" ]; then
    print_warning "No healthcare demo resource groups found"
    read -p "Enter resource group name to delete: " RESOURCE_GROUP
    if [ -z "$RESOURCE_GROUP" ]; then
        print_error "No resource group specified"
        exit 1
    fi
    RESOURCE_GROUPS="$RESOURCE_GROUP"
else
    print_success "Found healthcare demo resource groups:"
    i=1
    declare -a RG_ARRAY
    while IFS= read -r rg; do
        RG_ARRAY+=("$rg")
        echo "  ${i}) ${rg}"
        ((i++))
    done <<< "$RESOURCE_GROUPS"

    echo ""
    read -p "Select resource group to delete [1-${#RG_ARRAY[@]}] or 'all': " CHOICE

    if [ "$CHOICE" = "all" ]; then
        RESOURCE_GROUPS="${RG_ARRAY[*]}"
    elif [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "${#RG_ARRAY[@]}" ]; then
        RESOURCE_GROUPS="${RG_ARRAY[$((CHOICE-1))]}"
    else
        print_error "Invalid choice"
        exit 1
    fi
fi

# Confirm deletion
echo ""
print_warning "=== DANGER ZONE ==="
print_warning "You are about to DELETE the following resource group(s):"
for rg in $RESOURCE_GROUPS; do
    echo "  - ${rg}"
done
echo ""
print_warning "This will permanently delete ALL resources in these groups!"
print_warning "This action CANNOT be undone!"
echo ""

read -p "Type 'DELETE' to confirm: " CONFIRMATION

if [ "$CONFIRMATION" != "DELETE" ]; then
    print_info "Cleanup cancelled"
    exit 0
fi

# Delete resource groups
echo ""
for RESOURCE_GROUP in $RESOURCE_GROUPS; do
    print_info "Deleting resource group: ${RESOURCE_GROUP}"

    if az group delete --name "$RESOURCE_GROUP" --yes --no-wait; then
        print_success "Deletion initiated for ${RESOURCE_GROUP}"
        print_info "Resources are being deleted in the background"
    else
        print_error "Failed to delete ${RESOURCE_GROUP}"
    fi
done

echo ""
print_info "=== Cleanup Summary ==="
echo "Resource group deletion has been initiated."
echo "Resources will be deleted in the background (this may take several minutes)."
echo ""
echo "To monitor deletion status:"
echo "  az group list --output table | grep healthcare"
echo ""

print_success "Cleanup script completed!"
