// ============================================================
// MODULE: Azure OpenAI
// Purpose: Deploys Azure OpenAI account and GPT-4o model
//          deployment for the Apex Query Assistant agent.
//
// Business rationale: GPT-4o is selected over GPT-3.5 because
// complex policy documents require stronger reasoning to
// synthesise accurate, citation-grounded responses. The cost
// premium (~3x) is offset by a projected 60% reduction in
// human escalations, reducing support team load.
// ============================================================

@description('Name of the Azure OpenAI account')
param openAiName string

@description('Azure region for deployment')
param location string

@description('GPT-4o model deployment name')
param deploymentName string = 'gpt-4o'

@description('Tokens per minute capacity (thousands). 30 = 30,000 TPM.')
@minValue(1)
@maxValue(300)
param capacityTpm int = 30

@description('Resource tags')
param tags object = {}

// ── Azure OpenAI Account ─────────────────────────────────────
resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: openAiName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Disabled'          // Private endpoint only — security requirement
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
    disableLocalAuth: true                   // Enforce Azure AD auth — no API key fallback
  }
}

// ── GPT-4o Model Deployment ──────────────────────────────────
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAiAccount
  name: deploymentName
  sku: {
    name: 'GlobalStandard'                   // GlobalStandard for higher TPM limits
    capacity: capacityTpm
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
    versionUpgradeOption: 'NoAutoUpgrade'    // Explicit version pin — prevents silent behaviour changes
    raiPolicyName: 'Microsoft.DefaultV2'     // Content safety policy
  }
}

// ── Diagnostic Settings ──────────────────────────────────────
// Wire up to Log Analytics for monitoring token usage,
// latency, and error rates — essential for governance reporting.
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${openAiName}-diagnostics'
  scope: openAiAccount
  properties: {
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// ── Outputs ──────────────────────────────────────────────────
output openAiEndpoint string = openAiAccount.properties.endpoint
output openAiResourceId string = openAiAccount.id
output deploymentName string = gpt4oDeployment.name
