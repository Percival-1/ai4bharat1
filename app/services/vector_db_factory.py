"""
Vector database factory for creating different vector database implementations.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class VectorDBInterface(ABC):
    """Abstract interface for vector database operations."""

    @abstractmethod
    def add_documents(
        self, collection_name: str, documents: list, metadatas: list, ids: list
    ) -> None:
        """Add documents to a collection."""
        pass

    @abstractmethod
    def query_documents(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Query documents from a collection."""
        pass

    @abstractmethod
    def get_or_create_collection(self, collection_name: str):
        """Get or create a collection."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        pass


class VectorDBFactory:
    """Factory for creating vector database instances."""

    @staticmethod
    def create_vector_db() -> VectorDBInterface:
        """Create vector database instance based on configuration."""

        db_type = settings.vector_db_type.lower()

        if db_type == "chromadb":
            from app.services.vector_db import ChromaDBService

            return ChromaDBService()
        elif db_type == "pinecone":
            from app.services.pinecone_db import PineconeDBService

            return PineconeDBService()
        elif db_type == "weaviate":
            from app.services.weaviate_db import WeaviateDBService

            return WeaviateDBService()
        else:
            logger.warning(
                f"Unknown vector DB type: {db_type}, falling back to ChromaDB"
            )
            from app.services.vector_db import ChromaDBService

            return ChromaDBService()


# Global instance - created lazily to avoid circular imports
_vector_db_instance = None


def get_vector_db() -> VectorDBInterface:
    """Get the global vector database instance."""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDBFactory.create_vector_db()
    return _vector_db_instance
