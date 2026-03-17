// ============================================================
// MODULE: Azure Blob Storage — CareAssist Incident Agent
// Document ingestion store for Aged Care Quality Standards,
// internal incident procedures, and escalation matrices.
// ============================================================

@description('Name of the storage account')
param storageAccountName string

@description('Azure region for deployment')
param location string

@description('Name of the document container')
param containerName string = 'careassist-documents'

@description('Resource tags')
param tags object = {}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: { name: 'Standard_ZRS' }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: { enabled: true, days: 30 }
    containerDeleteRetentionPolicy: { enabled: true, days: 7 }
    changeFeed: { enabled: true }
    versioning: true
  }
}

resource documentContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
    metadata: {
      purpose: 'careassist-rag-source-documents'
      managedBy: 'ingestion-pipeline'
    }
  }
}

output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output containerName string = documentContainer.name
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob
