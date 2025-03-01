# Vector Database Component

## Overview
The Vector Database component provides efficient storage and retrieval of text embeddings for semantic search capabilities. It uses ChromaDB as the underlying vector database to store text documents and their associated metadata. The component is designed to work alongside the Knowledge Graph to provide comprehensive context for narrative generation.

## Key Features
- Semantic search using embeddings from Sentence Transformers
- Flexible metadata filtering for contextual queries
- Memory management system with importance ratings and expiration
- Contextual retrieval that combines the vector store with knowledge graph entities
- Type-safe interfaces through Pydantic models

## Architecture
The Vector Database component consists of three main parts:
1. **VectorStore**: Low-level interface to ChromaDB operations
2. **MemoryManager**: Memory management abstraction with narrative focus
3. **ContextManager**: High-level context retrieval combining memories and entities

## Usage

### Basic Setup
```python
from Vector_Database import VectorStore, Document

# Initialize the vector store
vector_store = VectorStore(
    collection_name="narrative_data",
    persist_directory="./chroma_db",
    embedding_model="all-MiniLM-L6-v2"
)
```

### Adding Documents
```python
# Create a document
doc = Document(
    text="The sun was setting over the ancient forest of Elyndoria, casting golden light through the towering trees.",
    metadata={"type": "description", "location": "Elyndoria", "time": "evening"}
)

# Add to the vector store
vector_store.add_document(doc)
```

### Searching
```python
# Search by semantic similarity
results = vector_store.search(
    query="forest atmosphere",
    n_results=5
)

# Search by metadata
location_docs = vector_store.search_by_metadata(
    metadata_filter={"location": "Elyndoria"}
)
```

### Working with Memories
```python
from Vector_Database import MemoryManager, Memory

# Initialize memory manager
memory_manager = MemoryManager(
    persist_directory="./memories_db",
    collection_name="narrative_memories"
)

# Create a memory
memory = Memory(
    text="Aria revealed her true identity during the Council meeting.",
    source="narrative",
    memory_type="event",
    importance=8,
    location="Council Chambers",
    entity_ids=["character1", "location1"],
    tags=["revelation", "identity"]
)

# Add to memory database
memory_id = memory_manager.add_memory(memory)
```

### Retrieving Context
```python
from Vector_Database import ContextManager

# Initialize context manager
context_manager = ContextManager(
    vector_db_path="./narrative_db",
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="nasukili12"
)

# Get context for a query
context = context_manager.get_context_for_query(
    query="What happened at the Council meeting?",
    character_name="Aria",
    location_name="Council Chambers"
)

# Generate a narrative from context
narrative = context_manager.create_narrative_summary(context)
```

## Testing
To verify the Vector Database component is working correctly, run the test script:
```bash
python test_vector_db.py
```