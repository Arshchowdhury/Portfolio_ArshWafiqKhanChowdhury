// ============================================================
// MODULE: Azure Key Vault — RetailIQ Sales Agent
// Centralised secret management for all RetailIQ service
// credentials. All services authenticate via Managed Identity.
//
// Secrets provisioned post-deployment:
//   retailiq-openai-endpoint
//   retailiq-search-endpoint
//   retailiq-search-index-name
//   retailiq-storage-connection
//   retailiq-copilot-studio-secret
// ============================================================

@description('Name of the Key Vault')
param keyVaultName string

@description('Azure region for deployment')
param location string

@description('Object ID of the agent application managed identity')
param agentManagedIdentityObjectId string

@description('Object ID of the indexing pipeline managed identity')
param indexerManagedIdentityObjectId string

@description('Resource tags')
param tags object = {}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

resource agentSecretsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, agentManagedIdentityObjectId, 'secrets-reader')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'
    )
    principalId: agentManagedIdentityObjectId
    principalType: 'ServicePrincipal'
  }
}

resource indexerSecretsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, indexerManagedIdentityObjectId, 'secrets-reader')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'
    )
    principalId: indexerManagedIdentityObjectId
    principalType: 'ServicePrincipal'
  }
}

resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${keyVaultName}-diagnostics'
  scope: keyVault
  properties: {
    logs: [
      {
        categoryGroup: 'audit'
        enabled: true
        retentionPolicy: { enabled: true, days: 365 }
      }
    ]
  }
}

output keyVaultId string = keyVault.id
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
