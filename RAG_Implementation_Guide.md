# RAG Implementation Guide

This guide explains how to read and understand the RAG (Retrieval-Augmented Generation) implementation in the agri-civic intelligence platform.

## 📁 File Structure Overview

```
app/
├── services/
│   ├── rag_engine.py          # Main RAG orchestration
│   ├── embedding_service.py   # Document embedding & search
│   ├── llm_service.py         # LLM integration
│   ├── vector_db.py           # ChromaDB operations
│   └── vector_db_factory.py   # Vector DB abstraction
├── api/
│   └── rag.py                 # REST API endpoints
└── config.py                  # Configuration settings
```

## 🔄 RAG Flow Architecture

```
User Query → RAG API → RAG Engine → [Retrieval] → [Generation] → Response
                          ↓              ↓            ↓
                    Embedding Service → Vector DB → LLM Service
```

## 📖 Reading Order for Understanding

### 1. Start with Configuration (`app/config.py`)
**Purpose**: Understand system settings and environment variables

**Key sections to read**:
```python
# Vector database settings
VECTOR_DB_TYPE = "chromadb"
CHROMA_PERSIST_DIRECTORY = "./data/chroma_db"

# LLM configuration
PRIMARY_LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-3.5-turbo"
LLM_MAX_TOKENS = 1000
```

### 2. Vector Database Layer (`app/services/vector_db_factory.py` → `app/services/vector_db.py`)

**Start with**: `vector_db_factory.py`
- Defines the `VectorDBInterface` abstract class
- Shows what operations any vector DB must support
- Factory pattern for creating different vector DB implementations

**Then read**: `vector_db.py` (ChromaDB implementation)
- `ChromaDBService` class implements the interface
- Key methods to understand:
  - `add_documents()` - Store documents with embeddings
  - `query_documents()` - Search for similar documents
  - `get_or_create_collection()` - Manage document collections

**Key concepts**:
```python
# Document storage
def add_documents(self, collection_name, documents, metadatas, ids):
    # Stores documents with their embeddings in ChromaDB

# Document retrieval  
def query_documents(self, collection_name, query_text, n_results=5):
    # Finds similar documents using vector similarity search
```

### 3. Embedding Service (`app/services/embedding_service.py`)

**Purpose**: High-level document management and search operations

**Key classes and methods**:
```python
class DocumentEmbeddingService:
    def add_agricultural_knowledge()    # Add farming documents
    def add_government_scheme()         # Add scheme documents  
    def add_disease_information()       # Add disease documents
    def search_agricultural_knowledge() # Search farming docs
    def _format_search_results()        # Format ChromaDB results
```

**Reading flow**:
1. Document addition methods (how documents are stored)
2. Search methods (how documents are retrieved)
3. `_format_search_results()` (how raw results are processed)

### 4. LLM Service (`app/services/llm_service.py`)

**Purpose**: Unified interface for multiple LLM providers (OpenAI, Anthropic)

**Key components**:
```python
class LLMService:
    def generate_response()      # Main method to get LLM responses
    def _generate_with_retry()   # Retry logic with exponential backoff
    def health_check()           # Check LLM provider status
    def get_metrics()            # Performance monitoring
```

**Key concepts**:
- Circuit breaker pattern for resilience
- Automatic failover between providers
- Request/response monitoring

### 5. RAG Engine (`app/services/rag_engine.py`) - **MAIN FILE**

**Purpose**: Orchestrates the complete RAG pipeline

**Reading approach**:

#### A. Start with the main public methods:
```python
async def search_and_generate():
    # Complete RAG pipeline - this is the main entry point
    
def retrieve_documents():
    # Step 1: Find relevant documents
    
async def generate_grounded_response():
    # Step 2: Generate LLM response from documents
```

#### B. Follow the retrieval flow:
```python
def retrieve_documents():
    # 1. Search across multiple collections
    # 2. Format and filter results  
    # 3. Add metadata (collection, query, timestamp)
    # 4. Sort by similarity score
```

#### C. Follow the generation flow:
```python
async def generate_grounded_response():
    # 1. Prepare context from documents
    # 2. Generate response with LLM
    # 3. Validate source grounding
    # 4. Return structured response
```

#### D. Understand the LLM integration:
```python
async def _generate_response_with_grounding():
    # 1. Create system message (role definition)
    # 2. Create user prompt (context + query)
    # 3. Call LLM service
    # 4. Process response and collect sources
```

#### E. Study the helper methods:
```python
def _prepare_context()              # Format documents for LLM
def _create_system_message()        # LLM role and instructions
def _create_user_prompt()           # Context + query formatting
def _validate_source_grounding()    # Check response citations
def _detect_hallucination_indicators() # Identify unsupported claims
```

### 6. RAG API (`app/api/rag.py`)

**Purpose**: REST API endpoints for RAG functionality

