# Step-by-Step Guide to Reading RAG Code

This guide provides a practical approach to understanding the RAG implementation by following specific reading steps.

## 🎯 Phase 1: Understanding the Foundation (30 minutes)

### Step 1: Read Configuration (`app/config.py`)
**Time**: 5 minutes  
**Focus**: Environment variables and settings

```python
# Look for these key sections:
class Settings(BaseSettings):
    # Vector database configuration
    vector_db_type: str = "chromadb"
    chroma_persist_directory: str = "./data/chroma_db"
    
    # LLM configuration  
    primary_llm_provider: str = "openai"
    llm_model: str = "gpt-3.5-turbo"
    llm_max_tokens: int = 1000
    
    # API keys
    openai_api_key: Optional[str] = None
```

**Questions to answer**:
- What vector database is being used?
- Which LLM providers are supported?
- What are the default settings?

### Step 2: Understand Vector Database Interface (`app/services/vector_db_factory.py`)
**Time**: 10 minutes  
**Focus**: Abstract interface and factory pattern

```python
# Read this abstract class first:
class VectorDBInterface(ABC):
    @abstractmethod
    def add_documents(self, collection_name, documents, metadatas, ids):
        pass
    
    @abstractmethod  
    def query_documents(self, collection_name, query_text, n_results=5):
        pass
```

**Questions to answer**:
- What operations must any vector database support?
- How does the factory pattern work here?
- What databases are supported?

### Step 3: Read ChromaDB Implementation (`app/services/vector_db.py`)
**Time**: 15 minutes  
**Focus**: Concrete implementation of vector operations

**Start with these methods**:
```python
def add_documents(self, collection_name, documents, metadatas, ids):
    # How documents are stored with embeddings

def query_documents(self, collection_name, query_text, n_results=5):
    # How similar documents are found
    
def get_or_create_collection(self, collection_name):
    # How collections are managed
```

**Questions to answer**:
- How are embeddings generated and stored?
- How does similarity search work?
- How are collections organized?

## 🎯 Phase 2: Document Management Layer (45 minutes)

### Step 4: Read Embedding Service (`app/services/embedding_service.py`)
**Time**: 25 minutes  
**Focus**: High-level document operations

**Read in this order**:

1. **Document Addition Methods** (10 minutes):
```python
def add_agricultural_knowledge(self, content, crop=None, category="general"):
    # How farming documents are added
    
def add_disease_information(self, content, crop, disease_name):
    # How disease documents are added
    
def add_government_scheme(self, content, scheme_name, scheme_type):
    # How scheme documents are added
```

2. **Search Methods** (10 minutes):
```python
def search_agricultural_knowledge(self, query, crop=None, category=None):
    # How to search farming documents
    
def search_disease_information(self, query, crop=None, disease_name=None):
    # How to search disease documents
```

3. **Result Formatting** (5 minutes):
```python
def _format_search_results(self, raw_results):
    # How ChromaDB results are converted to usable format
```

**Questions to answer**:
- How are different document types handled?
- What metadata is stored with each document?
- How are search results formatted?

### Step 5: Test Document Operations
**Time**: 20 minutes  
**Action**: Run this code to see document operations in action

```python
# Create test script: test_document_ops.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.services.embedding_service import embedding_service

# Add a test document
doc_id = embedding_service.add_disease_information(
    content="Test disease information",
    crop="wheat", 
    disease_name="test_disease",
    source="test_source"
)
print(f"Added document: {doc_id}")

# Search for the document
results = embedding_service.search_disease_information(
    query="test disease",
    crop="wheat"
)
print(f"Found {len(results)} results")
for result in results:
    print(f"- {result['id']}: {result['content'][:50]}...")
```

## 🎯 Phase 3: LLM Integration Layer (30 minutes)

### Step 6: Read LLM Service (`app/services/llm_service.py`)
**Time**: 30 minutes  
**Focus**: LLM provider management and error handling

**Read in this order**:

1. **Data Structures** (5 minutes):
```python
@dataclass
class LLMRequest:
    prompt: str
    system_message: Optional[str] = None
    max_tokens: Optional[int] = None
    
@dataclass  
class LLMResponse:
    content: str
    provider: str
    model: str
    tokens_used: int
```

