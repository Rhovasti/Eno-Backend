import logging
from typing import Dict, List, Optional, Union, Any, Type, TypeVar
from datetime import datetime
from py2neo import Node, Relationship

from .graph_connector import KnowledgeGraphConnector
from .models.entity_models import (
    Entity, Character, Location, Event, Faction, Item, Concept
)
from .utils.relationships import RelationshipType, create_relationship_properties
from .schema_adapter import SchemaAdapter

# Setup logging
logging.basicConfig(
    filename='knowledge_manager.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Type variable for entity models
T = TypeVar('T', bound=Entity)

class KnowledgeGraphManager:
    """
    High-level manager for the knowledge graph.
    
    Provides simplified API for working with the knowledge graph,
    handling entity creation, relationship management, and querying.
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "nasukili12",
        database: str = "population"
    ):
        """
        Initialize the knowledge graph manager.
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
            database: Name of the Neo4j database
        """
        self.connector = KnowledgeGraphConnector(
            uri=uri,
            username=username,
            password=password,
            database=database
        )
        
        # Initialize schema adapter
        self.schema_adapter = SchemaAdapter(self.connector)
        
        # Entity type to Neo4j label mapping
        self.entity_types = {
            Character: "Character",
            Location: "Location",
            Event: "Event",
            Faction: "Faction",
            Item: "Item",
            Concept: "Concept"
        }
        
        # Update label mappings based on schema adapter
        for entity_class, label in self.entity_types.items():
            mapped_label = self.schema_adapter.map_entity_model(label)
            if mapped_label != label:
                logging.info(f"Mapped entity type {label} to existing label {mapped_label}")
                self.entity_types[entity_class] = mapped_label
        
        logging.info("Knowledge Graph Manager initialized")
    
    def add_entity(self, entity: Entity) -> Node:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity: The entity to add
            
        Returns:
            The created Neo4j node
        """
        entity_type = type(entity).__name__
        
        # Map to existing label if needed
        db_entity_type = self.schema_adapter.map_entity_model(entity_type)
        
        # Get properties and map to database schema
        properties = entity.to_dict()
        mapped_properties = self.schema_adapter.get_property_mapping(db_entity_type, properties)
        
        # Create the entity
        node = self.connector.create_entity(db_entity_type, mapped_properties)
        
        logging.info(f"Added {db_entity_type} entity: {entity.name}")
        return node
    
    def get_entity_by_name(self, entity_type: Type[T], name: str) -> Optional[T]:
        """
        Find an entity by its type and name.
        
        Args:
            entity_type: The type of entity to find
            name: The name of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        # Get Neo4j type from entity class
        neo4j_type = self.entity_types.get(entity_type, entity_type.__name__)
        
        # Map to existing label if needed
        db_neo4j_type = self.schema_adapter.map_entity_model(neo4j_type)
        
        # Try to find the node
        node = self.connector.get_entity_by_name(db_neo4j_type, name)
        
        if node is None:
            # If not found, try a case-insensitive search
            cypher_query = f"""
            MATCH (n:{db_neo4j_type})
            WHERE toLower(n.name) = toLower($name)
            RETURN n LIMIT 1
            """
            results = self.connector.execute_query(cypher_query, {"name": name})
            
            if results and 'n' in results[0]:
                node = results[0]['n']
            else:
                return None
        
        # Convert Neo4j node to entity object
        return self._node_to_entity(node, entity_type)
    
    def add_relationship(
        self,
        source_entity: Entity,
        target_entity: Entity,
        relationship_type: RelationshipType,
        **properties
    ) -> Relationship:
        """
        Create a relationship between two entities.
        
        Args:
            source_entity: Source entity
            target_entity: Target entity
            relationship_type: Type of relationship
            **properties: Additional properties for the relationship
            
        Returns:
            The created relationship
        """
        # Map relationship type to existing type if needed
        db_rel_type = self.schema_adapter.map_relationship_type(relationship_type.value)
        
        # Get or create the source node
        source_type = type(source_entity).__name__
        db_source_type = self.schema_adapter.map_entity_model(source_type)
        source_node = self.connector.get_entity_by_name(db_source_type, source_entity.name)
        
        if source_node is None:
            source_node = self.add_entity(source_entity)
        
        # Get or create the target node
        target_type = type(target_entity).__name__
        db_target_type = self.schema_adapter.map_entity_model(target_type)
        target_node = self.connector.get_entity_by_name(db_target_type, target_entity.name)
        
        if target_node is None:
            target_node = self.add_entity(target_entity)
        
        # Create relationship properties and map to database schema
        rel_properties = create_relationship_properties(relationship_type, **properties)
        mapped_rel_properties = self.schema_adapter.get_property_mapping(db_rel_type, rel_properties)
        
        # Create the relationship
        relationship = self.connector.create_relationship(
            source_node,
            target_node,
            db_rel_type,
            mapped_rel_properties
        )
        
        logging.info(f"Added relationship: {source_entity.name} -{db_rel_type}-> {target_entity.name}")
        return relationship
    
    def get_related_entities(
        self,
        entity: Entity,
        relationship_type: Optional[RelationshipType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all entities related to the given entity.
        
        Args:
            entity: The entity to start from
            relationship_type: Optional relationship type filter
            
        Returns:
            List of related entities with relationship information
        """
        entity_type = type(entity).__name__
        node = self.connector.get_entity_by_name(entity_type, entity.name)
        
        if node is None:
            logging.warning(f"Cannot find entity {entity.name} to get relationships")
            return []
        
        rel_type = relationship_type.value if relationship_type else None
        related = self.connector.get_connected_entities(node, rel_type)
        
        # Process results
        processed_results = []
        for result in related:
            related_node = result.get('m')
            relationship = result.get('r')
            processed_results.append({
                'entity': self._node_to_dict(related_node),
                'relationship_type': result.get('relationship'),
                'relationship_properties': dict(relationship) if relationship else {}
            })
        
        return processed_results
    
    def search_entities(
        self,
        entity_type: Optional[Type[Entity]] = None,
        **properties
    ) -> List[Dict[str, Any]]:
        """
        Search for entities by type and properties.
        
        Args:
            entity_type: Optional type of entity to search for
            **properties: Properties to filter by
            
        Returns:
            List of matching entities
        """
        # Build Cypher query
        if entity_type:
            neo4j_type = self.entity_types.get(entity_type, entity_type.__name__)
            query = f"MATCH (n:{neo4j_type})"
        else:
            query = "MATCH (n)"
        
        where_clauses = []
        params = {}
        
        for i, (key, value) in enumerate(properties.items()):
            param_name = f"param{i}"
            where_clauses.append(f"n.{key} = ${param_name}")
            params[param_name] = value
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " RETURN n"
        
        # Execute query
        results = self.connector.execute_query(query, params)
        
        # Process results
        entities = []
        for result in results:
            node = result.get('n')
            entities.append(self._node_to_dict(node))
        
        return entities
    
    def update_entity(self, entity: Entity) -> Node:
        """
        Update an entity in the knowledge graph.
        
        Args:
            entity: The entity with updated properties
            
        Returns:
            The updated node
        """
        entity_type = type(entity).__name__
        node = self.connector.get_entity_by_name(entity_type, entity.name)
        
        if node is None:
            logging.warning(f"Cannot find entity {entity.name} to update")
            return self.add_entity(entity)
        
        # Update the entity
        properties = entity.to_dict()
        updated_node = self.connector.update_entity(node, properties)
        
        logging.info(f"Updated entity: {entity.name}")
        return updated_node
    
    def delete_entity(self, entity: Entity) -> None:
        """
        Delete an entity from the knowledge graph.
        
        Args:
            entity: The entity to delete
        """
        entity_type = type(entity).__name__
        node = self.connector.get_entity_by_name(entity_type, entity.name)
        
        if node is None:
            logging.warning(f"Cannot find entity {entity.name} to delete")
            return
        
        # Delete the entity
        self.connector.delete_entity(node)
        
        logging.info(f"Deleted entity: {entity.name}")
    
    def get_character(self, name: str) -> Optional[Character]:
        """
        Get a character by name.
        
        Args:
            name: The name of the character
            
        Returns:
            The character if found, None otherwise
        """
        return self.get_entity_by_name(Character, name)
    
    def get_location(self, name: str) -> Optional[Location]:
        """
        Get a location by name.
        
        Args:
            name: The name of the location
            
        Returns:
            The location if found, None otherwise
        """
        return self.get_entity_by_name(Location, name)
    
    def get_event(self, name: str) -> Optional[Event]:
        """
        Get an event by name.
        
        Args:
            name: The name of the event
            
        Returns:
            The event if found, None otherwise
        """
        return self.get_entity_by_name(Event, name)
    
    def get_all_characters(self) -> List[Character]:
        """
        Get all characters in the knowledge graph.
        
        Returns:
            List of all characters
        """
        query = "MATCH (c:Character) RETURN c"
        results = self.connector.execute_query(query)
        
        characters = []
        for result in results:
            node = result.get('c')
            character = self._node_to_entity(node, Character)
            if character:
                characters.append(character)
        
        return characters
    
    def get_all_locations(self) -> List[Location]:
        """
        Get all locations in the knowledge graph.
        
        Returns:
            List of all locations
        """
        query = "MATCH (l:Location) RETURN l"
        results = self.connector.execute_query(query)
        
        locations = []
        for result in results:
            node = result.get('l')
            location = self._node_to_entity(node, Location)
            if location:
                locations.append(location)
        
        return locations
    
    def characters_at_location(self, location_name: str) -> List[Character]:
        """
        Get all characters at a specific location.
        
        Args:
            location_name: The name of the location
            
        Returns:
            List of characters at the location
        """
        query = f"""
        MATCH (c:Character)-[r:LOCATED_IN]->(l:Location)
        WHERE l.name = $location_name
        RETURN c
        """
        
        results = self.connector.execute_query(query, {"location_name": location_name})
        
        characters = []
        for result in results:
            node = result.get('c')
            character = self._node_to_entity(node, Character)
            if character:
                characters.append(character)
        
        return characters
    
    def _node_to_dict(self, node: Node) -> Dict[str, Any]:
        """
        Convert a Neo4j node to a dictionary.
        
        Args:
            node: The Neo4j node
            
        Returns:
            Dictionary representation of the node
        """
        node_dict = dict(node)
        node_dict['labels'] = list(node.labels)
        return node_dict
    
    def _node_to_entity(self, node: Node, entity_type: Type[T]) -> Optional[T]:
        """
        Convert a Neo4j node to an entity object.
        
        Args:
            node: The Neo4j node
            entity_type: The type of entity to create
            
        Returns:
            Entity object or None if conversion fails
        """
        try:
            # Get all properties from the node
            props = dict(node)
            
            # Get default entity properties by creating an instance with minimal data
            if hasattr(entity_type, '__annotations__'):
                required_fields = {
                    name: None for name, field_type 
                    in entity_type.__annotations__.items() 
                    if name in entity_type.__init__.__code__.co_varnames
                }
                
                # Ensure 'name' is set for the minimal entity
                if 'name' in required_fields:
                    required_fields['name'] = props.get('name', 'unnamed')
                
                # Create a minimal entity to get default values
                minimal_entity = entity_type(**required_fields)
                default_props = minimal_entity.to_dict()
                
                # Prepare a complete set of properties with defaults
                complete_props = {**default_props}
                
                # Update with values from the node, handling type conversions
                for key, value in props.items():
                    if key in default_props:
                        # Handle list fields stored as comma-separated strings
                        default_value = default_props[key]
                        if isinstance(default_value, list) and isinstance(value, str):
                            complete_props[key] = value.split(',') if value else []
                        elif isinstance(default_value, int) and isinstance(value, str):
                            try:
                                complete_props[key] = int(value)
                            except (ValueError, TypeError):
                                pass
                        else:
                            complete_props[key] = value
            else:
                # If entity_type doesn't have annotations, use properties directly
                complete_props = props
            
            # Special handling for specific entity types
            # Character
            if entity_type == Character:
                list_fields = ['traits', 'motivations']
                for field in list_fields:
                    if field in complete_props and isinstance(complete_props[field], str):
                        complete_props[field] = complete_props[field].split(',') if complete_props[field] else []
            
            # Location
            elif entity_type == Location:
                list_fields = ['resources', 'dangers']
                for field in list_fields:
                    if field in complete_props and isinstance(complete_props[field], str):
                        complete_props[field] = complete_props[field].split(',') if complete_props[field] else []
            
            # Event
            elif entity_type == Event:
                list_fields = ['participants', 'locations', 'consequences']
                for field in list_fields:
                    if field in complete_props and isinstance(complete_props[field], str):
                        complete_props[field] = complete_props[field].split(',') if complete_props[field] else []
            
            # Faction
            elif entity_type == Faction:
                list_fields = ['goals', 'values', 'enemies', 'allies']
                for field in list_fields:
                    if field in complete_props and isinstance(complete_props[field], str):
                        complete_props[field] = complete_props[field].split(',') if complete_props[field] else []
            
            # Create the entity instance
            return entity_type(**complete_props)
        
        except Exception as e:
            logging.error(f"Error converting node to entity: {e}")
            logging.error(f"Node properties: {dict(node)}")
            logging.error(f"Entity type: {entity_type}")
            return None