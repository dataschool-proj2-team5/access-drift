$ErrorActionPreference = "Stop"

$RESOURCE_GROUP = "dt4_project2_team5"

az deployment group create `
  --resource-group $RESOURCE_GROUP `
  --template-file "$PSScriptRoot\main.bicep" `
  --parameters "$PSScriptRoot\main.bicepparam"
