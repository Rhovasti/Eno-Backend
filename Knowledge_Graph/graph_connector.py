import logging
from typing import Dict, List, Optional, Union, Any
from py2neo import Graph, Node, Relationship, NodeMatcher
import os
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='knowledge_graph.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KnowledgeGraphConnector:
    """
    Connector class for the Neo4j knowledge graph.
    Handles connections, querying, and mutations.
    """
    
    def __init__(
        self, 
        uri: str = "bolt://localhost:7687", 
        username: str = "neo4j", 
        password: str = "nasukili12",
        database: str = "population"
    ):
        """
        Initialize connection to Neo4j database.
        
        Args:
            uri: The Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
            database: Name of the Neo4j database
        """
        try:
            self.graph = Graph(uri, auth=(username, password), name=database)
            self.matcher = NodeMatcher(self.graph)
            logging.info("Successfully connected to Neo4j knowledge graph")
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def create_entity(self, entity_type: str, properties: Dict[str, Any]) -> Node:
        """
        Create a new entity node in the knowledge graph.
        
        Args:
            entity_type: Type of entity (Character, Location, Event, etc.)
            properties: Dictionary of entity properties
            
        Returns:
            The created node
        """
        try:
            # Add metadata
            properties['created_at'] = datetime.now().isoformat()
            properties['updated_at'] = datetime.now().isoformat()
            
            # Create the node
            node = Node(entity_type, **properties)
            self.graph.create(node)
            
            logging.info(f"Created {entity_type} node: {properties.get('name', 'unnamed')}")
            return node
        except Exception as e:
            logging.error(f"Error creating entity: {e}")
            raise
    
    def create_relationship(
        self, 
        source_node: Node, 
        target_node: Node, 
        relationship_type: str, 
        properties: Optional[Dict[str, Any]] = None
    ) -> Relationship:
        """
        Create a relationship between two nodes.
        
        Args:
            source_node: Source node
            target_node: Target node
            relationship_type: Type of relationship (e.g., KNOWS, LOCATED_IN)
            properties: Optional properties for the relationship
            
        Returns:
            The created relationship
        """
        try:
            if properties is None:
                properties = {}
            
            # Add metadata
            properties['created_at'] = datetime.now().isoformat()
            
            # Create the relationship
            relationship = Relationship(source_node, relationship_type, target_node, **properties)
            self.graph.create(relationship)
            
            source_name = source_node.get('name', 'unnamed')
            target_name = target_node.get('name', 'unnamed')
            logging.info(f"Created relationship: {source_name} -{relationship_type}-> {target_name}")
            
            return relationship
        except Exception as e:
            logging.error(f"Error creating relationship: {e}")
            raise
    
    def get_entity_by_name(self, entity_type: str, name: str) -> Optional[Node]:
        """
        Find an entity by its type and name.
        
        Args:
            entity_type: Type of entity to search for
            name: Name of the entity
            
        Returns:
            The node if found, None otherwise
        """
        try:
            node = self.matcher.match(entity_type, name=name).first()
            return node
        except Exception as e:
            logging.error(f"Error getting entity by name: {e}")
            raise
    
    def get_entity_by_id(self, entity_id: int) -> Optional[Node]:
        """
        Find an entity by its internal Neo4j ID.
        
        Args:
            entity_id: Neo4j internal ID
            
        Returns:
            The node if found, None otherwise
        """
        try:
            query = f"MATCH (n) WHERE ID(n) = {entity_id} RETURN n"
            result = self.graph.run(query).data()
            return result[0]['n'] if result else None
        except Exception as e:
            logging.error(f"Error getting entity by ID: {e}")
            raise
    
    def update_entity(self, node: Node, properties: Dict[str, Any]) -> Node:
        """
        Update an entity with new properties.
        
        Args:
            node: The node to update
            properties: Properties to update or add
            
        Returns:
            The updated node
        """
        try:
            # Update metadata
            properties['updated_at'] = datetime.now().isoformat()
            
            # Update properties
            for key, value in properties.items():
                node[key] = value
            
            # Push changes to database
            self.graph.push(node)
            
            logging.info(f"Updated node: {node.get('name', 'unnamed')}")
            return node
        except Exception as e:
            logging.error(f"Error updating entity: {e}")
            raise
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Optional parameters for the query
            
        Returns:
            List of results
        """
        try:
            if parameters is None:
                parameters = {}
                
            result = self.graph.run(query, parameters=parameters)
            return result.data()
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            raise
    
    def get_connected_entities(self, node: Node, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all entities connected to a node.
        
        Args:
            node: The node to start from
            relationship_type: Optional type of relationship to filter by
            
        Returns:
            List of connected nodes with relationship information
        """
        try:
            node_id = self.graph.resolve_node_id(node)
            
            if relationship_type:
                query = """
                MATCH (n)-[r:%s]-(m)
                WHERE ID(n) = $node_id
                RETURN type(r) as relationship, m, r
                """ % relationship_type
            else:
                query = """
                MATCH (n)-[r]-(m)
                WHERE ID(n) = $node_id
                RETURN type(r) as relationship, m, r
                """
                
            result = self.graph.run(query, node_id=node_id).data()
            return result
        except Exception as e:
            logging.error(f"Error getting connected entities: {e}")
            raise
    
    def delete_entity(self, node: Node) -> None:
        """
        Delete an entity and its relationships.
        
        Args:
            node: The node to delete
        """
        try:
            # First detach all relationships
            query = """
            MATCH (n)
            WHERE ID(n) = $node_id
            DETACH DELETE n
            """
            
            node_id = self.graph.resolve_node_id(node)
            self.graph.run(query, node_id=node_id)
            
            logging.info(f"Deleted node: {node.get('name', 'unnamed')}")
        except Exception as e:
            logging.error(f"Error deleting entity: {e}")
            raise