2. **Main Service Class** (15 minutes):
```python
class LLMService:
    async def generate_response(self, prompt, system_message=None):
        # Main method for getting LLM responses
        
    def _is_circuit_breaker_open(self, provider):
        # Circuit breaker pattern for resilience
        
    async def _generate_with_retry(self, client, request):
        # Retry logic with exponential backoff
```

3. **Provider Clients** (10 minutes):
```python
class OpenAIClient(LLMClient):
    async def generate_response(self, request):
        # OpenAI API integration
        
class AnthropicClient(LLMClient):  
    async def generate_response(self, request):
        # Anthropic API integration
```

**Questions to answer**:
- How does failover between providers work?
- What is the circuit breaker pattern doing?
- How are retries handled?

## 🎯 Phase 4: RAG Engine Core (60 minutes)

### Step 7: Read RAG Engine Overview (`app/services/rag_engine.py`)
**Time**: 15 minutes  
**Focus**: Class structure and main methods

**Start with the class definition and main methods**:
```python
class RAGEngine:
    def __init__(self):
        # What components are initialized?
        
    async def search_and_generate(self):
        # Main entry point - complete RAG pipeline
        
    def retrieve_documents(self):
        # Document retrieval step
        
    async def generate_grounded_response(self):
        # Response generation step
```

**Questions to answer**:
- What are the main components of the RAG engine?
- What is the overall flow of the pipeline?
- Which methods are async and why?

### Step 8: Deep Dive into Document Retrieval
**Time**: 20 minutes  
**Focus**: How documents are found and ranked

**Read this method carefully**:
```python
def retrieve_documents(self, query, collections=None, top_k=5, similarity_threshold=None):
    # Step 1: Set default collections if none provided
    if collections is None:
        collections = ["agricultural_knowledge", "government_schemes", ...]
    
    # Step 2: Search each collection
    all_results = []
    for collection in collections:
        results = self.vector_db.query_documents(
            collection_name=collection,
            query_text=query,
            n_results=top_k
        )
        
        # Step 3: Format and filter results
        formatted_results = self.embedding_service._format_search_results(results)
        filtered_results = [
            result for result in formatted_results 
            if result.get("similarity_score", 0) >= similarity_threshold
        ]
        
        # Step 4: Add metadata
        for result in filtered_results:
            result["metadata"]["collection"] = collection
            result["metadata"]["retrieval_query"] = query
            result["metadata"]["retrieved_at"] = datetime.now().isoformat()
        
        all_results.extend(filtered_results)
    
    # Step 5: Sort by similarity and return top results
    all_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
    return all_results[:top_k]
```

**Questions to answer**:
- How are multiple collections searched?
- How is similarity filtering applied?
- What metadata is added to results?
- How are results ranked and limited?

### Step 9: Deep Dive into Response Generation
**Time**: 25 minutes  
**Focus**: How LLM responses are generated and validated

**Read these methods in order**:

1. **Main Generation Method** (10 minutes):
```python
async def generate_grounded_response(self, query, retrieved_documents, response_type="comprehensive", language="en"):
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
        language=language
    )
    
    # Validate source grounding
    grounding_validation = self._validate_source_grounding(
        response_data["response"], retrieved_documents
    )
    
    response_data.update(grounding_validation)
    return response_data
```

2. **Context Preparation** (5 minutes):
```python
def _prepare_context(self, documents):
    context_parts = []
    for i, doc in enumerate(documents):
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})
        
        source_ref = f"[Source {i+1}]"
        source_info = f"Source: {metadata.get('source', 'Unknown')}"
        
        doc_context = f"{source_ref} {source_info}\n{content}\n\n"
        context_parts.append(doc_context)
    
    return "".join(context_parts)
```

