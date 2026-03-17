// ============================================================
// MAIN: RetailIQ — AI Sales Assistant Agent
// Author: Arsh Wafiq Khan Chowdhury
// Portfolio: github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury
//
// Provisions the Azure backend for a retail sales assistant
// agent using Copilot Studio, Azure OpenAI, Azure AI Search,
// Blob Storage, and Key Vault.
//
// Deploy:
//   az deployment group create \
//     --resource-group rg-retailiq-prod \
//     --template-file main.bicep \
//     --parameters @parameters.json
// ============================================================

targetScope = 'resourceGroup'

@description('Deployment environment')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Project identifier')
param projectName string = 'retailiq'

@description('Object ID of the Copilot Studio managed identity')
param agentManagedIdentityObjectId string

@description('Object ID of the indexing pipeline managed identity')
param indexerManagedIdentityObjectId string

@description('GPT-4o tokens per minute capacity (thousands)')
param openAiCapacityTpm int = 30

@description('AI Search SKU')
@allowed(['basic', 'standard'])
param searchSku string = 'standard'

var suffix = '${projectName}-${environment}'
var openAiName = 'oai-${suffix}'
var searchServiceName = 'srch-${suffix}'
var storageAccountName = 'st${projectName}${environment}'
var keyVaultName = 'kv-${suffix}'

var tags = {
  project: projectName
  environment: environment
  industry: 'retail'
  managedBy: 'bicep'
  owner: 'arsh-wafiq-khan-chowdhury'
  portfolioArtefact: 'true'
}

// ── Azure OpenAI ──────────────────────────────────────────────
// Higher TPM than CareAssist — retail queries are higher volume
module openAi 'modules/openai.bicep' = {
  name: 'deploy-openai'
  params: {
    openAiName: openAiName
    location: location
    deploymentName: 'gpt-4o'
    capacityTpm: openAiCapacityTpm
    tags: tags
  }
}

// ── Azure AI Search ───────────────────────────────────────────
// Indexes product catalogue (8,000 SKUs), pricing tiers, spec sheets
// SKU stored as filterable metadata field for direct product lookups
module aiSearch 'modules/aisearch.bicep' = {
  name: 'deploy-aisearch'
  params: {
    searchServiceName: searchServiceName
    location: location
    sku: searchSku
    indexName: 'retailiq-products'
    tags: tags
  }
}

// ── Blob Storage ──────────────────────────────────────────────
// Product catalogue PDFs, pricing CSVs, spec sheets
// Change feed enabled for event-driven re-indexing on price updates
module storage 'modules/storage.bicep' = {
  name: 'deploy-storage'
  params: {
    storageAccountName: storageAccountName
    location: location
    containerName: 'retailiq-catalogue'
    tags: tags
  }
}

// ── Key Vault ─────────────────────────────────────────────────
module keyVault 'modules/keyvault.bicep' = {
  name: 'deploy-keyvault'
  dependsOn: [openAi, aiSearch, storage]
  params: {
    keyVaultName: keyVaultName
    location: location
    agentManagedIdentityObjectId: agentManagedIdentityObjectId
    indexerManagedIdentityObjectId: indexerManagedIdentityObjectId
    tags: tags
  }
}

// ── RBAC: AI Search → Storage ─────────────────────────────────
resource searchStorageAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.outputs.storageAccountId, searchServiceName, 'blob-reader')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    )
    principalId: aiSearch.outputs.searchServiceResourceId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [storage, aiSearch]
}

// ── Outputs ───────────────────────────────────────────────────
output openAiEndpoint string = openAi.outputs.openAiEndpoint
output openAiDeploymentName string = openAi.outputs.deploymentName
output searchEndpoint string = aiSearch.outputs.searchServiceEndpoint
output searchIndexName string = aiSearch.outputs.indexName
output storageBlobEndpoint string = storage.outputs.blobEndpoint
output keyVaultUri string = keyVault.outputs.keyVaultUri
