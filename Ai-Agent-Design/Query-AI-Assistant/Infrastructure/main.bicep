// ============================================================
// MAIN: Apex Query Assistant — Azure Infrastructure
// Author: Arsh Wafiq Khan Chowdhury
// Portfolio: github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury
//
// Provisions the complete Azure backend for a RAG-powered
// AI agent using Copilot Studio, Azure OpenAI, Azure AI Search,
// Blob Storage, and Key Vault.
//
// Architecture:
//   Documents → Blob Storage → Indexing Pipeline → AI Search
//   User Query → Copilot Studio → OpenAI (RAG grounding) ← AI Search
//   Secrets → Key Vault ← Managed Identity (no hardcoded creds)
//
// Deploy:
//   az deployment group create \
//     --resource-group rg-apex-prod \
//     --template-file main.bicep \
//     --parameters @parameters.json
// ============================================================

targetScope = 'resourceGroup'

// ── Parameters ───────────────────────────────────────────────

@description('Deployment environment')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Project identifier — used in all resource names')
param projectName string = 'apex'

@description('Object ID of the agent application managed identity')
param agentManagedIdentityObjectId string

@description('Object ID of the indexing pipeline managed identity')
param indexerManagedIdentityObjectId string

@description('GPT-4o tokens per minute capacity (thousands)')
param openAiCapacityTpm int = 30

@description('AI Search SKU')
@allowed(['basic', 'standard', 'standard2'])
param searchSku string = 'standard'

// ── Variables ─────────────────────────────────────────────────

var suffix = '${projectName}-${environment}'
var openAiName = 'oai-${suffix}'
var searchServiceName = 'srch-${suffix}'
var storageAccountName = 'st${projectName}${environment}'    // No hyphens — storage account constraint
var keyVaultName = 'kv-${suffix}'

var tags = {
  project: projectName
  environment: environment
  managedBy: 'bicep'
  owner: 'arsh-wafiq-khan-chowdhury'
  portfolioArtefact: 'true'
}

// ── Module: Azure OpenAI ──────────────────────────────────────
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

// ── Module: Azure AI Search ───────────────────────────────────
module aiSearch 'modules/aisearch.bicep' = {
  name: 'deploy-aisearch'
  params: {
    searchServiceName: searchServiceName
    location: location
    sku: searchSku
    indexName: 'apex-documents'
    tags: tags
  }
}

// ── Module: Blob Storage ──────────────────────────────────────
module storage 'modules/storage.bicep' = {
  name: 'deploy-storage'
  params: {
    storageAccountName: storageAccountName
    location: location
    containerName: 'apex-documents'
    tags: tags
  }
}

// ── Module: Key Vault ─────────────────────────────────────────
// Deployed after other modules so resource IDs are available
// for RBAC assignments scoped to each service.
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

// ── RBAC: AI Search → Storage (indexer data access) ──────────
// Azure AI Search indexer reads documents from Blob Storage
// using its system-assigned managed identity.
// 'Storage Blob Data Reader' is the minimum required role.
resource searchIndexerStorageAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.outputs.storageAccountId, searchServiceName, 'blob-reader')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1' // Storage Blob Data Reader
    )
    principalId: aiSearch.outputs.searchServiceResourceId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [storage, aiSearch]
}

// ── RBAC: OpenAI → AI Search (RAG retrieval) ─────────────────
// Azure OpenAI reads the search index at inference time
// to retrieve relevant document chunks for grounding.
resource openAiSearchAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiSearch.outputs.searchServiceResourceId, openAiName, 'search-reader')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '1407120a-92aa-4202-b7e9-c0e197c71c8f' // Search Index Data Reader
    )
    principalId: openAi.outputs.openAiResourceId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [openAi, aiSearch]
}

// ── Outputs ───────────────────────────────────────────────────
// Reference these in CI/CD pipelines and application config.
// All sensitive values (keys, connection strings) are in Key Vault.

output openAiEndpoint string = openAi.outputs.openAiEndpoint
output openAiDeploymentName string = openAi.outputs.deploymentName
output searchEndpoint string = aiSearch.outputs.searchServiceEndpoint
output searchIndexName string = aiSearch.outputs.indexName
output storageBlobEndpoint string = storage.outputs.blobEndpoint
output storageDocumentContainer string = storage.outputs.containerName
output keyVaultUri string = keyVault.outputs.keyVaultUri
