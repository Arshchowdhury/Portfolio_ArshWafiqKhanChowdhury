// ============================================================
// MODULE: Azure AI Search — CareAssist Incident Agent
// Deploys the vector search index for grounding the agent
// in Aged Care Quality Standards and internal procedures.
// ============================================================

@description('Name of the Azure AI Search service')
param searchServiceName string

@description('Azure region for deployment')
param location string

@allowed(['free', 'basic', 'standard', 'standard2', 'standard3'])
param sku string = 'standard'

@minValue(1)
@maxValue(12)
param replicaCount int = 1

@allowed([1, 2, 3, 4, 6, 12])
param partitionCount int = 1

@description('Name of the vector search index')
param indexName string = 'careassist-standards'

@description('Resource tags')
param tags object = {}

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: { name: sku }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'default'
    publicNetworkAccess: 'disabled'
    semanticSearch: 'standard'
    disableLocalAuth: true
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http403'
      }
    }
  }
}

output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'
output searchServiceResourceId string = searchService.id
output indexName string = indexName