**Key endpoints to understand**:
```python
@router.post("/query")              # Main RAG query endpoint
@router.post("/retrieve")           # Document retrieval only
@router.post("/ingest")             # Add new documents
@router.get("/stats")               # Knowledge base statistics
```

## 🔍 Understanding the Complete Flow

### Example: User asks "My wheat has orange spots, what should I do?"

1. **API Layer** (`rag.py`):
   ```python
   async def rag_query(request: RAGQueryRequest):
       response_data = await rag_engine.search_and_generate(...)
   ```

2. **RAG Engine** (`rag_engine.py`):
   ```python
   async def search_and_generate():
       # Step 1: Retrieve documents
       retrieved_docs = self.retrieve_documents(
           query="wheat orange spots",
           collections=["crop_diseases"]
       )
       
       # Step 2: Generate response
       response_data = await self.generate_grounded_response(
           query, retrieved_docs
       )
   ```

3. **Document Retrieval**:
   ```python
   def retrieve_documents():
       # For each collection:
       results = self.vector_db.query_documents(
           collection_name="crop_diseases",
           query_text="wheat orange spots"
       )
       # Format and filter results
       formatted_results = self.embedding_service._format_search_results(results)
   ```

4. **Response Generation**:
   ```python
   async def generate_grounded_response():
       # Prepare context from retrieved documents
       context = self._prepare_context(retrieved_documents)
       
       # Generate LLM response
       llm_response = await llm_service.generate_response(
           prompt=user_prompt,
           system_message=system_message
       )
   ```

5. **LLM Service**:
   ```python
   async def generate_response():
       # Try primary provider (OpenAI)
       response = await openai_client.generate_response(request)
       # Return structured response with metadata
   ```

## 🧩 Key Design Patterns

### 1. **Factory Pattern** (`vector_db_factory.py`)
- Abstracts vector database creation
- Allows switching between ChromaDB, Pinecone, Weaviate

### 2. **Strategy Pattern** (`llm_service.py`)
- Multiple LLM providers with same interface
- Automatic failover between providers

### 3. **Template Method** (`rag_engine.py`)
- `search_and_generate()` defines the algorithm
- Subcomponents handle specific steps

### 4. **Circuit Breaker** (`llm_service.py`)
- Prevents cascading failures
- Automatic recovery after failures

## 📚 Understanding Data Flow

### Document Storage:
```
Raw Document → Embedding Service → Vector DB → ChromaDB Collections
     ↓              ↓                ↓              ↓
  Content +     Generate         Store with      Persistent
  Metadata      Embeddings       Vectors         Storage
```

### Document Retrieval:
```
User Query → Embedding → Vector Search → Similarity Matching → Ranked Results
     ↓           ↓            ↓              ↓                    ↓
  "wheat rust"  Vector    ChromaDB Query   Cosine Similarity   Top-K Docs
```

### Response Generation:
```
Query + Documents → Context Preparation → LLM Prompt → LLM Response → Validation
       ↓                    ↓                ↓            ↓            ↓
   Retrieved Docs      Format Context    System +     Generated    Source Check
                                        User Prompt    Text
```

## 🔧 Debugging and Testing

### 1. **Test Scripts**:
- `test_rag_with_llm.py` - End-to-end RAG testing
- `demo_rag_llm_integration.py` - Comprehensive demonstration
- `tests/test_rag_engine.py` - Unit tests

### 2. **Logging Points**:
```python
# In rag_engine.py
logger.info(f"Retrieved {len(all_results)} relevant documents")
logger.info(f"Generated grounded response for query: {query[:50]}...")

# In llm_service.py  
logger.info(f"LLM request successful with {provider_name}")
```

### 3. **Monitoring**:
```python
# Check RAG statistics
stats = rag_engine.get_knowledge_base_stats()

# Check LLM metrics
metrics = llm_service.get_metrics()
```

## 🎯 Key Methods to Focus On

### For Understanding RAG Flow:
1. `RAGEngine.search_and_generate()` - Main orchestration
2. `RAGEngine.retrieve_documents()` - Document retrieval
3. `RAGEngine.generate_grounded_response()` - Response generation

### For Understanding Document Management:
1. `DocumentEmbeddingService.add_*()` methods - Document ingestion
2. `DocumentEmbeddingService.search_*()` methods - Document search
3. `ChromaDBService.query_documents()` - Vector search

### For Understanding LLM Integration:
1. `LLMService.generate_response()` - Main LLM interface
2. `RAGEngine._create_system_message()` - LLM prompting
3. `RAGEngine._validate_source_grounding()` - Response validation

## 💡 Tips for Reading the Code

1. **Start with interfaces** - Understand what each component should do
2. **Follow the data** - Trace how documents and queries flow through the system
3. **Read tests** - They show expected behavior and usage patterns
4. **Use the demo scripts** - See the system in action
5. **Check error handling** - Understand failure modes and recovery

This guide provides a structured approach to understanding the RAG implementation. Start with the overview, then dive deep into each component following the suggested reading order.