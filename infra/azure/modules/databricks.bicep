param location string
param workspaceName string
param tags object

resource workspace 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name: workspaceName
  location: location
  tags: tags
  sku: {
    name: 'trial'
  }
  properties: {
    managedResourceGroupId: '${subscription().id}/resourceGroups/${workspaceName}-managed'
  }
}

output workspaceUrl string = workspace.properties.workspaceUrl
output workspaceId string = workspace.id
