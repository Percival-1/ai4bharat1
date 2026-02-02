"""
Pinecone vector database integration.
"""

import logging
from typing import List, Dict, Any, Optional
import hashlib
import json

from app.config import get_settings
from app.core.logging import get_logger
from app.services.vector_db_factory import VectorDBInterface

settings = get_settings()
logger = get_logger(__name__)


class PineconeDBService(VectorDBInterface):
    """Service for managing Pinecone vector database operations."""

    def __init__(self):
        """Initialize Pinecone client."""
        self.client = None
        self.index = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Pinecone client with appropriate settings."""
        try:
            import pinecone

            if not settings.pinecone_api_key:
                raise ValueError("Pinecone API key not provided")

            # Initialize Pinecone
            pinecone.init(
                api_key=settings.pinecone_api_key,
                environment=settings.pinecone_environment,
            )

            # Connect to index
            if settings.pinecone_index_name not in pinecone.list_indexes():
                # Create index if it doesn't exist
                pinecone.create_index(
                    name=settings.pinecone_index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                )

            self.index = pinecone.Index(settings.pinecone_index_name)
            logger.info("Pinecone client initialized successfully")

        except ImportError:
            logger.error(
                "Pinecone package not installed. Install with: pip install pinecone-client"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {e}")
            raise

    def get_or_create_collection(self, collection_name: str):
        """Get or create a collection (namespace in Pinecone)."""
        # Pinecone uses namespaces instead of collections
        return collection_name

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """Add documents to a collection (namespace)."""
        try:
            # Generate embeddings (you'd typically use OpenAI API here)
            embeddings = self._generate_embeddings(documents)

            # Prepare vectors for upsert
            vectors = []
            for i, (doc_id, embedding, metadata) in enumerate(
                zip(ids, embeddings, metadatas)
            ):
                # Add document content to metadata
                metadata_with_content = {**metadata, "content": documents[i]}
                vectors.append(
                    {
                        "id": f"{collection_name}_{doc_id}",
                        "values": embedding,
                        "metadata": metadata_with_content,
                    }
                )

            # Upsert vectors to Pinecone
            self.index.upsert(vectors=vectors, namespace=collection_name)
            logger.info(
                f"Added {len(documents)} documents to Pinecone namespace '{collection_name}'"
            )

        except Exception as e:
            logger.error(
                f"Failed to add documents to Pinecone namespace '{collection_name}': {e}"
            )
            raise

    def query_documents(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query documents from a collection (namespace)."""
        try:
            # Generate embedding for query
            query_embedding = self._generate_embeddings([query_text])[0]

            # Build filter if provided
            filter_dict = where if where else {}

            # Query Pinecone
            response = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                namespace=collection_name,
                filter=filter_dict,
                include_metadata=True,
            )

            # Format response to match ChromaDB format
            documents = []
            metadatas = []
            distances = []
            ids = []

            for match in response.matches:
                documents.append(match.metadata.get("content", ""))
                # Remove content from metadata for consistency
                metadata = {k: v for k, v in match.metadata.items() if k != "content"}
                metadatas.append(metadata)
                distances.append(1 - match.score)  # Convert similarity to distance
                ids.append(match.id.replace(f"{collection_name}_", ""))

            return {
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [distances],
                "ids": [ids],
            }

        except Exception as e:
            logger.error(f"Failed to query Pinecone namespace '{collection_name}': {e}")
            raise

    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Update existing documents in a collection."""
        # For Pinecone, update is the same as upsert
        self.add_documents(collection_name, documents, metadatas, ids)

    def delete_documents(self, collection_name: str, ids: List[str]) -> None:
        """Delete documents from a collection."""
        try:
            # Prefix IDs with collection name
            prefixed_ids = [f"{collection_name}_{doc_id}" for doc_id in ids]
            self.index.delete(ids=prefixed_ids, namespace=collection_name)
            logger.info(
                f"Deleted {len(ids)} documents from Pinecone namespace '{collection_name}'"
            )
        except Exception as e:
            logger.error(
                f"Failed to delete documents from Pinecone namespace '{collection_name}': {e}"
            )
            raise

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection (namespace)."""
        try:
            stats = self.index.describe_index_stats()
            namespace_stats = stats.namespaces.get(collection_name, {})

            return {
                "name": collection_name,
                "count": namespace_stats.get("vector_count", 0),
                "metadata": {"type": "pinecone_namespace"},
            }
        except Exception as e:
            logger.error(
                f"Failed to get info for Pinecone namespace '{collection_name}': {e}"
            )
            raise

    def reset_collection(self, collection_name: str) -> None:
        """Reset (clear all data from) a collection."""
        try:
            # Delete all vectors in the namespace
            self.index.delete(delete_all=True, namespace=collection_name)
            logger.info(f"Reset Pinecone namespace '{collection_name}'")
        except Exception as e:
            logger.error(f"Failed to reset Pinecone namespace '{collection_name}': {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Pinecone."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "status": "healthy",
                "client_connected": True,
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "message": "Pinecone is operational",
            }
        except Exception as e:
            logger.error(f"Pinecone health check failed: {e}")
            return {
                "status": "unhealthy",
                "client_connected": False,
                "error": str(e),
                "message": "Pinecone is not operational",
            }

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using OpenAI."""
        try:
            import openai

            if not settings.openai_api_key:
                raise ValueError("OpenAI API key required for embeddings")

            openai.api_key = settings.openai_api_key

            response = openai.Embedding.create(
                input=texts, model="text-embedding-ada-002"
            )

            return [item["embedding"] for item in response["data"]]

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
