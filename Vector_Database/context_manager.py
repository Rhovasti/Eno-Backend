import logging
import os
from typing import Dict, List, Optional, Union, Any, Set, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from .memory_manager import MemoryManager, Memory
from Knowledge_Graph.knowledge_manager import KnowledgeGraphManager
from Knowledge_Graph.models.entity_models import Character, Location, Event

# Set up logging
logging.basicConfig(
    filename='context_manager.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class NarrativeContext(BaseModel):
    """
    Represents a context for narrative generation, combining memories and entities.
    """
    query: str
    memories: List[Memory] = Field(default_factory=list)
    characters: List[Character] = Field(default_factory=list)
    locations: List[Location] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    character_focus: Optional[Character] = None
    location_focus: Optional[Location] = None
    event_focus: Optional[Event] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_text(self) -> str:
        """
        Convert the context to a formatted text representation.
        """
        text_parts = [f"Query: {self.query}", ""]
        
        # Add focus entities
        if self.character_focus:
            text_parts.append(f"Character Focus: {self.character_focus.name}")
            text_parts.append(f"Description: {self.character_focus.description}")
            text_parts.append("")
        
        if self.location_focus:
            text_parts.append(f"Location Focus: {self.location_focus.name}")
            text_parts.append(f"Description: {self.location_focus.description}")
            text_parts.append("")
        
        if self.event_focus:
            text_parts.append(f"Event Focus: {self.event_focus.name}")
            text_parts.append(f"Description: {self.event_focus.description}")
            text_parts.append("")
        
        # Add characters
        if self.characters:
            text_parts.append("Relevant Characters:")
            for char in self.characters:
                text_parts.append(f"- {char.name}: {char.description}")
            text_parts.append("")
        
        # Add locations
        if self.locations:
            text_parts.append("Relevant Locations:")
            for loc in self.locations:
                text_parts.append(f"- {loc.name}: {loc.description}")
            text_parts.append("")
        
        # Add events
        if self.events:
            text_parts.append("Relevant Events:")
            for evt in self.events:
                text_parts.append(f"- {evt.name}: {evt.description}")
            text_parts.append("")
        
        # Add memories
        if self.memories:
            text_parts.append("Relevant Memories:")
            for memory in self.memories:
                text_parts.append(f"- [{memory.memory_type}] {memory.text}")
            text_parts.append("")
        
        return "\n".join(text_parts)

class ContextManager:
    """
    Manager for creating and retrieving narrative contexts.
    Combines the Knowledge Graph and Vector Database.
    """
    
    def __init__(
        self,
        vector_db_path: str = "./narrative_db",
        embedding_model: str = "all-MiniLM-L6-v2",
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "nasukili12",
        neo4j_database: str = "population"
    ):
        """
        Initialize the context manager.
        
        Args:
            vector_db_path: Path to store vector database
            embedding_model: Name of embedding model to use
            neo4j_uri: URI for Neo4j connection
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            neo4j_database: Neo4j database name
        """
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            persist_directory=vector_db_path,
            embedding_model=embedding_model,
            collection_name="narrative_memory"
        )
        
        try:
            # Initialize knowledge graph manager
            self.kg_manager = KnowledgeGraphManager(
                uri=neo4j_uri,
                username=neo4j_user,
                password=neo4j_password,
                database=neo4j_database
            )
            self.kg_connected = True
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            self.kg_connected = False
        
        logging.info("Initialized context manager")
    
    def create_memory_from_text(
        self,
        text: str,
        source: str,
        memory_type: str = "general",
        importance: int = 5,
        location: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        expiration: Optional[datetime] = None
    ) -> Memory:
        """
        Create a memory from text.
        
        Args:
            text: The text content of the memory
            source: Source of the memory (user, system, character, etc.)
            memory_type: Type of memory
            importance: Importance rating (1-10)
            location: Optional location name
            entity_ids: Optional list of entity IDs associated with this memory
            tags: Optional list of tags
            expiration: Optional expiration date
            
        Returns:
            Created memory
        """
        memory = Memory(
            text=text,
            source=source,
            memory_type=memory_type,
            importance=importance,
            location=location,
            entity_ids=entity_ids or [],
            tags=tags or [],
            expiration=expiration,
            timestamp=datetime.now()
        )
        
        return memory
    
    def add_memory(self, memory: Memory) -> str:
        """
        Add a memory to the vector database.
        
        Args:
            memory: Memory to add
            
        Returns:
            ID of the added memory
        """
        return self.memory_manager.add_memory(memory)
    
    def get_context_for_query(
        self,
        query: str,
        character_name: Optional[str] = None,
        location_name: Optional[str] = None,
        event_name: Optional[str] = None,
        n_memories: int = 10,
        n_related_entities: int = 5
    ) -> NarrativeContext:
        """
        Generate a narrative context for a query.
        
        Args:
            query: Query to generate context for
            character_name: Optional name of character to focus on
            location_name: Optional name of location to focus on
            event_name: Optional name of event to focus on
            n_memories: Number of memories to include
            n_related_entities: Number of related entities to include
            
        Returns:
            Generated context
        """
        context = NarrativeContext(query=query)
        
        # Get focus entities if names provided
        if character_name and self.kg_connected:
            context.character_focus = self.kg_manager.get_character(character_name)
        
        if location_name and self.kg_connected:
            context.location_focus = self.kg_manager.get_location(location_name)
        
        if event_name and self.kg_connected:
            context.event_focus = self.kg_manager.get_event(event_name)
        
        # Get relevant memories from vector database
        memory_filter = {}
        if location_name:
            memory_filter["location"] = location_name
        
        # Get character entity ID if available
        character_id = None
        if context.character_focus:
            for rel in self.kg_manager.get_related_entities(context.character_focus):
                entity = rel.get('entity', {})
                context.characters.append(self.kg_manager.get_entity_by_name(Character, entity.get('name')))
        
        # Get location entity ID if available
        location_id = None
        if context.location_focus:
            for rel in self.kg_manager.get_related_entities(context.location_focus):
                entity = rel.get('entity', {})
                if 'Character' in entity.get('labels', []):
                    char = self.kg_manager.get_entity_by_name(Character, entity.get('name'))
                    if char:
                        context.characters.append(char)
                elif 'Event' in entity.get('labels', []):
                    evt = self.kg_manager.get_entity_by_name(Event, entity.get('name'))
                    if evt:
                        context.events.append(evt)
        
        # Get relevant memories
        relevant_memories = self.memory_manager.search_memories(
            query=query,
            n_results=n_memories,
            filter_metadata=memory_filter,
            entity_id=character_id
        )
        context.memories = relevant_memories
        
        # Get additional character context if we have a character focus
        if context.character_focus and len(context.characters) < n_related_entities:
            # Get characters with similar names or descriptions
            similar_characters = []
            if self.kg_connected:
                results = self.kg_manager.search_entities(
                    entity_type=Character,
                    name=context.character_focus.name
                )
                for result in results:
                    if 'name' in result and result['name'] != context.character_focus.name:
                        char = self.kg_manager.get_entity_by_name(Character, result['name'])
                        if char:
                            similar_characters.append(char)
                
                # Add similar characters up to the limit
                for char in similar_characters[:n_related_entities - len(context.characters)]:
                    if char not in context.characters:
                        context.characters.append(char)
        
        # Get additional location context if we have a location focus
        if context.location_focus and len(context.locations) < n_related_entities:
            # Get nearby locations
            nearby_locations = []
            if self.kg_connected:
                for rel in self.kg_manager.get_related_entities(context.location_focus):
                    entity = rel.get('entity', {})
                    if 'Location' in entity.get('labels', []):
                        loc = self.kg_manager.get_entity_by_name(Location, entity.get('name'))
                        if loc and loc.name != context.location_focus.name:
                            nearby_locations.append(loc)
                
                # Add nearby locations up to the limit
                for loc in nearby_locations[:n_related_entities - len(context.locations)]:
                    context.locations.append(loc)
        
        return context
    
    def search_memories_by_text(
        self,
        query: str,
        n_results: int = 10,
        memory_type: Optional[str] = None,
        min_importance: Optional[int] = None
    ) -> List[Memory]:
        """
        Search for memories by text similarity.
        
        Args:
            query: Text query
            n_results: Number of results to return
            memory_type: Optional memory type filter
            min_importance: Optional minimum importance
            
        Returns:
            List of matching memories
        """
        return self.memory_manager.search_memories(
            query=query,
            n_results=n_results,
            memory_type=memory_type,
            min_importance=min_importance
        )
    
    def search_entities(
        self,
        query: str,
        entity_type: str = "Character",
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for entities by name or description.
        
        Args:
            query: Text query
            entity_type: Type of entity to search for
            n_results: Number of results to return
            
        Returns:
            List of matching entities
        """
        if not self.kg_connected:
            return []
        
        if entity_type == "Character":
            return self.kg_manager.search_entities(
                entity_type=Character,
                name=query
            )[:n_results]
        elif entity_type == "Location":
            return self.kg_manager.search_entities(
                entity_type=Location,
                name=query
            )[:n_results]
        elif entity_type == "Event":
            return self.kg_manager.search_entities(
                entity_type=Event,
                name=query
            )[:n_results]
        else:
            return []
    
    def get_entity_context(
        self,
        entity_name: str,
        entity_type: str = "Character",
        n_memories: int = 10,
        n_related_entities: int = 5
    ) -> Dict[str, Any]:
        """
        Get context for a specific entity.
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of entity
            n_memories: Number of memories to include
            n_related_entities: Number of related entities to include
            
        Returns:
            Dictionary with entity context
        """
        if not self.kg_connected:
            return {"error": "Knowledge graph not connected"}
        
        context = {
            "entity_name": entity_name,
            "entity_type": entity_type,
            "entity": None,
            "memories": [],
            "related_entities": []
        }
        
        # Get the entity
        if entity_type == "Character":
            entity = self.kg_manager.get_character(entity_name)
        elif entity_type == "Location":
            entity = self.kg_manager.get_location(entity_name)
        elif entity_type == "Event":
            entity = self.kg_manager.get_event(entity_name)
        else:
            return {"error": f"Unknown entity type: {entity_type}"}
        
        if not entity:
            return {"error": f"Entity not found: {entity_name}"}
        
        context["entity"] = entity
        
        # Get related entities
        if hasattr(entity, 'id'):
            related = self.kg_manager.get_related_entities(entity)
            if related:
                context["related_entities"] = related[:n_related_entities]
        
        # Get memories related to the entity
        if hasattr(entity, 'id'):
            memories = self.memory_manager.search_by_entity(entity.id, limit=n_memories)
            if memories:
                context["memories"] = memories
        
        # If no memories found by ID, try searching by name
        if not context["memories"]:
            memories = self.memory_manager.search_memories(
                query=entity_name,
                n_results=n_memories
            )
            context["memories"] = memories
        
        return context
    
    def create_narrative_summary(self, context: NarrativeContext) -> str:
        """
        Create a narrative summary from a context.
        
        Args:
            context: Context to summarize
            
        Returns:
            Narrative summary text
        """
        # Convert context to text
        context_text = context.to_text()
        
        # You would typically use an LLM here to generate a summary
        # For now, we'll just return the formatted context
        return context_text
    
    def add_narrative_memory(
        self,
        text: str,
        source: str,
        related_entities: List[Tuple[str, str]] = None,
        location: Optional[str] = None,
        importance: int = 5,
        tags: List[str] = None
    ) -> str:
        """
        Add a narrative memory, optionally linked to entities.
        
        Args:
            text: Text content of the memory
            source: Source of the memory
            related_entities: List of tuples (entity_name, entity_type)
            location: Optional location name
            importance: Importance rating (1-10)
            tags: Optional list of tags
            
        Returns:
            ID of the created memory
        """
        # Initialize entity IDs list
        entity_ids = []
        
        # Get entity IDs if related entities provided
        if related_entities and self.kg_connected:
            for entity_name, entity_type in related_entities:
                if entity_type == "Character":
                    entity = self.kg_manager.get_character(entity_name)
                elif entity_type == "Location":
                    entity = self.kg_manager.get_location(entity_name)
                elif entity_type == "Event":
                    entity = self.kg_manager.get_event(entity_name)
                else:
                    continue
                
                if entity and hasattr(entity, 'id'):
                    entity_ids.append(entity.id)
        
        # Create memory
        memory = self.create_memory_from_text(
            text=text,
            source=source,
            memory_type="narrative",
            importance=importance,
            location=location,
            entity_ids=entity_ids,
            tags=tags or []
        )
        
        # Add memory to database
        memory_id = self.add_memory(memory)
        
        return memory_id