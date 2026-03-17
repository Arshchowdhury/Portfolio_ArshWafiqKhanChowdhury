// ============================================================
// MODULE: Azure Blob Storage
// Purpose: Document ingestion store. Source documents land
//          here before the indexing pipeline chunks, embeds,
//          and loads them into Azure AI Search.
//
// Business rationale: Blob Storage is the ingestion layer
// because it decouples document upload from indexing.
// Operations teams can drop new documents at any time —
// the indexing pipeline runs on a schedule, ensuring the
// agent always reflects the latest approved documents
// without requiring manual agent configuration changes.
// ============================================================

@description('Name of the storage account')
param storageAccountName string

@description('Azure region for deployment')
param location string

@description('Name of the document container')
param containerName string = 'findfield-documents'

@description('Resource tags')
param tags object = {}

// ── Storage Account ───────────────────────────────────────────
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_ZRS'                     // Zone-redundant — survives AZ failure
  }
  properties: {
    accessTier: 'Hot'                        // Documents accessed frequently by indexer
    allowBlobPublicAccess: false             // No anonymous access — documents are internal
    allowSharedKeyAccess: false              // Enforce Azure AD auth — Key Vault manages identity
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Disabled'          // Private endpoint only
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'               // Allows Azure Indexer to access over private network
    }
    encryption: {
      services: {
        blob: { enabled: true, keyType: 'Account' }
      }
      keySource: 'Microsoft.Storage'        // Microsoft-managed keys (upgrade to CMK for regulated)
    }
  }
}

// ── Blob Service Settings ─────────────────────────────────────
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 30                               // 30-day soft delete — accidental deletions recoverable
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    changeFeed: {
      enabled: true                          // Change feed enables event-driven indexing triggers
    }
    versioning: true                         // Document versioning — older chunks traceable
  }
}

// ── Document Container ────────────────────────────────────────
resource documentContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
    metadata: {
      purpose: 'findfield-rag-source-documents'
      managedBy: 'ingestion-pipeline'
    }
  }
}

// ── Lifecycle Management ──────────────────────────────────────
// Move documents to Cool tier after 90 days (indexed, rarely re-accessed)
// Move to Archive after 365 days
resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/managementPolicies@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    policy: {
      rules: [
        {
          name: 'document-lifecycle'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: ['blockBlob']
              prefixMatch: ['${containerName}/']
            }
            actions: {
              baseBlob: {
                tierToCool: { daysAfterModificationGreaterThan: 90 }
                tierToArchive: { daysAfterModificationGreaterThan: 365 }
              }
            }
          }
        }
      ]
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────
output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output containerName string = documentContainer.name
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob
