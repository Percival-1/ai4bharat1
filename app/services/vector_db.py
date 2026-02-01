"""
ChromaDB integration for vector database operations.
"""

import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ChromaDBService:
    """Service for managing ChromaDB operations."""

    def __init__(self):
        """Initialize ChromaDB client and collections."""
        self.client = None
        self.collections = {}
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client with appropriate settings."""
        try:
            # For development: use persistent local storage
            if settings.environment == "development":
                self.client = chromadb.PersistentClient(
                    path="./data/chroma_db",
                    settings=Settings(anonymized_telemetry=False, allow_reset=True),
                )
            else:
                # For production: use HTTP client to connect to ChromaDB server
                self.client = chromadb.HttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                    settings=Settings(anonymized_telemetry=False),
                )

            # Initialize embedding function
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key, model_name="text-embedding-ada-002"
            )

            logger.info("ChromaDB client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise

    def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
        """Get or create a ChromaDB collection."""
        if collection_name not in self.collections:
            try:
                self.collections[collection_name] = (
                    self.client.get_or_create_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"description": f"Collection for {collection_name}"},
                    )
                )
                logger.info(f"Collection '{collection_name}' ready")
            except Exception as e:
                logger.error(f"Failed to create collection '{collection_name}': {e}")
                raise

        return self.collections[collection_name]

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """Add documents to a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(f"Added {len(documents)} documents to '{collection_name}'")
        except Exception as e:
            logger.error(f"Failed to add documents to '{collection_name}': {e}")
            raise

    def query_documents(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query documents from a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.query(
                query_texts=[query_text], n_results=n_results, where=where
            )

            logger.info(
                f"Retrieved {len(results['documents'][0])} results from '{collection_name}'"
            )
            return results

        except Exception as e:
            logger.error(f"Failed to query '{collection_name}': {e}")
            raise

    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Update existing documents in a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.update(ids=ids, documents=documents, metadatas=metadatas)
            logger.info(f"Updated {len(ids)} documents in '{collection_name}'")
        except Exception as e:
            logger.error(f"Failed to update documents in '{collection_name}': {e}")
            raise

    def delete_documents(self, collection_name: str, ids: List[str]) -> None:
        """Delete documents from a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from '{collection_name}'")
        except Exception as e:
            logger.error(f"Failed to delete documents from '{collection_name}': {e}")
            raise

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata,
            }
        except Exception as e:
            logger.error(f"Failed to get info for '{collection_name}': {e}")
            raise

    def reset_collection(self, collection_name: str) -> None:
        """Reset (clear all data from) a collection."""
        try:
            if collection_name in self.collections:
                del self.collections[collection_name]

            # Delete and recreate the collection
            try:
                self.client.delete_collection(name=collection_name)
            except:
                pass  # Collection might not exist

            self.get_or_create_collection(collection_name)
            logger.info(f"Reset collection '{collection_name}'")

        except Exception as e:
            logger.error(f"Failed to reset collection '{collection_name}': {e}")
            raise


# Global instance
chroma_service = ChromaDBService()
