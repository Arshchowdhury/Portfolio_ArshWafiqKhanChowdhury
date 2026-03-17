// ============================================================
// MAIN: CareAssist — Clinical Incident Triage Agent
// Author: Arsh Wafiq Khan Chowdhury
// Portfolio: github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury
//
// Provisions the Azure backend for an aged care clinical
// incident triage agent using Copilot Studio, Azure OpenAI,
// Azure AI Search, Blob Storage, and Key Vault.
//
// Architecture:
//   Staff (Teams) → Copilot Studio → Azure OpenAI (classification)
//   Azure AI Search ← Standards + Procedures (knowledge grounding)
//   SharePoint ← Incident records (via Power Automate)
//   Key Vault ← All credentials (Managed Identity, no hardcoded keys)
//
// Deploy:
//   az deployment group create \
//     --resource-group rg-careassist-prod \
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
param projectName string = 'careassist'

@description('Object ID of the Copilot Studio managed identity')
param agentManagedIdentityObjectId string

@description('Object ID of the indexing pipeline managed identity')
param indexerManagedIdentityObjectId string

@description('GPT-4o tokens per minute capacity (thousands)')
param openAiCapacityTpm int = 20

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
  industry: 'aged-care'
  managedBy: 'bicep'
  owner: 'arsh-wafiq-khan-chowdhury'
  portfolioArtefact: 'true'
}

// ── Azure OpenAI ──────────────────────────────────────────────
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
// Indexes Aged Care Quality Standards and internal procedures
// for in-agent policy lookup and classification context
module aiSearch 'modules/aisearch.bicep' = {
  name: 'deploy-aisearch'
  params: {
    searchServiceName: searchServiceName
    location: location
    sku: searchSku
    indexName: 'careassist-standards'
    tags: tags
  }
}

// ── Blob Storage ──────────────────────────────────────────────
// Ingestion store for regulatory documents and internal procedures
module storage 'modules/storage.bicep' = {
  name: 'deploy-storage'
  params: {
    storageAccountName: storageAccountName
    location: location
    containerName: 'careassist-documents'
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
