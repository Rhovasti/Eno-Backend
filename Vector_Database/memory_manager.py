import logging
import os
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel, Field

from .vector_store import VectorStore, Document

# Set up logging
logging.basicConfig(
    filename='memory_manager.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Memory(BaseModel):
    """
    A single memory item that can be stored in the vector database.
    """
    text: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    importance: int = 1  # 1-10 scale
    expiration: Optional[datetime] = None
    entity_ids: List[str] = Field(default_factory=list)  # References to entities in the knowledge graph
    location: Optional[str] = None
    memory_type: str = "general"  # general, conversation, event, etc.
    tags: List[str] = Field(default_factory=list)
    id: Optional[str] = None
    
    def to_document(self) -> Document:
        """
        Convert the memory to a document for storage in the vector database.
        """
        metadata = {
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "memory_type": self.memory_type,
            "tags": ",".join(self.tags),
            "entity_ids": ",".join(self.entity_ids)
        }
        
        if self.expiration:
            metadata["expiration"] = self.expiration.isoformat()
        
        if self.location:
            metadata["location"] = self.location
        
        return Document(
            text=self.text,
            metadata=metadata,
            id=self.id
        )
    
    @classmethod
    def from_document(cls, document: Document) -> "Memory":
        """
        Create a memory from a document retrieved from the vector database.
        """
        metadata = document.metadata or {}
        
        # Parse timestamps
        timestamp = metadata.get("timestamp")
        if timestamp:
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        expiration = metadata.get("expiration")
        if expiration:
            try:
                expiration = datetime.fromisoformat(expiration)
            except (ValueError, TypeError):
                expiration = None
        
        # Parse lists
        tags = metadata.get("tags", "")
        if isinstance(tags, str):
            tags = tags.split(",") if tags else []
        
        entity_ids = metadata.get("entity_ids", "")
        if isinstance(entity_ids, str):
            entity_ids = entity_ids.split(",") if entity_ids else []
        
        # Create memory
        return cls(
            id=document.id,
            text=document.text,
            source=metadata.get("source", "unknown"),
            timestamp=timestamp,
            importance=int(metadata.get("importance", 1)),
            expiration=expiration,
            entity_ids=entity_ids,
            location=metadata.get("location"),
            memory_type=metadata.get("memory_type", "general"),
            tags=tags
        )

class MemoryManager:
    """
    Manager for long-term memory storage and retrieval using vector database.
    """
    
    def __init__(
        self,
        persist_directory: str = "./memory_db",
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "narrative_memory"
    ):
        """
        Initialize the memory manager.
        
        Args:
            persist_directory: Directory to persist the vector database
            embedding_model: Model to use for embeddings
            collection_name: Name of the collection in the vector database
        """
        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            embedding_model=embedding_model,
            collection_name=collection_name
        )
        
        logging.info(f"Initialized memory manager with collection: {collection_name}")
    
    def add_memory(self, memory: Memory) -> str:
        """
        Add a memory to the vector database.
        
        Args:
            memory: Memory to add
            
        Returns:
            ID of the added memory
        """
        if not memory.id:
            memory.id = str(uuid.uuid4())
        
        document = memory.to_document()
        self.vector_store.add_document(document)
        
        logging.info(f"Added memory: {memory.id} - {memory.text[:50]}...")
        return memory.id
    
    def add_memories(self, memories: List[Memory]) -> List[str]:
        """
        Add multiple memories to the vector database.
        
        Args:
            memories: List of memories to add
            
        Returns:
            List of IDs of the added memories
        """
        if not memories:
            return []
        
        # Generate IDs for memories that don't have them
        for memory in memories:
            if not memory.id:
                memory.id = str(uuid.uuid4())
        
        # Convert memories to documents
        documents = [memory.to_document() for memory in memories]
        
        # Add documents to vector store
        self.vector_store.add_documents(documents)
        
        memory_ids = [memory.id for memory in memories]
        logging.info(f"Added {len(memories)} memories")
        return memory_ids
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: ID of the memory to get
            
        Returns:
            Memory if found, None otherwise
        """
        document = self.vector_store.get_document(memory_id)
        if not document:
            return None
        
        return Memory.from_document(document)
    
    def search_memories(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_importance: Optional[int] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        entity_id: Optional[str] = None,
        location: Optional[str] = None,
        include_expired: bool = False
    ) -> List[Memory]:
        """
        Search for memories similar to the query.
        
        Args:
            query: Query string
            n_results: Number of results to return
            filter_metadata: Raw metadata filter to apply
            min_importance: Minimum importance level (1-10)
            memory_type: Type of memory to filter by
            tags: Tags to filter by
            entity_id: Entity ID to filter by
            location: Location to filter by
            include_expired: Whether to include expired memories
            
        Returns:
            List of matching memories
        """
        # Build metadata filter
        combined_filter = filter_metadata or {}
        
        if min_importance is not None:
            combined_filter["importance"] = {"$gte": min_importance}
        
        if memory_type is not None:
            combined_filter["memory_type"] = memory_type
        
        if location is not None:
            combined_filter["location"] = location
        
        if tags:
            # This is a simplification - in practice, filtering by tags in Chroma
            # requires more complex handling since we store them as comma-separated values
            tag_filters = []
            for tag in tags:
                tag_filters.append({"$contains": tag})
            
            # We would need to add these filters to a proper query builder
            pass
        
        if entity_id:
            # Similar to tags, this is a simplification
            pass
        
        if not include_expired:
            # Filter out expired memories
            now = datetime.now().isoformat()
            expiration_filter = {"$or": [
                {"expiration": {"$exists": False}},
                {"expiration": None},
                {"expiration": {"$gt": now}}
            ]}
            # In practice, this would need to be combined with other filters
        
        # Search documents
        documents = self.vector_store.search(
            query=query,
            n_results=n_results,
            filter_metadata=combined_filter
        )
        
        # Convert documents to memories
        memories = [Memory.from_document(doc) for doc in documents]
        
        # Apply manual filtering for the complex cases that Chroma can't handle well
        if tags or entity_id or (not include_expired):
            filtered_memories = []
            for memory in memories:
                # Check tags
                if tags and not any(tag in memory.tags for tag in tags):
                    continue
                
                # Check entity ID
                if entity_id and entity_id not in memory.entity_ids:
                    continue
                
                # Check expiration
                if not include_expired and memory.expiration and memory.expiration < datetime.now():
                    continue
                
                filtered_memories.append(memory)
            
            memories = filtered_memories
        
        return memories
    
    def search_by_entity(self, entity_id: str, limit: int = 100) -> List[Memory]:
        """
        Search for memories associated with a specific entity.
        
        Args:
            entity_id: ID of the entity
            limit: Maximum number of results to return
            
        Returns:
            List of memories associated with the entity
        """
        # This is a simplification since Chroma doesn't easily support substring matching in lists
        # In a real implementation, you might need a more complex query or post-filtering
        
        # Get all potentially relevant documents
        documents = self.vector_store.search_by_metadata(
            metadata_filter={},  # We'll filter manually
            limit=limit
        )
        
        # Filter manually
        memories = []
        for doc in documents:
            memory = Memory.from_document(doc)
            if entity_id in memory.entity_ids:
                memories.append(memory)
                if len(memories) >= limit:
                    break
        
        return memories
    
    def search_by_location(self, location: str, limit: int = 100) -> List[Memory]:
        """
        Search for memories associated with a specific location.
        
        Args:
            location: Location name
            limit: Maximum number of results to return
            
        Returns:
            List of memories associated with the location
        """
        documents = self.vector_store.search_by_metadata(
            metadata_filter={"location": location},
            limit=limit
        )
        
        return [Memory.from_document(doc) for doc in documents]
    
    def get_recent_memories(
        self,
        limit: int = 100,
        days: Optional[int] = None,
        memory_type: Optional[str] = None
    ) -> List[Memory]:
        """
        Get recent memories, optionally filtered by type.
        
        Args:
            limit: Maximum number of results to return
            days: Number of days to look back
            memory_type: Type of memory to filter by
            
        Returns:
            List of recent memories
        """
        # Build metadata filter
        filter_metadata = {}
        
        if memory_type:
            filter_metadata["memory_type"] = memory_type
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            filter_metadata["timestamp"] = {"$gte": cutoff_date}
        
        # Get documents
        documents = self.vector_store.search_by_metadata(
            metadata_filter=filter_metadata,
            limit=limit
        )
        
        # Convert to memories
        memories = [Memory.from_document(doc) for doc in documents]
        
        # Sort by timestamp (most recent first)
        memories.sort(key=lambda x: x.timestamp, reverse=True)
        
        return memories[:limit]
    
    def update_memory(self, memory: Memory) -> bool:
        """
        Update a memory in the vector database.
        
        Args:
            memory: Memory to update
            
        Returns:
            True if successful, False otherwise
        """
        if not memory.id:
            logging.error("Cannot update memory without ID")
            return False
        
        document = memory.to_document()
        return self.vector_store.update_document(document)
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from the vector database.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            True if successful, False otherwise
        """
        return self.vector_store.delete_document(memory_id)
    
    def update_memory_importance(self, memory_id: str, importance: int) -> bool:
        """
        Update the importance of a memory.
        
        Args:
            memory_id: ID of the memory to update
            importance: New importance value (1-10)
            
        Returns:
            True if successful, False otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        memory.importance = max(1, min(10, importance))  # Ensure 1-10 range
        return self.update_memory(memory)
    
    def add_tags_to_memory(self, memory_id: str, tags: List[str]) -> bool:
        """
        Add tags to a memory.
        
        Args:
            memory_id: ID of the memory to update
            tags: Tags to add
            
        Returns:
            True if successful, False otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        # Add tags (avoid duplicates)
        existing_tags = set(memory.tags)
        for tag in tags:
            existing_tags.add(tag)
        memory.tags = list(existing_tags)
        
        return self.update_memory(memory)
    
    def add_entity_to_memory(self, memory_id: str, entity_id: str) -> bool:
        """
        Associate an entity with a memory.
        
        Args:
            memory_id: ID of the memory to update
            entity_id: ID of the entity to associate
            
        Returns:
            True if successful, False otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        # Add entity ID (avoid duplicates)
        if entity_id not in memory.entity_ids:
            memory.entity_ids.append(entity_id)
            return self.update_memory(memory)
        
        return True
    
    def set_memory_expiration(self, memory_id: str, expiration: datetime) -> bool:
        """
        Set the expiration date for a memory.
        
        Args:
            memory_id: ID of the memory to update
            expiration: Expiration date
            
        Returns:
            True if successful, False otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        memory.expiration = expiration
        return self.update_memory(memory)
    
    def remove_expired_memories(self) -> int:
        """
        Remove all expired memories from the database.
        
        Returns:
            Number of memories removed
        """
        now = datetime.now().isoformat()
        
        # This would be better with a proper query, but Chroma's filtering 
        # capabilities are limited for this type of operation
        
        # Get all documents with expiration dates
        documents = self.vector_store.search_by_metadata(
            metadata_filter={"expiration": {"$exists": True}},
            limit=10000  # Use a reasonable limit
        )
        
        # Filter to find expired ones
        expired_ids = []
        for doc in documents:
            metadata = doc.metadata or {}
            expiration = metadata.get("expiration")
            if expiration and expiration < now:
                expired_ids.append(doc.id)
        
        # Delete expired documents
        if expired_ids:
            self.vector_store.delete_documents(expired_ids)
        
        logging.info(f"Removed {len(expired_ids)} expired memories")
        return len(expired_ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory database.
        
        Returns:
            Dictionary of statistics
        """
        # Get collection stats
        stats = self.vector_store.get_collection_stats()
        
        # Add memory-specific stats
        stats["memory_manager"] = {
            "types_count": {},
            "importance_distribution": {},
            "expired_count": 0,
            "tags_distribution": {},
            "source_distribution": {},
            "location_distribution": {},
            "entity_distribution": {}
        }
        
        return stats
    
    def reset(self) -> bool:
        """
        Reset the memory database (delete all memories).
        
        Returns:
            True if successful, False otherwise
        """
        return self.vector_store.reset_collection()