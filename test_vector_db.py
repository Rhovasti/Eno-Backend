#!/usr/bin/env python3
"""
Test script for the Vector Database implementation.
Creates and tests basic functionality of the vector database and memory system.
"""

import logging
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Vector_Database import (
    VectorStore, Document,
    MemoryManager, Memory,
    ContextManager, NarrativeContext
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_vector_store():
    """Test the basic VectorStore functionality."""
    print("\n=== Testing VectorStore ===")
    
    # Initialize vector store
    vector_store = VectorStore(
        collection_name="test_collection",
        persist_directory="./test_db",
        embedding_model="all-MiniLM-L6-v2"
    )
    
    # Create test documents
    doc1 = Document(
        text="The sun was setting over the ancient forest of Elyndoria, casting golden light through the towering trees.",
        metadata={"type": "description", "location": "Elyndoria", "time": "evening"},
        id="doc1"
    )
    
    doc2 = Document(
        text="Aria stood at the edge of the clearing, her silver hair reflecting the moonlight as she prepared for the ritual.",
        metadata={"type": "character", "name": "Aria", "location": "Elyndoria", "time": "night"},
        id="doc2"
    )
    
    doc3 = Document(
        text="The dwarven stronghold of Ironforge was bustling with activity as smiths hammered away at their forges.",
        metadata={"type": "description", "location": "Ironforge", "time": "day"},
        id="doc3"
    )
    
    # Add documents
    print("Adding documents...")
    vector_store.add_documents([doc1, doc2, doc3])
    
    # Search for similar documents
    print("\nSearching for 'forest'...")
    results = vector_store.search("forest", n_results=2)
    for i, doc in enumerate(results, 1):
        print(f"Result {i}: {doc.text[:50]}...")
    
    # Search by metadata
    print("\nSearching for documents about Elyndoria...")
    results = vector_store.search_by_metadata({"location": "Elyndoria"}, limit=10)
    for i, doc in enumerate(results, 1):
        print(f"Result {i}: {doc.text[:50]}...")
    
    # Get document by ID
    print("\nGetting document by ID...")
    doc = vector_store.get_document("doc2")
    if doc:
        print(f"Found document: {doc.text[:50]}...")
    
    # Collection stats
    print("\nGetting collection stats...")
    stats = vector_store.get_collection_stats()
    print(f"Collection contains {stats['count']} documents")
    if 'metadata_keys' in stats:
        print(f"Metadata keys: {', '.join(stats['metadata_keys'])}")
    
    # Reset collection
    print("\nResetting collection...")
    vector_store.reset_collection()
    
    return vector_store

def test_memory_manager():
    """Test the MemoryManager functionality."""
    print("\n=== Testing MemoryManager ===")
    
    # Initialize memory manager
    memory_manager = MemoryManager(
        persist_directory="./test_memory_db",
        collection_name="test_memories"
    )
    
    # Create test memories
    memory1 = Memory(
        text="Aria revealed her true identity as the heir to the Elyndorian throne during the Council meeting.",
        source="narrative",
        memory_type="event",
        importance=8,
        location="Council Chambers",
        entity_ids=["character1", "location1"],
        tags=["revelation", "identity", "politics"]
    )
    
    memory2 = Memory(
        text="Thorne crafted a legendary axe from the rare metal found in the deepest mines of Ironforge.",
        source="narrative",
        memory_type="achievement",
        importance=7,
        location="Ironforge",
        entity_ids=["character2", "location2", "item1"],
        tags=["crafting", "legendary", "weapon"]
    )
    
    memory3 = Memory(
        text="The ancient treaty between elves and dwarves was renewed following months of tense negotiations.",
        source="narrative",
        memory_type="event",
        importance=9,
        location="Neutral Grounds",
        entity_ids=["faction1", "faction2", "event1"],
        tags=["treaty", "diplomacy", "alliance"],
        expiration=datetime.now() + timedelta(days=365)
    )
    
    # Add memories
    print("Adding memories...")
    memory1.id = memory_manager.add_memory(memory1)
    memory2.id = memory_manager.add_memory(memory2)
    memory3.id = memory_manager.add_memory(memory3)
    
    # Search for memories
    print("\nSearching for memories about 'treaty'...")
    results = memory_manager.search_memories("treaty", n_results=2)
    for i, memory in enumerate(results, 1):
        print(f"Result {i}: {memory.text[:50]}...")
    
    # Search by entity ID
    print("\nSearching for memories related to character1...")
    results = memory_manager.search_by_entity("character1", limit=10)
    for i, memory in enumerate(results, 1):
        print(f"Result {i}: {memory.text[:50]}...")
    
    # Get recent memories
    print("\nGetting recent memories...")
    results = memory_manager.get_recent_memories(limit=5)
    for i, memory in enumerate(results, 1):
        print(f"Memory {i}: {memory.text[:50]}...")
    
    # Update memory importance
    print("\nUpdating memory importance...")
    memory_manager.update_memory_importance(memory1.id, 10)
    updated_memory = memory_manager.get_memory(memory1.id)
    print(f"Updated importance: {updated_memory.importance}")
    
    # Add tags
    print("\nAdding tags to memory...")
    memory_manager.add_tags_to_memory(memory2.id, ["masterwork", "inheritance"])
    updated_memory = memory_manager.get_memory(memory2.id)
    print(f"Updated tags: {', '.join(updated_memory.tags)}")
    
    # Reset memory manager
    print("\nResetting memory collection...")
    memory_manager.reset()
    
    return memory_manager

def main():
    """Main test function."""
    print("Starting Vector Database tests...")
    
    try:
        # Test vector store
        vector_store = test_vector_store()
        
        # Test memory manager
        memory_manager = test_memory_manager()
        
        # Test integration with the Knowledge Graph can be added when both components are present
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())