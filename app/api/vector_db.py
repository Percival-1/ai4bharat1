"""
Vector database API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional

from app.services.vector_db_factory import get_vector_db
from app.services.embedding_service import embedding_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/vector-db", tags=["vector-db"])


@router.get("/health")
async def vector_db_health() -> Dict[str, Any]:
    """Check vector database health."""
    try:
        vector_db = get_vector_db()
        health_status = vector_db.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Vector database health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections")
async def list_collections() -> Dict[str, Any]:
    """List all vector database collections."""
    try:
        stats = embedding_service.get_collection_stats()
        return {"collections": stats}
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/info")
async def get_collection_info(collection_name: str) -> Dict[str, Any]:
    """Get information about a specific collection."""
    try:
        vector_db = get_vector_db()
        info = vector_db.get_collection_info(collection_name)
        return info
    except Exception as e:
        logger.error(f"Failed to get collection info for {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/search")
async def search_collection(
    collection_name: str,
    query: str,
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Search documents in a specific collection."""
    try:
        vector_db = get_vector_db()
        results = vector_db.query_documents(
            collection_name=collection_name,
            query_text=query,
            n_results=n_results,
            where=where,
        )

        # Format results for API response
        formatted_results = embedding_service._format_search_results(results)

        return {
            "query": query,
            "collection": collection_name,
            "results": formatted_results,
            "total_results": len(formatted_results),
        }
    except Exception as e:
        logger.error(f"Search failed for collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def hybrid_search(
    query: str,
    collections: Optional[List[str]] = None,
    n_results_per_collection: int = 3,
) -> Dict[str, Any]:
    """Perform hybrid search across multiple collections."""
    try:
        results = embedding_service.hybrid_search(
            query=query,
            collections=collections,
            n_results_per_collection=n_results_per_collection,
        )

        return {
            "query": query,
            "collections_searched": list(results.keys()),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/reset")
async def reset_collection(collection_name: str) -> Dict[str, str]:
    """Reset a collection (delete all documents)."""
    try:
        vector_db = get_vector_db()
        vector_db.reset_collection(collection_name)
        return {"message": f"Collection '{collection_name}' reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
