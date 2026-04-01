from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Azure AI Search
    azure_search_endpoint: str = Field(..., env="AZURE_SEARCH_ENDPOINT")
    azure_search_key: str = Field(..., env="AZURE_SEARCH_KEY")
    azure_search_index_name: str = Field("meridian-ai-governance", env="AZURE_SEARCH_INDEX_NAME")

    # Azure OpenAI
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = Field(..., env="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field("gpt-4o", env="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_embedding_deployment: str = Field("text-embedding-ada-002", env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    azure_openai_api_version: str = Field("2024-02-01", env="AZURE_OPENAI_API_VERSION")

    # Search behaviour
    semantic_config_name: str = Field("semantic-config", env="SEMANTIC_CONFIG_NAME")
    confidence_threshold: float = Field(0.7, env="CONFIDENCE_THRESHOLD")
    top_k_results: int = Field(5, env="TOP_K_RESULTS")

    # Document processing
    knowledge_base_path: str = Field("./knowledge-base", env="KNOWLEDGE_BASE_PATH")
    chunk_size_tokens: int = Field(512, env="CHUNK_SIZE_TOKENS")
    chunk_overlap_ratio: float = Field(0.2, env="CHUNK_OVERLAP_RATIO")

    # Audit
    audit_log_path: str = Field("./audit/audit_log.jsonl", env="AUDIT_LOG_PATH")

    # SharePoint (optional, production only)
    sharepoint_site_url: str = Field("", env="SHAREPOINT_SITE_URL")
    sharepoint_list_name: str = Field("AI-Governance-Audit", env="SHAREPOINT_LIST_NAME")
    sharepoint_tenant_id: str = Field("", env="SHAREPOINT_TENANT_ID")
    sharepoint_client_id: str = Field("", env="SHAREPOINT_CLIENT_ID")
    sharepoint_client_secret: str = Field("", env="SHAREPOINT_CLIENT_SECRET")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