3. **LLM Integration** (10 minutes):
```python
async def _generate_response_with_grounding(self, query, context, retrieved_documents, response_type, language):
    # Create system message for agricultural context
    system_message = self._create_system_message(response_type, language)
    
    # Create user prompt with context and query
    user_prompt = self._create_user_prompt(query, context, response_type, language)
    
    # Call LLM service to generate response
    llm_response = await llm_service.generate_response(
        prompt=user_prompt,
        system_message=system_message,
        max_tokens=self._get_max_tokens_for_response_type(response_type),
        temperature=0.3
    )
    
    # Return structured response with metadata
    return {
        "response": llm_response.content,
        "sources": sources,
        "llm_metadata": {
            "provider": llm_response.provider,
            "model": llm_response.model,
            "tokens_used": llm_response.tokens_used,
            "response_time": llm_response.response_time
        }
    }
```

**Questions to answer**:
- How is context prepared from documents?
- How are system messages and user prompts created?
- What metadata is returned with responses?
- How is source grounding validated?

## 🎯 Phase 5: API Layer and Testing (30 minutes)

### Step 10: Read RAG API (`app/api/rag.py`)
**Time**: 15 minutes  
**Focus**: REST API endpoints and request/response models

**Read these key endpoints**:
```python
@router.post("/query")
async def rag_query(request: RAGQueryRequest):
    # Main RAG query endpoint
    
@router.post("/retrieve")  
async def retrieve_documents(request: DocumentRetrievalRequest):
    # Document retrieval only
    
@router.post("/ingest")
async def ingest_documents(request: DocumentIngestionRequest):
    # Add new documents
```

**Questions to answer**:
- What are the request/response models?
- How are errors handled in the API?
- What endpoints are available?

### Step 11: Run and Study Test Scripts
**Time**: 15 minutes  
**Action**: Execute test scripts to see the system in action

```bash
# Run the comprehensive demo
python demo_rag_llm_integration.py

# Run the LLM integration test  
python test_rag_with_llm.py

# Run unit tests
python -m pytest tests/test_rag_engine.py -v
```

**Questions to answer**:
- How do the components work together?
- What does a complete RAG flow look like?
- How are errors handled in practice?

## 🎯 Phase 6: Advanced Understanding (Optional - 45 minutes)

### Step 12: Study Error Handling and Fallbacks
**Time**: 15 minutes  
**Focus**: How the system handles failures

**Look for these patterns**:
```python
try:
    # Primary operation
    response = await llm_service.generate_response(...)
except Exception as e:
    # Fallback operation
    response = self._generate_simple_response_fallback(...)
```

### Step 13: Study Validation and Quality Control
**Time**: 15 minutes  
**Focus**: How response quality is ensured

```python
def _validate_source_grounding(self, response, retrieved_documents):
    # Check for source references in response
    source_pattern = r"\[Source \d+\]"
    source_references = re.findall(source_pattern, response)
    
    # Calculate grounding metrics
    grounding_score = referenced_sources / max(total_sources, 1)
    
    # Check for potential hallucination indicators
    hallucination_indicators = self._detect_hallucination_indicators(response, retrieved_documents)
```

### Step 14: Study Performance and Monitoring
**Time**: 15 minutes  
**Focus**: How the system tracks performance

```python
def get_metrics(self):
    return {
        "total_requests": self.metrics.total_requests,
        "success_rate": self.metrics.successful_requests / max(self.metrics.total_requests, 1),
        "total_tokens_used": self.metrics.total_tokens_used,
        "average_response_time": self.metrics.average_response_time,
        "provider_usage": self.metrics.provider_usage
    }
```

## 📝 Summary Checklist

After completing all phases, you should understand:

- ✅ How documents are stored and retrieved using vector embeddings
- ✅ How multiple LLM providers are managed with failover
- ✅ How the complete RAG pipeline orchestrates retrieval and generation
- ✅ How responses are validated for source grounding
- ✅ How errors are handled and fallbacks work
- ✅ How the system is monitored and optimized
- ✅ How the API layer exposes RAG functionality

## 🔧 Practical Exercises

1. **Modify a prompt template** in `_create_system_message()`
2. **Add a new document type** in `embedding_service.py`
3. **Create a custom search filter** in `retrieve_documents()`
4. **Add a new validation rule** in `_validate_source_grounding()`
5. **Implement a new LLM provider** following the existing pattern

This step-by-step approach will give you a comprehensive understanding of the RAG implementation and how all components work together.