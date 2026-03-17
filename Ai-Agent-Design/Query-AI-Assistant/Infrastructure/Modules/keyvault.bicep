// ============================================================
// MODULE: Azure Key Vault
// Purpose: Centralised secret management for all service
//          credentials used by the FindField agent pipeline.
//
// Business rationale: Storing credentials in Key Vault rather
// than app config or environment variables eliminates the
// primary cause of credential exposure incidents. All service
// principals authenticate via Managed Identity — no secret
// strings exist in any application configuration file.
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

// ── Key Vault ─────────────────────────────────────────────────
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true            // RBAC over access policies — more granular control
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true              // Prevents permanent deletion — compliance requirement
    publicNetworkAccess: 'Disabled'          // Private endpoint only
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

// ── RBAC: Agent Managed Identity → Key Vault Secrets Reader ──
// The agent application reads credentials at runtime via
// Managed Identity — no hardcoded secrets anywhere.
resource agentSecretsReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, agentManagedIdentityObjectId, 'secrets-reader')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets Reader built-in role
    )
    principalId: agentManagedIdentityObjectId
    principalType: 'ServicePrincipal'
  }
}

// ── RBAC: Indexer Managed Identity → Key Vault Secrets Reader ─
resource indexerSecretsReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
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

// ── Secret Placeholders ───────────────────────────────────────
// Secrets are provisioned post-deployment via CI/CD pipeline.
// These placeholder names define the expected secret schema.
//
// Secrets provisioned externally:
//   findfield-openai-endpoint       — Azure OpenAI endpoint URL
//   findfield-search-endpoint       — Azure AI Search endpoint URL
//   findfield-search-index-name     — Target index name
//   findfield-storage-connection    — Storage account connection (Managed Identity preferred)
//   findfield-copilot-studio-secret — Copilot Studio channel secret

// ── Diagnostic Settings ───────────────────────────────────────
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${keyVaultName}-diagnostics'
  scope: keyVault
  properties: {
    logs: [
      {
        categoryGroup: 'audit'               // Audit log: every secret access recorded
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 365                          // 1-year audit retention for compliance
        }
      }
    ]
  }
}

// ── Outputs ───────────────────────────────────────────────────
output keyVaultId string = keyVault.id
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
