"""
RAG (Retrieval-Augmented Generation) Engine for the agri-civic intelligence platform.
Provides document retrieval, response generation with source grounding, and hallucination prevention.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import json
import re
from datetime import datetime

from app.services.embedding_service import DocumentEmbeddingService
from app.services.llm_service import llm_service, LLMRequest
from app.services.vector_db_factory import get_vector_db
from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class RAGEngine:
    """RAG Engine for retrieval-augmented generation with source grounding."""

    def __init__(self):
        """Initialize the RAG engine."""
        self.embedding_service = DocumentEmbeddingService()
        self.vector_db = get_vector_db()
        self.min_similarity_threshold = 0.3  # Lower threshold for better recall
        self.max_context_length = 4000  # Maximum context length for LLM

    def retrieve_documents(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using semantic search.

        Args:
            query: The search query
            collections: List of collections to search (default: all)
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score (default: 0.7)
            filters: Additional metadata filters

        Returns:
            List of relevant documents with metadata and similarity scores
        """
        if similarity_threshold is None:
            similarity_threshold = self.min_similarity_threshold

        if collections is None:
            collections = [
                "agricultural_knowledge",
                "government_schemes",
                "market_intelligence",
                "crop_diseases",
            ]

        try:
            # Perform hybrid search across collections
            all_results = []

            for collection in collections:
                try:
                    results = self.vector_db.query_documents(
                        collection_name=collection,
                        query_text=query,
                        n_results=top_k,
                        where=filters,
                    )

                    # Format and filter results
                    formatted_results = self.embedding_service._format_search_results(
                        results
                    )

                    # Filter by similarity threshold
                    filtered_results = [
                        result
                        for result in formatted_results
                        if result.get("similarity_score", 0) >= similarity_threshold
                    ]

                    # Add collection info to metadata
                    for result in filtered_results:
                        result["metadata"]["collection"] = collection
                        result["metadata"]["retrieval_query"] = query
                        result["metadata"]["retrieved_at"] = datetime.now().isoformat()

                    all_results.extend(filtered_results)

                except Exception as e:
                    logger.warning(f"Failed to search collection {collection}: {e}")
                    continue

            # Sort by similarity score and return top results
            all_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

            logger.info(
                f"Retrieved {len(all_results)} relevant documents for query: {query[:50]}..."
            )
            return all_results[:top_k]

        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            raise

    async def generate_grounded_response(
        self,
        query: str,
        retrieved_documents: List[Dict[str, Any]],
        response_type: str = "comprehensive",
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Generate a response grounded in retrieved documents.

        Args:
            query: The user query
            retrieved_documents: Documents retrieved from vector search
            response_type: Type of response (comprehensive, concise, technical)
            language: Target language for response

        Returns:
            Dictionary containing response, sources, and grounding information
        """
        try:
            if not retrieved_documents:
                return self._generate_fallback_response(query, language)

            # Prepare context from retrieved documents
            context = self._prepare_context(retrieved_documents)

            # Generate response with source grounding
            response_data = await self._generate_response_with_grounding(
                query=query,
                context=context,
                retrieved_documents=retrieved_documents,
                response_type=response_type,
                language=language,
            )

            # Validate source grounding
            grounding_validation = self._validate_source_grounding(
                response_data["response"], retrieved_documents
            )

            response_data.update(grounding_validation)

            logger.info(f"Generated grounded response for query: {query[:50]}...")
            return response_data

        except Exception as e:
            logger.error(f"Failed to generate grounded response: {e}")
            return self._generate_fallback_response(query, language)

    def _prepare_context(self, documents: List[Dict[str, Any]]) -> str:
        """Prepare context string from retrieved documents."""
        context_parts = []
        current_length = 0

        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # Create source reference
            source_ref = f"[Source {i+1}]"
            source_info = f"Source: {metadata.get('source', 'Unknown')}"
            if metadata.get("crop"):
                source_info += f", Crop: {metadata['crop']}"
            if metadata.get("category"):
                source_info += f", Category: {metadata['category']}"

            doc_context = f"{source_ref} {source_info}\n{content}\n\n"

            # Check if adding this document would exceed context length
            if current_length + len(doc_context) > self.max_context_length:
                break

            context_parts.append(doc_context)
            current_length += len(doc_context)

        return "".join(context_parts)

    async def _generate_response_with_grounding(
        self,
        query: str,
        context: str,
        retrieved_documents: List[Dict[str, Any]],
        response_type: str,
        language: str,
    ) -> Dict[str, Any]:
        """Generate response with proper source grounding using LLM."""

        try:
            # Create system message for agricultural context
            system_message = self._create_system_message(response_type, language)

            # Create user prompt with context and query
            user_prompt = self._create_user_prompt(
                query, context, response_type, language
            )

            # Call LLM service to generate response
            llm_response = await llm_service.generate_response(
                prompt=user_prompt,
                system_message=system_message,
                max_tokens=self._get_max_tokens_for_response_type(response_type),
                temperature=0.3,  # Lower temperature for more factual responses
                metadata={
                    "query": query,
                    "response_type": response_type,
                    "language": language,
                    "num_sources": len(retrieved_documents),
                },
            )

            # Collect sources information
            sources = []
            for i, doc in enumerate(retrieved_documents):
                metadata = doc.get("metadata", {})
                source_info = {
                    "id": doc.get("id", f"doc_{i}"),
                    "source": metadata.get("source", "Unknown"),
                    "category": metadata.get("category", "General"),
                    "similarity_score": doc.get("similarity_score", 0),
                    "collection": metadata.get("collection", "Unknown"),
                }
                sources.append(source_info)

            return {
                "response": llm_response.content,
                "sources": sources,
                "context_used": context,
                "query": query,
                "response_type": response_type,
                "language": language,
                "generated_at": datetime.now().isoformat(),
                "num_sources": len(sources),
                "llm_metadata": {
                    "provider": llm_response.provider,
                    "model": llm_response.model,
                    "tokens_used": llm_response.tokens_used,
                    "response_time": llm_response.response_time,
                },
            }

        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            # Fallback to simple response generation
            return self._generate_simple_response_fallback(
                query, retrieved_documents, response_type, language
            )

    def _create_system_message(self, response_type: str, language: str) -> str:
        """Create system message for the LLM based on response type and language."""

        base_instructions = {
            "en": """You are an expert agricultural advisor for Indian farmers. Your role is to provide accurate, practical, and actionable agricultural advice based on the provided context documents.

IMPORTANT GUIDELINES:
1. ONLY use information from the provided context documents
2. ALWAYS cite sources using [Source X] format when making claims
3. If the context doesn't contain enough information, clearly state this limitation
4. Provide specific, actionable advice with dosages, timing, and costs when available
5. Focus on practical solutions that farmers can implement
6. Include prevention strategies when discussing disease/pest management
7. Mention local availability and approximate costs when provided in context""",
        }

        response_type_additions = {
            "comprehensive": "Provide detailed, comprehensive responses with all relevant information.",
            "concise": "Provide concise, to-the-point responses focusing on key actionable items.",
            "technical": "Provide technical responses with scientific details and precise measurements.",
        }

        system_msg = base_instructions.get(language, base_instructions["en"])

        if response_type in response_type_additions:
            system_msg += (
                f"\n\nResponse Style: {response_type_additions[response_type]}"
            )

        return system_msg

    def _create_user_prompt(
        self, query: str, context: str, response_type: str, language: str
    ) -> str:
        """Create user prompt with context and query."""

        prompt_templates = {
            "en": """Based on the following agricultural knowledge context, please answer the farmer's question.

CONTEXT DOCUMENTS:
{context}

FARMER'S QUESTION: {query}

Please provide a helpful response based ONLY on the information in the context documents above. Always cite your sources using [Source X] format.""",
        }

        template = prompt_templates.get(language, prompt_templates["en"])
        return template.format(context=context, query=query)

    def _get_max_tokens_for_response_type(self, response_type: str) -> int:
        """Get appropriate max tokens based on response type."""
        token_limits = {"concise": 300, "comprehensive": 800, "technical": 600}
        return token_limits.get(response_type, 500)

    def _generate_simple_response_fallback(
        self,
        query: str,
        retrieved_documents: List[Dict[str, Any]],
        response_type: str,
        language: str,
    ) -> Dict[str, Any]:
        """Fallback response generation when LLM fails."""

        # This is the old logic as fallback
        response_parts = []
        sources = []

        # Analyze query intent
        query_lower = query.lower()

        if any(
            word in query_lower for word in ["disease", "pest", "problem", "symptom"]
        ):
            response_parts.append(self._generate_disease_response(retrieved_documents))
        elif any(word in query_lower for word in ["price", "market", "sell", "mandi"]):
            response_parts.append(self._generate_market_response(retrieved_documents))
        elif any(
            word in query_lower
            for word in ["scheme", "subsidy", "government", "benefit"]
        ):
            response_parts.append(self._generate_scheme_response(retrieved_documents))
        else:
            response_parts.append(self._generate_general_response(retrieved_documents))

        # Collect sources
        for i, doc in enumerate(retrieved_documents):
            metadata = doc.get("metadata", {})
            source_info = {
                "id": doc.get("id", f"doc_{i}"),
                "source": metadata.get("source", "Unknown"),
                "category": metadata.get("category", "General"),
                "similarity_score": doc.get("similarity_score", 0),
                "collection": metadata.get("collection", "Unknown"),
            }
            sources.append(source_info)

        response_text = " ".join(response_parts)

        return {
            "response": response_text,
            "sources": sources,
            "context_used": "",
            "query": query,
            "response_type": response_type,
            "language": language,
            "generated_at": datetime.now().isoformat(),
            "num_sources": len(sources),
            "fallback_used": True,
        }

    def _generate_disease_response(self, documents: List[Dict[str, Any]]) -> str:
        """Generate disease-related response from documents."""
        response_parts = []

        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            if metadata.get("category") == "disease_management":
                response_parts.append(
                    f"According to {metadata.get('source', 'agricultural sources')} [Source {i+1}], {content[:200]}..."
                )
            elif "disease" in content.lower() or "pest" in content.lower():
                response_parts.append(
                    f"Based on {metadata.get('source', 'available information')} [Source {i+1}], {content[:200]}..."
                )

        if not response_parts:
            response_parts.append(
                "Based on the available agricultural knowledge, here's what I found relevant to your query."
            )

        return " ".join(response_parts)

    def _generate_market_response(self, documents: List[Dict[str, Any]]) -> str:
        """Generate market-related response from documents."""
        response_parts = []

        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            if metadata.get("category") == "market_intelligence":
                response_parts.append(
                    f"According to market data from {metadata.get('source', 'market sources')} [Source {i+1}], {content[:200]}..."
                )
            elif any(word in content.lower() for word in ["price", "market", "mandi"]):
                response_parts.append(
                    f"Based on {metadata.get('source', 'available information')} [Source {i+1}], {content[:200]}..."
                )

        if not response_parts:
            response_parts.append(
                "Based on the available market intelligence, here's what I found relevant to your query."
            )

        return " ".join(response_parts)

    def _generate_scheme_response(self, documents: List[Dict[str, Any]]) -> str:
        """Generate government scheme response from documents."""
        response_parts = []

        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            if metadata.get("category") == "government_scheme":
                scheme_name = metadata.get("scheme_name", "government scheme")
                response_parts.append(
                    f"According to official information about {scheme_name} [Source {i+1}], {content[:200]}..."
                )
            elif any(
                word in content.lower() for word in ["scheme", "subsidy", "government"]
            ):
                response_parts.append(
                    f"Based on {metadata.get('source', 'government sources')} [Source {i+1}], {content[:200]}..."
                )

        if not response_parts:
            response_parts.append(
                "Based on the available government scheme information, here's what I found relevant to your query."
            )

        return " ".join(response_parts)

    def _generate_general_response(self, documents: List[Dict[str, Any]]) -> str:
        """Generate general agricultural response from documents."""
        response_parts = []

        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            source_name = metadata.get("source", "agricultural sources")
            response_parts.append(
                f"According to {source_name} [Source {i+1}], {content[:200]}..."
            )

        if not response_parts:
            response_parts.append(
                "Based on the available agricultural knowledge, here's what I found relevant to your query."
            )

        return " ".join(response_parts)

    def _validate_source_grounding(
        self, response: str, retrieved_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate that response is properly grounded in sources."""

        # Check for source references in response
        source_pattern = r"\[Source \d+\]"
        source_references = re.findall(source_pattern, response)

        # Calculate grounding metrics
        total_sources = len(retrieved_documents)
        referenced_sources = len(set(source_references))

        grounding_score = referenced_sources / max(total_sources, 1)

        # Check for potential hallucination indicators
        hallucination_indicators = self._detect_hallucination_indicators(
            response, retrieved_documents
        )

        return {
            "grounding_score": grounding_score,
            "total_sources": total_sources,
            "referenced_sources": referenced_sources,
            "source_references": source_references,
            "hallucination_risk": len(hallucination_indicators) > 0,
            "hallucination_indicators": hallucination_indicators,
            "is_well_grounded": grounding_score > 0.5
            and len(hallucination_indicators) == 0,
        }

    def _detect_hallucination_indicators(
        self, response: str, retrieved_documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect potential hallucination indicators in the response."""

        indicators = []

        # Check for specific claims not supported by documents
        response_lower = response.lower()

        # Collect all content from documents
        document_content = " ".join(
            [doc.get("content", "").lower() for doc in retrieved_documents]
        )

        # Check for specific numeric claims
        numeric_claims = re.findall(
            r"\d+(?:\.\d+)?(?:\s*(?:percent|%|rupees|rs|kg|quintal|acre|hectare))",
            response_lower,
        )
        for claim in numeric_claims:
            if claim not in document_content:
                indicators.append(f"Unsupported numeric claim: {claim}")

        # Check for specific product/chemical names (more specific pattern)
        chemical_pattern = r"\b[A-Z][a-z]*(?:azole|mycin|bendazim|conazole|thiram|captan|mancozeb)\b|\b[A-Z][a-z]*\s+\d+(?:\.\d+)?%?\s*(?:EC|WP|SL|G)\b"
        chemical_mentions = re.findall(chemical_pattern, response)
        for chemical in chemical_mentions:
            if chemical.lower() not in document_content:
                indicators.append(f"Unsupported chemical/product mention: {chemical}")

        return indicators

    def _generate_fallback_response(self, query: str, language: str) -> Dict[str, Any]:
        """Generate fallback response when no relevant documents are found."""

        fallback_responses = {
            "en": "I don't have specific information about your query in my knowledge base. Please consult with local agricultural experts or extension officers for accurate guidance.",
            "hi": "मेरे पास आपके प्रश्न के बारे में विशिष्ट जानकारी नहीं है। कृपया सटीक मार्गदर्शन के लिए स्थानीय कृषि विशेषज्ञों या विस्तार अधिकारियों से सलाह लें।",
        }

        response_text = fallback_responses.get(language, fallback_responses["en"])

        return {
            "response": response_text,
            "sources": [],
            "context_used": "",
            "query": query,
            "response_type": "fallback",
            "language": language,
            "generated_at": datetime.now().isoformat(),
            "num_sources": 0,
            "grounding_score": 0.0,
            "is_well_grounded": False,
            "hallucination_risk": False,
        }

    def ingest_document_batch(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Ingest a batch of documents into the knowledge base.

        Args:
            documents: List of documents with content and metadata
            collection_name: Target collection name
            batch_size: Number of documents to process in each batch

        Returns:
            Ingestion results and statistics
        """
        try:
            total_docs = len(documents)
            processed_docs = 0
            failed_docs = 0
            ingested_ids = []

            # Process documents in batches
            for i in range(0, total_docs, batch_size):
                batch = documents[i : i + batch_size]

                try:
                    # Validate and prepare documents
                    validated_batch = []
                    for doc in batch:
                        if self._validate_document(doc):
                            validated_batch.append(doc)
                        else:
                            failed_docs += 1

                    if validated_batch:
                        # Use embedding service for bulk ingestion
                        batch_ids = self.embedding_service.bulk_add_documents(
                            collection_name, validated_batch
                        )
                        ingested_ids.extend(batch_ids)
                        processed_docs += len(validated_batch)

                except Exception as e:
                    logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
                    failed_docs += len(batch)

            ingestion_stats = {
                "total_documents": total_docs,
                "processed_documents": processed_docs,
                "failed_documents": failed_docs,
                "success_rate": processed_docs / max(total_docs, 1),
                "ingested_ids": ingested_ids,
                "collection_name": collection_name,
                "ingested_at": datetime.now().isoformat(),
            }

            logger.info(
                f"Ingested {processed_docs}/{total_docs} documents into {collection_name}"
            )
            return ingestion_stats

        except Exception as e:
            logger.error(f"Failed to ingest document batch: {e}")
            raise

    def _validate_document(self, document: Dict[str, Any]) -> bool:
        """Validate document structure and content."""

        # Check required fields
        if not document.get("content"):
            logger.warning("Document missing content field")
            return False

        if not isinstance(document.get("metadata"), dict):
            logger.warning("Document missing or invalid metadata")
            return False

        # Check content length
        content = document["content"]
        if len(content.strip()) < 10:
            logger.warning("Document content too short")
            return False

        if len(content) > 10000:  # Reasonable limit for document size
            logger.warning("Document content too long")
            return False

        # Check for required metadata fields
        metadata = document["metadata"]
        if not metadata.get("source"):
            logger.warning("Document missing source in metadata")
            return False

        return True

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the knowledge base."""

        try:
            collection_stats = self.embedding_service.get_collection_stats()

            total_documents = sum(
                stats.get("count", 0)
                for stats in collection_stats.values()
                if isinstance(stats, dict) and "count" in stats
            )

            # Get vector database health
            db_health = self.vector_db.health_check()

            return {
                "total_documents": total_documents,
                "collections": collection_stats,
                "vector_db_health": db_health,
                "embedding_dimension": (
                    self.vector_db.get_embedding_dimension()
                    if hasattr(self.vector_db, "get_embedding_dimension")
                    else "unknown"
                ),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            return {"error": str(e), "last_updated": datetime.now().isoformat()}

    async def search_and_generate(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        top_k: int = 5,
        response_type: str = "comprehensive",
        language: str = "en",
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: search documents and generate grounded response.

        Args:
            query: User query
            collections: Collections to search
            top_k: Number of documents to retrieve
            response_type: Type of response to generate
            language: Target language
            filters: Additional search filters

        Returns:
            Complete response with sources and grounding information
        """
        try:
            # Step 1: Retrieve relevant documents
            retrieved_docs = self.retrieve_documents(
                query=query, collections=collections, top_k=top_k, filters=filters
            )

            # Step 2: Generate grounded response using LLM
            response_data = await self.generate_grounded_response(
                query=query,
                retrieved_documents=retrieved_docs,
                response_type=response_type,
                language=language,
            )

            return response_data

        except Exception as e:
            logger.error(f"Failed in search_and_generate pipeline: {e}")
            return self._generate_fallback_response(query, language)


# Global instance
rag_engine = RAGEngine()
