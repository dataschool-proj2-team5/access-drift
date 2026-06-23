#!/bin/bash
set -euo pipefail

RESOURCE_GROUP=dt4_project2_team5

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "$(dirname "$0")/main.bicep" \
  --parameters "$(dirname "$0")/main.bicepparam"
