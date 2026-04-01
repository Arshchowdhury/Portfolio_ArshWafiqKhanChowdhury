"""
Azure AI Search index schema — meridian-ai-governance.

Schema matches the Deployment Runbook (docs/05_Deployment_Runbook.md).
Requires Azure AI Search Basic tier or above for the semantic ranker;
the Free tier supports hybrid search but not semantic re-ranking,
which is the most important layer for governance query accuracy.
"""

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
)

from config.settings import settings


def get_index_client() -> SearchIndexClient:
    return SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=AzureKeyCredential(settings.azure_search_key),
    )


def build_index_definition() -> SearchIndex:
    """
    Define the search index schema.

    Fields mirror the schema in the Deployment Runbook with the addition of
    content_vector for hybrid search and chunk metadata for debugging.
    """
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),
        SimpleField(
            name="sourceUrl",
            type=SearchFieldDataType.String,
            retrievable=True,
        ),
        SimpleField(
            name="author",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True,
        ),
        SimpleField(
            name="lastModified",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
            retrievable=True,
        ),
        SimpleField(
            name="chunkIndex",
            type=SearchFieldDataType.Int32,
            retrievable=True,
        ),
        SimpleField(
            name="totalChunks",
            type=SearchFieldDataType.Int32,
            retrievable=True,
        ),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,  # text-embedding-ada-002
            vector_search_profile_name="hnsw-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters={
                    # m=4 is Azure's default. Increasing to 8 or 16 improves recall
                    # on large corpora but roughly doubles index memory. At ~1,500 chunks
                    # the difference is negligible, so keeping the default.
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine",
                },
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="hnsw-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ],
    )

    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name=settings.semantic_config_name,
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
        ]
    )

    return SearchIndex(
        name=settings.azure_search_index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def create_or_update_index() -> None:
    """Create the index if it doesn't exist, or update it if the schema has changed."""
    client = get_index_client()
    index = build_index_definition()
    result = client.create_or_update_index(index)
    print(f"Index '{result.name}' created/updated successfully.")


def delete_index() -> None:
    """Delete the index and all indexed documents. Primarily used for dev/test resets."""
    client = get_index_client()
    client.delete_index(settings.azure_search_index_name)
    print(f"Index '{settings.azure_search_index_name}' deleted.")


def index_exists() -> bool:
    client = get_index_client()
    try:
        client.get_index(settings.azure_search_index_name)
        return True
    except Exception:
        return False
