"""
Document embedding service for the agri-civic intelligence platform.
Provides high-level document processing and embedding operations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
from datetime import datetime

from app.services.vector_db_factory import get_vector_db
from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class DocumentEmbeddingService:
    """Service for document embedding and retrieval operations."""

    def __init__(self):
        """Initialize the document embedding service."""
        self.vector_db = get_vector_db()

    def _generate_document_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique document ID based on content and metadata."""
        # Create a hash of content and key metadata fields
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]

        # Include key metadata in ID generation
        key_fields = ["source", "category", "crop", "scheme_type"]
        metadata_str = "_".join(
            [
                str(metadata.get(field, ""))
                for field in key_fields
                if metadata.get(field)
            ]
        )

        if metadata_str:
            return f"{metadata_str}_{content_hash}"
        else:
            return f"doc_{content_hash}"

    def add_agricultural_knowledge(
        self,
        content: str,
        crop: Optional[str] = None,
        category: str = "general",
        source: str = "unknown",
        language: str = "en",
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add agricultural knowledge document to the vector database."""

        metadata = {
            "source": source,
            "category": category,
            "language": language,
            "added_at": datetime.now().isoformat(),
            "document_type": "agricultural_knowledge",
        }

        if crop:
            metadata["crop"] = crop

        if additional_metadata:
            metadata.update(additional_metadata)

        doc_id = self._generate_document_id(content, metadata)

        try:
            self.vector_db.add_documents(
                "agricultural_knowledge", [content], [metadata], [doc_id]
            )

            logger.info(f"Added agricultural knowledge document: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add agricultural knowledge document: {e}")
            raise

    def add_government_scheme(
        self,
        content: str,
        scheme_name: str,
        scheme_type: str = "general",
        eligibility: Optional[str] = None,
        benefits: Optional[str] = None,
        source: str = "government_portal",
        language: str = "en",
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add government scheme document to the vector database."""

        metadata = {
            "source": source,
            "scheme_name": scheme_name,
            "scheme_type": scheme_type,
            "category": "government_scheme",
            "language": language,
            "added_at": datetime.now().isoformat(),
            "document_type": "government_scheme",
        }

        if eligibility:
            metadata["eligibility"] = eligibility
        if benefits:
            metadata["benefits"] = benefits

        if additional_metadata:
            metadata.update(additional_metadata)

        doc_id = self._generate_document_id(content, metadata)

        try:
            self.vector_db.add_documents(
                "government_schemes", [content], [metadata], [doc_id]
            )

            logger.info(f"Added government scheme document: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add government scheme document: {e}")
            raise

    def add_market_intelligence(
        self,
        content: str,
        crop: Optional[str] = None,
        region: Optional[str] = None,
        price_range: Optional[str] = None,
        forecast_period: Optional[str] = None,
        source: str = "market_data",
        language: str = "en",
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add market intelligence document to the vector database."""

        metadata = {
            "source": source,
            "category": "market_intelligence",
            "language": language,
            "added_at": datetime.now().isoformat(),
            "document_type": "market_intelligence",
        }

        if crop:
            metadata["crop"] = crop
        if region:
            metadata["region"] = region
        if price_range:
            metadata["price_range"] = price_range
        if forecast_period:
            metadata["forecast_period"] = forecast_period

        if additional_metadata:
            metadata.update(additional_metadata)

        doc_id = self._generate_document_id(content, metadata)

        try:
            self.vector_db.add_documents(
                "market_intelligence", [content], [metadata], [doc_id]
            )

            logger.info(f"Added market intelligence document: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add market intelligence document: {e}")
            raise

    def add_disease_information(
        self,
        content: str,
        crop: str,
        disease_name: str,
        symptoms: Optional[str] = None,
        treatment: Optional[str] = None,
        prevention: Optional[str] = None,
        source: str = "agricultural_extension",
        language: str = "en",
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add crop disease information to the vector database."""

        metadata = {
            "source": source,
            "crop": crop,
            "disease_name": disease_name,
            "category": "disease_management",
            "language": language,
            "added_at": datetime.now().isoformat(),
            "document_type": "disease_information",
        }

        if symptoms:
            metadata["symptoms"] = symptoms
        if treatment:
            metadata["treatment"] = treatment
        if prevention:
            metadata["prevention"] = prevention

        if additional_metadata:
            metadata.update(additional_metadata)

        doc_id = self._generate_document_id(content, metadata)

        try:
            self.vector_db.add_documents(
                "crop_diseases", [content], [metadata], [doc_id]
            )

            logger.info(f"Added disease information document: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add disease information document: {e}")
            raise

    def search_agricultural_knowledge(
        self,
        query: str,
        crop: Optional[str] = None,
        category: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search agricultural knowledge documents."""

        where_filter = {}
        if crop:
            where_filter["crop"] = crop
        if category:
            where_filter["category"] = category

        try:
            results = self.vector_db.query_documents(
                "agricultural_knowledge",
                query,
                n_results=n_results,
                where=where_filter if where_filter else None,
            )

            return self._format_search_results(results)

        except Exception as e:
            logger.error(f"Failed to search agricultural knowledge: {e}")
            raise

    def search_government_schemes(
        self,
        query: str,
        scheme_type: Optional[str] = None,
        eligibility: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search government scheme documents."""

        where_filter = {}
        if scheme_type:
            where_filter["scheme_type"] = scheme_type
        if eligibility:
            where_filter["eligibility"] = eligibility

        try:
            results = self.vector_db.query_documents(
                "government_schemes",
                query,
                n_results=n_results,
                where=where_filter if where_filter else None,
            )

            return self._format_search_results(results)

        except Exception as e:
            logger.error(f"Failed to search government schemes: {e}")
            raise

    def search_market_intelligence(
        self,
        query: str,
        crop: Optional[str] = None,
        region: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search market intelligence documents."""

        where_filter = {}
        if crop:
            where_filter["crop"] = crop
        if region:
            where_filter["region"] = region

        try:
            results = self.vector_db.query_documents(
                "market_intelligence",
                query,
                n_results=n_results,
                where=where_filter if where_filter else None,
            )

            return self._format_search_results(results)

        except Exception as e:
            logger.error(f"Failed to search market intelligence: {e}")
            raise

    def search_disease_information(
        self,
        query: str,
        crop: Optional[str] = None,
        disease_name: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search crop disease information."""

        where_filter = {}
        if crop:
            where_filter["crop"] = crop
        if disease_name:
            where_filter["disease_name"] = disease_name

        try:
            results = self.vector_db.query_documents(
                "crop_diseases",
                query,
                n_results=n_results,
                where=where_filter if where_filter else None,
            )

            return self._format_search_results(results)

        except Exception as e:
            logger.error(f"Failed to search disease information: {e}")
            raise

    def hybrid_search(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        n_results_per_collection: int = 3,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform hybrid search across multiple collections."""

        if collections is None:
            collections = [
                "agricultural_knowledge",
                "government_schemes",
                "market_intelligence",
                "crop_diseases",
            ]

        results = {}

        for collection in collections:
            try:
                collection_results = self.vector_db.query_documents(
                    collection, query, n_results=n_results_per_collection
                )

                results[collection] = self._format_search_results(collection_results)

            except Exception as e:
                logger.warning(f"Failed to search collection {collection}: {e}")
                results[collection] = []

        return results

    def _format_search_results(
        self, raw_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Format raw ChromaDB results into a more usable format."""

        formatted_results = []

        if not raw_results.get("documents") or not raw_results["documents"][0]:
            return formatted_results

        documents = raw_results["documents"][0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]
        ids = raw_results.get("ids", [[]])[0]

        for i, document in enumerate(documents):
            result = {
                "id": ids[i] if i < len(ids) else f"doc_{i}",
                "content": document,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "similarity_score": 1 - distances[i] if i < len(distances) else 0.0,
            }
            formatted_results.append(result)

        return formatted_results

    def get_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collections."""

        collections = [
            "agricultural_knowledge",
            "government_schemes",
            "market_intelligence",
            "crop_diseases",
            "pest_management",
        ]

        stats = {}

        for collection_name in collections:
            try:
                info = self.vector_db.get_collection_info(collection_name)
                stats[collection_name] = info
            except Exception as e:
                logger.warning(f"Failed to get stats for {collection_name}: {e}")
                stats[collection_name] = {"error": str(e)}

        return stats

    def bulk_add_documents(
        self, collection_name: str, documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Bulk add documents to a collection."""

        contents = []
        metadatas = []
        ids = []

        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_id = doc.get("id") or self._generate_document_id(content, metadata)

            # Add timestamp if not present
            if "added_at" not in metadata:
                metadata["added_at"] = datetime.now().isoformat()

            contents.append(content)
            metadatas.append(metadata)
            ids.append(doc_id)

        try:
            self.vector_db.add_documents(collection_name, contents, metadatas, ids)

            logger.info(f"Bulk added {len(documents)} documents to {collection_name}")
            return ids

        except Exception as e:
            logger.error(f"Failed to bulk add documents to {collection_name}: {e}")
            raise


# Global instance
embedding_service = DocumentEmbeddingService()
