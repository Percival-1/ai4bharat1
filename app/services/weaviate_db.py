"""
Weaviate vector database integration.
"""

import logging
from typing import List, Dict, Any, Optional

from app.config import get_settings
from app.core.logging import get_logger
from app.services.vector_db_factory import VectorDBInterface

settings = get_settings()
logger = get_logger(__name__)


class WeaviateDBService(VectorDBInterface):
    """Service for managing Weaviate vector database operations."""

    def __init__(self):
        """Initialize Weaviate client."""
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Weaviate client with appropriate settings."""
        try:
            import weaviate

            # Configure authentication if API key is provided
            auth_config = None
            if settings.weaviate_api_key:
                auth_config = weaviate.AuthApiKey(api_key=settings.weaviate_api_key)

            self.client = weaviate.Client(
                url=settings.weaviate_url, auth_client_secret=auth_config
            )

            logger.info("Weaviate client initialized successfully")

        except ImportError:
            logger.error(
                "Weaviate package not installed. Install with: pip install weaviate-client"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate client: {e}")
            raise

    def get_or_create_collection(self, collection_name: str):
        """Get or create a collection (class in Weaviate)."""
        try:
            class_name = self._format_class_name(collection_name)

            # Check if class exists
            if not self.client.schema.exists(class_name):
                # Create class schema
                class_schema = {
                    "class": class_name,
                    "description": f"Collection for {collection_name}",
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Document content",
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"],
                            "description": "Document metadata",
                        },
                    ],
                    "vectorizer": "text2vec-openai",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "model": "ada",
                            "modelVersion": "002",
                            "type": "text",
                        }
                    },
                }

                self.client.schema.create_class(class_schema)
                logger.info(f"Created Weaviate class '{class_name}'")

            return class_name

        except Exception as e:
            logger.error(
                f"Failed to get/create Weaviate class '{collection_name}': {e}"
            )
            raise

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """Add documents to a collection (class)."""
        try:
            class_name = self.get_or_create_collection(collection_name)

            # Batch import documents
            with self.client.batch as batch:
                batch.batch_size = 100

                for doc_id, document, metadata in zip(ids, documents, metadatas):
                    data_object = {"content": document, "metadata": metadata}

                    batch.add_data_object(
                        data_object=data_object, class_name=class_name, uuid=doc_id
                    )

            logger.info(
                f"Added {len(documents)} documents to Weaviate class '{class_name}'"
            )

        except Exception as e:
            logger.error(
                f"Failed to add documents to Weaviate class '{collection_name}': {e}"
            )
            raise

    def query_documents(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query documents from a collection (class)."""
        try:
            class_name = self._format_class_name(collection_name)

            # Build GraphQL query
            query_builder = (
                self.client.query.get(class_name, ["content", "metadata"])
                .with_near_text({"concepts": [query_text]})
                .with_limit(n_results)
                .with_additional(["certainty", "id"])
            )

            # Add where filter if provided
            if where:
                query_builder = query_builder.with_where(where)

            result = query_builder.do()

            # Format response to match ChromaDB format
            documents = []
            metadatas = []
            distances = []
            ids = []

            if (
                "data" in result
                and "Get" in result["data"]
                and class_name in result["data"]["Get"]
            ):
                for item in result["data"]["Get"][class_name]:
                    documents.append(item.get("content", ""))
                    metadatas.append(item.get("metadata", {}))
                    # Convert certainty to distance (1 - certainty)
                    certainty = item.get("_additional", {}).get("certainty", 0)
                    distances.append(1 - certainty)
                    ids.append(item.get("_additional", {}).get("id", ""))

            return {
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [distances],
                "ids": [ids],
            }

        except Exception as e:
            logger.error(f"Failed to query Weaviate class '{collection_name}': {e}")
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
            class_name = self._format_class_name(collection_name)

            for doc_id, document, metadata in zip(ids, documents, metadatas):
                data_object = {"content": document, "metadata": metadata}

                self.client.data_object.update(
                    data_object=data_object, class_name=class_name, uuid=doc_id
                )

            logger.info(
                f"Updated {len(ids)} documents in Weaviate class '{class_name}'"
            )

        except Exception as e:
            logger.error(
                f"Failed to update documents in Weaviate class '{collection_name}': {e}"
            )
            raise

    def delete_documents(self, collection_name: str, ids: List[str]) -> None:
        """Delete documents from a collection."""
        try:
            class_name = self._format_class_name(collection_name)

            for doc_id in ids:
                self.client.data_object.delete(uuid=doc_id, class_name=class_name)

            logger.info(
                f"Deleted {len(ids)} documents from Weaviate class '{class_name}'"
            )

        except Exception as e:
            logger.error(
                f"Failed to delete documents from Weaviate class '{collection_name}': {e}"
            )
            raise

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection (class)."""
        try:
            class_name = self._format_class_name(collection_name)

            # Get class schema
            schema = self.client.schema.get(class_name)

            # Get object count (this is an approximation)
            result = self.client.query.aggregate(class_name).with_meta_count().do()

            count = 0
            if "data" in result and "Aggregate" in result["data"]:
                aggregate_data = result["data"]["Aggregate"].get(class_name, [])
                if aggregate_data:
                    count = aggregate_data[0].get("meta", {}).get("count", 0)

            return {
                "name": collection_name,
                "count": count,
                "metadata": {"type": "weaviate_class", "schema": schema},
            }

        except Exception as e:
            logger.error(
                f"Failed to get info for Weaviate class '{collection_name}': {e}"
            )
            raise

    def reset_collection(self, collection_name: str) -> None:
        """Reset (clear all data from) a collection."""
        try:
            class_name = self._format_class_name(collection_name)

            # Delete the class (this removes all objects)
            self.client.schema.delete_class(class_name)

            # Recreate the class
            self.get_or_create_collection(collection_name)

            logger.info(f"Reset Weaviate class '{class_name}'")

        except Exception as e:
            logger.error(f"Failed to reset Weaviate class '{collection_name}': {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Weaviate."""
        try:
            # Check if Weaviate is ready
            ready = self.client.is_ready()

            if ready:
                # Get cluster info
                meta = self.client.get_meta()
                return {
                    "status": "healthy",
                    "client_connected": True,
                    "version": meta.get("version", "unknown"),
                    "message": "Weaviate is operational",
                }
            else:
                return {
                    "status": "unhealthy",
                    "client_connected": False,
                    "message": "Weaviate is not ready",
                }

        except Exception as e:
            logger.error(f"Weaviate health check failed: {e}")
            return {
                "status": "unhealthy",
                "client_connected": False,
                "error": str(e),
                "message": "Weaviate is not operational",
            }

    def _format_class_name(self, collection_name: str) -> str:
        """Format collection name to valid Weaviate class name."""
        # Weaviate class names must start with uppercase letter
        formatted = collection_name.replace("_", "").replace("-", "")
        return formatted.capitalize()
