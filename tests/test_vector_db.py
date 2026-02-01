"""
Tests for ChromaDB vector database integration.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os

from app.services.vector_db import ChromaDBService


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_chroma_service(temp_chroma_dir):
    """Create a mock ChromaDB service for testing."""
    with patch("app.services.vector_db.settings") as mock_settings:
        mock_settings.environment = "development"
        mock_settings.openai_api_key = "test-key"

        with patch("chromadb.PersistentClient") as mock_client:
            service = ChromaDBService()
            service.client = Mock()
            service.embedding_function = Mock()
            yield service


def test_chromadb_service_initialization(mock_chroma_service):
    """Test ChromaDB service initialization."""
    assert mock_chroma_service.client is not None
    assert mock_chroma_service.embedding_function is not None
    assert isinstance(mock_chroma_service.collections, dict)


def test_get_or_create_collection(mock_chroma_service):
    """Test getting or creating a collection."""
    collection_name = "test_collection"
    mock_collection = Mock()
    mock_chroma_service.client.get_or_create_collection.return_value = mock_collection

    result = mock_chroma_service.get_or_create_collection(collection_name)

    assert result == mock_collection
    assert collection_name in mock_chroma_service.collections
    mock_chroma_service.client.get_or_create_collection.assert_called_once()


def test_add_documents(mock_chroma_service):
    """Test adding documents to a collection."""
    collection_name = "test_collection"
    documents = ["Document 1", "Document 2"]
    metadatas = [{"source": "test1"}, {"source": "test2"}]
    ids = ["id1", "id2"]

    mock_collection = Mock()
    mock_chroma_service.client.get_or_create_collection.return_value = mock_collection

    mock_chroma_service.add_documents(collection_name, documents, metadatas, ids)

    mock_collection.add.assert_called_once_with(
        documents=documents, metadatas=metadatas, ids=ids
    )


def test_query_documents(mock_chroma_service):
    """Test querying documents from a collection."""
    collection_name = "test_collection"
    query_text = "test query"

    mock_collection = Mock()
    mock_results = {
        "documents": [["Document 1", "Document 2"]],
        "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
        "distances": [[0.1, 0.2]],
    }
    mock_collection.query.return_value = mock_results
    mock_chroma_service.client.get_or_create_collection.return_value = mock_collection

    results = mock_chroma_service.query_documents(
        collection_name, query_text, n_results=2
    )

    assert results == mock_results
    mock_collection.query.assert_called_once_with(
        query_texts=[query_text], n_results=2, where=None
    )


def test_update_documents(mock_chroma_service):
    """Test updating documents in a collection."""
    collection_name = "test_collection"
    ids = ["id1", "id2"]
    documents = ["Updated Document 1", "Updated Document 2"]
    metadatas = [{"source": "updated1"}, {"source": "updated2"}]

    mock_collection = Mock()
    mock_chroma_service.client.get_or_create_collection.return_value = mock_collection

    mock_chroma_service.update_documents(collection_name, ids, documents, metadatas)

    mock_collection.update.assert_called_once_with(
        ids=ids, documents=documents, metadatas=metadatas
    )


def test_delete_documents(mock_chroma_service):
    """Test deleting documents from a collection."""
    collection_name = "test_collection"
    ids = ["id1", "id2"]

    mock_collection = Mock()
    mock_chroma_service.client.get_or_create_collection.return_value = mock_collection

    mock_chroma_service.delete_documents(collection_name, ids)

    mock_collection.delete.assert_called_once_with(ids=ids)


def test_get_collection_info(mock_chroma_service):
    """Test getting collection information."""
    collection_name = "test_collection"

    mock_collection = Mock()
    mock_collection.count.return_value = 10
    mock_collection.metadata = {"description": "Test collection"}
    mock_chroma_service.client.get_or_create_collection.return_value = mock_collection

    info = mock_chroma_service.get_collection_info(collection_name)

    assert info["name"] == collection_name
    assert info["count"] == 10
    assert info["metadata"]["description"] == "Test collection"


def test_reset_collection(mock_chroma_service):
    """Test resetting a collection."""
    collection_name = "test_collection"

    # Add collection to cache first
    mock_chroma_service.collections[collection_name] = Mock()

    mock_chroma_service.reset_collection(collection_name)

    # Collection should be removed from cache
    assert collection_name not in mock_chroma_service.collections

    # Should attempt to delete and recreate
    mock_chroma_service.client.delete_collection.assert_called_once_with(
        name=collection_name
    )
