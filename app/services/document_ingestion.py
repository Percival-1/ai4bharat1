"""
Document ingestion pipeline for the agri-civic intelligence platform.
Handles bulk document processing, validation, and knowledge base updates.
"""

import logging
import json
import csv
import os
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime
from pathlib import Path

from app.services.rag_engine import RAGEngine
from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class DocumentIngestionPipeline:
    """Pipeline for ingesting documents into the knowledge base."""

    def __init__(self):
        """Initialize the document ingestion pipeline."""
        self.rag_engine = RAGEngine()
        self.supported_formats = ["json", "csv", "txt"]
        self.batch_size = 50

    def ingest_from_file(
        self,
        file_path: str,
        collection_name: str,
        file_format: Optional[str] = None,
        metadata_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest documents from a file.

        Args:
            file_path: Path to the file containing documents
            collection_name: Target collection name
            file_format: File format (json, csv, txt) - auto-detected if None
            metadata_overrides: Additional metadata to add to all documents

        Returns:
            Ingestion results and statistics
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Auto-detect file format if not provided
            if file_format is None:
                file_format = Path(file_path).suffix.lower().lstrip(".")

            if file_format not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_format}")

            # Parse documents based on format
            documents = list(
                self._parse_file(file_path, file_format, metadata_overrides)
            )

            if not documents:
                return {
                    "total_documents": 0,
                    "processed_documents": 0,
                    "failed_documents": 0,
                    "success_rate": 0.0,
                    "error": "No valid documents found in file",
                }

            # Ingest documents using RAG engine
            results = self.rag_engine.ingest_document_batch(
                documents=documents,
                collection_name=collection_name,
                batch_size=self.batch_size,
            )

            results["source_file"] = file_path
            results["file_format"] = file_format

            logger.info(f"Ingested documents from {file_path} into {collection_name}")
            return results

        except Exception as e:
            logger.error(f"Failed to ingest from file {file_path}: {e}")
            raise

    def _parse_file(
        self,
        file_path: str,
        file_format: str,
        metadata_overrides: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Parse documents from file based on format."""

        if file_format == "json":
            yield from self._parse_json_file(file_path, metadata_overrides)
        elif file_format == "csv":
            yield from self._parse_csv_file(file_path, metadata_overrides)
        elif file_format == "txt":
            yield from self._parse_txt_file(file_path, metadata_overrides)

    def _parse_json_file(
        self, file_path: str, metadata_overrides: Optional[Dict[str, Any]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Parse JSON file containing documents."""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                # Array of documents
                for item in data:
                    doc = self._normalize_document(item, metadata_overrides)
                    if doc:
                        yield doc
            elif isinstance(data, dict):
                if "documents" in data:
                    # Object with documents array
                    for item in data["documents"]:
                        doc = self._normalize_document(item, metadata_overrides)
                        if doc:
                            yield doc
                else:
                    # Single document object
                    doc = self._normalize_document(data, metadata_overrides)
                    if doc:
                        yield doc

        except Exception as e:
            logger.error(f"Failed to parse JSON file {file_path}: {e}")
            raise

    def _parse_csv_file(
        self, file_path: str, metadata_overrides: Optional[Dict[str, Any]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Parse CSV file containing documents."""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Convert CSV row to document format
                    content = (
                        row.get("content") or row.get("text") or row.get("document")
                    )
                    if not content:
                        logger.warning(f"Row missing content field: {row}")
                        continue

                    # Build metadata from other columns
                    metadata = {
                        k: v
                        for k, v in row.items()
                        if k not in ["content", "text", "document"]
                    }

                    if metadata_overrides:
                        metadata.update(metadata_overrides)

                    doc = {"content": content, "metadata": metadata}

                    yield doc

        except Exception as e:
            logger.error(f"Failed to parse CSV file {file_path}: {e}")
            raise

    def _parse_txt_file(
        self, file_path: str, metadata_overrides: Optional[Dict[str, Any]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Parse plain text file as a single document."""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                logger.warning(f"Empty text file: {file_path}")
                return

            metadata = {
                "source": os.path.basename(file_path),
                "file_path": file_path,
                "document_type": "text_file",
            }

            if metadata_overrides:
                metadata.update(metadata_overrides)

            yield {"content": content, "metadata": metadata}

        except Exception as e:
            logger.error(f"Failed to parse text file {file_path}: {e}")
            raise

    def _normalize_document(
        self,
        raw_doc: Dict[str, Any],
        metadata_overrides: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Normalize document structure."""

        # Extract content
        content = (
            raw_doc.get("content")
            or raw_doc.get("text")
            or raw_doc.get("document")
            or raw_doc.get("body")
        )

        if not content:
            logger.warning(f"Document missing content: {raw_doc}")
            return None

        # Extract or build metadata
        metadata = raw_doc.get("metadata", {})

        # Add other fields as metadata
        for key, value in raw_doc.items():
            if key not in ["content", "text", "document", "body", "metadata"]:
                metadata[key] = value

        # Apply metadata overrides
        if metadata_overrides:
            metadata.update(metadata_overrides)

        # Ensure required metadata fields
        if "source" not in metadata:
            metadata["source"] = "ingestion_pipeline"

        if "added_at" not in metadata:
            metadata["added_at"] = datetime.now().isoformat()

        return {"content": str(content), "metadata": metadata}

    def ingest_agricultural_knowledge_samples(self) -> Dict[str, Any]:
        """Ingest sample agricultural knowledge documents."""

        sample_documents = [
            {
                "content": "Wheat cultivation requires well-drained soil with pH between 6.0-7.5. Sowing should be done in November-December for optimal yield. Use 100-120 kg seeds per hectare.",
                "metadata": {
                    "source": "agricultural_extension_guide",
                    "crop": "wheat",
                    "category": "cultivation",
                    "language": "en",
                    "document_type": "agricultural_knowledge",
                },
            },
            {
                "content": "Rice blast disease appears as diamond-shaped lesions on leaves. Apply Tricyclazole 75% WP @ 0.6g/liter or Carbendazim 50% WP @ 1g/liter for control.",
                "metadata": {
                    "source": "plant_pathology_guide",
                    "crop": "rice",
                    "disease_name": "rice_blast",
                    "category": "disease_management",
                    "language": "en",
                    "document_type": "disease_information",
                },
            },
            {
                "content": "PM-KISAN scheme provides income support of Rs. 6000 per year to small and marginal farmers. Eligible farmers with landholding up to 2 hectares can apply online.",
                "metadata": {
                    "source": "government_portal",
                    "scheme_name": "PM-KISAN",
                    "scheme_type": "income_support",
                    "category": "government_scheme",
                    "language": "en",
                    "document_type": "government_scheme",
                },
            },
            {
                "content": "Current wheat prices in Delhi mandi: Rs. 2100-2200 per quintal. Demand is high due to festival season. Transport cost to nearby districts is Rs. 50-80 per quintal.",
                "metadata": {
                    "source": "market_intelligence_system",
                    "crop": "wheat",
                    "region": "delhi",
                    "category": "market_intelligence",
                    "language": "en",
                    "document_type": "market_intelligence",
                },
            },
            {
                "content": "Tomato early blight shows brown spots with concentric rings on older leaves. Remove affected leaves and spray Mancozeb 75% WP @ 2.5g/liter every 10-15 days.",
                "metadata": {
                    "source": "vegetable_production_guide",
                    "crop": "tomato",
                    "disease_name": "early_blight",
                    "category": "disease_management",
                    "language": "en",
                    "document_type": "disease_information",
                },
            },
        ]

        try:
            # Ingest into appropriate collections
            results = {}

            # Group documents by collection
            collections = {
                "agricultural_knowledge": [],
                "government_schemes": [],
                "market_intelligence": [],
                "crop_diseases": [],
            }

            for doc in sample_documents:
                doc_type = doc["metadata"].get(
                    "document_type", "agricultural_knowledge"
                )
                category = doc["metadata"].get("category", "general")

                if doc_type == "government_scheme" or category == "government_scheme":
                    collections["government_schemes"].append(doc)
                elif (
                    doc_type == "market_intelligence"
                    or category == "market_intelligence"
                ):
                    collections["market_intelligence"].append(doc)
                elif (
                    doc_type == "disease_information"
                    or category == "disease_management"
                ):
                    collections["crop_diseases"].append(doc)
                else:
                    collections["agricultural_knowledge"].append(doc)

            # Ingest each collection
            for collection_name, docs in collections.items():
                if docs:
                    collection_results = self.rag_engine.ingest_document_batch(
                        documents=docs, collection_name=collection_name
                    )
                    results[collection_name] = collection_results

            # Aggregate results
            total_processed = sum(
                r.get("processed_documents", 0) for r in results.values()
            )
            total_failed = sum(r.get("failed_documents", 0) for r in results.values())

            aggregate_results = {
                "total_documents": len(sample_documents),
                "processed_documents": total_processed,
                "failed_documents": total_failed,
                "success_rate": total_processed / len(sample_documents),
                "collections_updated": list(results.keys()),
                "collection_results": results,
                "ingested_at": datetime.now().isoformat(),
            }

            logger.info(
                f"Ingested {total_processed} sample documents across {len(results)} collections"
            )
            return aggregate_results

        except Exception as e:
            logger.error(f"Failed to ingest sample documents: {e}")
            raise

    def validate_knowledge_base(self) -> Dict[str, Any]:
        """Validate the current state of the knowledge base."""

        try:
            # Get knowledge base statistics
            kb_stats = self.rag_engine.get_knowledge_base_stats()

            # Perform validation checks
            validation_results = {
                "total_documents": kb_stats.get("total_documents", 0),
                "collections": kb_stats.get("collections", {}),
                "vector_db_health": kb_stats.get("vector_db_health", {}),
                "validation_checks": [],
            }

            # Check if knowledge base has minimum content
            min_docs_per_collection = 1
            for collection_name, stats in kb_stats.get("collections", {}).items():
                if isinstance(stats, dict):
                    doc_count = stats.get("count", 0)
                    if doc_count < min_docs_per_collection:
                        validation_results["validation_checks"].append(
                            {
                                "check": "minimum_documents",
                                "collection": collection_name,
                                "status": "warning",
                                "message": f"Collection has only {doc_count} documents",
                            }
                        )
                    else:
                        validation_results["validation_checks"].append(
                            {
                                "check": "minimum_documents",
                                "collection": collection_name,
                                "status": "pass",
                                "message": f"Collection has {doc_count} documents",
                            }
                        )

            # Check vector database health
            db_health = kb_stats.get("vector_db_health", {})
            if db_health.get("status") == "healthy":
                validation_results["validation_checks"].append(
                    {
                        "check": "vector_db_health",
                        "status": "pass",
                        "message": "Vector database is healthy",
                    }
                )
            else:
                validation_results["validation_checks"].append(
                    {
                        "check": "vector_db_health",
                        "status": "fail",
                        "message": f"Vector database issue: {db_health.get('error', 'Unknown error')}",
                    }
                )

            # Overall validation status
            failed_checks = [
                c
                for c in validation_results["validation_checks"]
                if c["status"] == "fail"
            ]
            warning_checks = [
                c
                for c in validation_results["validation_checks"]
                if c["status"] == "warning"
            ]

            if failed_checks:
                validation_results["overall_status"] = "fail"
            elif warning_checks:
                validation_results["overall_status"] = "warning"
            else:
                validation_results["overall_status"] = "pass"

            validation_results["validated_at"] = datetime.now().isoformat()

            return validation_results

        except Exception as e:
            logger.error(f"Failed to validate knowledge base: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "validated_at": datetime.now().isoformat(),
            }


# Global instance
document_ingestion_pipeline = DocumentIngestionPipeline()
