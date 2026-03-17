// ============================================================
// MODULE: Azure OpenAI — RetailIQ Sales Agent
// Deploys Azure OpenAI account and GPT-4o model deployment
// for product knowledge retrieval and sales query generation.
// Higher TPM than CareAssist — retail queries are higher volume.
// ============================================================

@description('Name of the Azure OpenAI account')
param openAiName string

@description('Azure region for deployment')
param location string

@description('GPT-4o model deployment name')
param deploymentName string = 'gpt-4o'

@description('Tokens per minute capacity (thousands)')
@minValue(1)
@maxValue(300)
param capacityTpm int = 30

@description('Resource tags')
param tags object = {}

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: openAiName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
    disableLocalAuth: true
  }
}

resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAiAccount
  name: deploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: capacityTpm
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
    versionUpgradeOption: 'NoAutoUpgrade'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

output openAiEndpoint string = openAiAccount.properties.endpoint
output openAiResourceId string = openAiAccount.id
output deploymentName string = gpt4oDeployment.name
