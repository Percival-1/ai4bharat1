"""
RAG (Retrieval-Augmented Generation) API endpoints.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.services.rag_engine import rag_engine
from app.services.document_ingestion import document_ingestion_pipeline
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG Engine"])


# Request/Response Models
class DocumentRetrievalRequest(BaseModel):
    """Request model for document retrieval."""

    query: str = Field(..., description="Search query")
    collections: Optional[List[str]] = Field(None, description="Collections to search")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    similarity_threshold: Optional[float] = Field(
        0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata filters"
    )


class RAGQueryRequest(BaseModel):
    """Request model for RAG query."""

    query: str = Field(..., description="User query")
    collections: Optional[List[str]] = Field(None, description="Collections to search")
    top_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve")
    response_type: str = Field("comprehensive", description="Type of response")
    language: str = Field("en", description="Target language")
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Additional search filters"
    )


class DocumentIngestionRequest(BaseModel):
    """Request model for document ingestion."""

    documents: List[Dict[str, Any]] = Field(..., description="Documents to ingest")
    collection_name: str = Field(..., description="Target collection name")
    batch_size: int = Field(50, ge=1, le=100, description="Batch size for processing")


class FileIngestionRequest(BaseModel):
    """Request model for file ingestion."""

    file_path: str = Field(..., description="Path to file")
    collection_name: str = Field(..., description="Target collection name")
    file_format: Optional[str] = Field(None, description="File format (json, csv, txt)")
    metadata_overrides: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


# API Endpoints
@router.post("/retrieve", summary="Retrieve relevant documents")
async def retrieve_documents(request: DocumentRetrievalRequest):
    """Retrieve relevant documents using semantic search."""
    try:
        results = rag_engine.retrieve_documents(
            query=request.query,
            collections=request.collections,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            filters=request.filters,
        )

        return {
            "success": True,
            "query": request.query,
            "num_results": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Document retrieval failed: {str(e)}"
        )


@router.post("/query", summary="Complete RAG query with response generation")
async def rag_query(request: RAGQueryRequest):
    """Perform complete RAG pipeline: retrieve documents and generate response."""
    try:
        response_data = rag_engine.search_and_generate(
            query=request.query,
            collections=request.collections,
            top_k=request.top_k,
            response_type=request.response_type,
            language=request.language,
            filters=request.filters,
        )

        return {"success": True, "data": response_data}

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


@router.post("/ingest", summary="Ingest documents into knowledge base")
async def ingest_documents(request: DocumentIngestionRequest):
    """Ingest a batch of documents into the knowledge base."""
    try:
        results = rag_engine.ingest_document_batch(
            documents=request.documents,
            collection_name=request.collection_name,
            batch_size=request.batch_size,
        )

        return {"success": True, "results": results}

    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Document ingestion failed: {str(e)}"
        )


@router.post("/ingest/file", summary="Ingest documents from file")
async def ingest_from_file(request: FileIngestionRequest):
    """Ingest documents from a file."""
    try:
        results = document_ingestion_pipeline.ingest_from_file(
            file_path=request.file_path,
            collection_name=request.collection_name,
            file_format=request.file_format,
            metadata_overrides=request.metadata_overrides,
        )

        return {"success": True, "results": results}

    except Exception as e:
        logger.error(f"File ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")


@router.post("/ingest/samples", summary="Ingest sample agricultural knowledge")
async def ingest_sample_documents():
    """Ingest sample agricultural knowledge documents for testing."""
    try:
        results = document_ingestion_pipeline.ingest_agricultural_knowledge_samples()

        return {
            "success": True,
            "message": "Sample documents ingested successfully",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Sample ingestion failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sample ingestion failed: {str(e)}"
        )


@router.get("/stats", summary="Get knowledge base statistics")
async def get_knowledge_base_stats():
    """Get comprehensive statistics about the knowledge base."""
    try:
        stats = rag_engine.get_knowledge_base_stats()

        return {"success": True, "stats": stats}

    except Exception as e:
        logger.error(f"Failed to get knowledge base stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/validate", summary="Validate knowledge base")
async def validate_knowledge_base():
    """Validate the current state of the knowledge base."""
    try:
        validation_results = document_ingestion_pipeline.validate_knowledge_base()

        return {"success": True, "validation": validation_results}

    except Exception as e:
        logger.error(f"Knowledge base validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/collections", summary="List available collections")
async def list_collections():
    """List all available collections in the vector database."""
    try:
        collections = rag_engine.vector_db.list_all_collections()

        return {"success": True, "collections": collections}

    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/search/agricultural", summary="Search agricultural knowledge")
async def search_agricultural_knowledge(
    query: str = Query(..., description="Search query"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    category: Optional[str] = Query(None, description="Filter by category"),
    n_results: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """Search agricultural knowledge documents."""
    try:
        results = rag_engine.embedding_service.search_agricultural_knowledge(
            query=query, crop=crop, category=category, n_results=n_results
        )

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Agricultural knowledge search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/schemes", summary="Search government schemes")
async def search_government_schemes(
    query: str = Query(..., description="Search query"),
    scheme_type: Optional[str] = Query(None, description="Filter by scheme type"),
    n_results: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """Search government scheme documents."""
    try:
        results = rag_engine.embedding_service.search_government_schemes(
            query=query, scheme_type=scheme_type, n_results=n_results
        )

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Government schemes search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/market", summary="Search market intelligence")
async def search_market_intelligence(
    query: str = Query(..., description="Search query"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    region: Optional[str] = Query(None, description="Filter by region"),
    n_results: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """Search market intelligence documents."""
    try:
        results = rag_engine.embedding_service.search_market_intelligence(
            query=query, crop=crop, region=region, n_results=n_results
        )

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Market intelligence search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/diseases", summary="Search crop disease information")
async def search_disease_information(
    query: str = Query(..., description="Search query"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    disease_name: Optional[str] = Query(None, description="Filter by disease name"),
    n_results: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """Search crop disease information."""
    try:
        results = rag_engine.embedding_service.search_disease_information(
            query=query, crop=crop, disease_name=disease_name, n_results=n_results
        )

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Disease information search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search/hybrid", summary="Hybrid search across collections")
async def hybrid_search(
    query: str = Body(..., description="Search query"),
    collections: Optional[List[str]] = Body(None, description="Collections to search"),
    n_results_per_collection: int = Body(
        3, ge=1, le=10, description="Results per collection"
    ),
):
    """Perform hybrid search across multiple collections."""
    try:
        results = rag_engine.embedding_service.hybrid_search(
            query=query,
            collections=collections,
            n_results_per_collection=n_results_per_collection,
        )

        return {"success": True, "query": query, "results": results}

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")
