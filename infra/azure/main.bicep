targetScope = 'resourceGroup'

param location string = 'koreacentral'
param prefix string = 'acdrift'
@description('Azure OpenAI region.')
param openAiLocation string = 'koreacentral'

var tags = {
  project: 'access-drift'
}

module databricks 'modules/databricks.bicep' = {
  name: 'databricks'
  params: {
    location: location
    workspaceName: '${prefix}-dbx'
    tags: tags
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    accountName: '${prefix}adls'
    tags: tags
  }
}

module unityCatalogAccess 'modules/unity-catalog-access.bicep' = {
  name: 'unity-catalog-access'
  params: {
    location: location
    accessConnectorName: '${prefix}-uc-access'
    storageAccountName: storage.outputs.storageAccountName
    storageAccountId: storage.outputs.storageAccountId
    tags: tags
  }
}

module openai 'modules/openai.bicep' = {
  name: 'openai'
  params: {
    location: openAiLocation
    accountName: '${prefix}-oai'
    tags: tags
  }
}

output databricksUrl string = databricks.outputs.workspaceUrl
output storageEndpoint string = storage.outputs.primaryEndpoint
output storageAccountName string = storage.outputs.storageAccountName
output openAiEndpoint string = openai.outputs.endpoint
output unityCatalogAccessConnectorId string = unityCatalogAccess.outputs.accessConnectorId
output unityCatalogManagedIdentityPrincipalId string = unityCatalogAccess.outputs.managedIdentityPrincipalId
