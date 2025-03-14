from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from ..db_connector import SQLDatabaseConnector
from ..models.base import EntityBase
from Vector_Database.vector_store import VectorStore, Document
from Knowledge_Graph.graph_connector import KnowledgeGraphConnector
from py2neo import Node, Relationship

# Set up logging
logging.basicConfig(
    filename='database_integrator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DatabaseIntegrator:
    """
    Utility class to integrate SQL, Vector, and Knowledge Graph databases.
    """
    
    def __init__(
        self,
        sql_connector: SQLDatabaseConnector,
        vector_store: VectorStore,
        graph_connector: KnowledgeGraphConnector
    ):
        """
        Initialize the database integrator.
        
        Args:
            sql_connector: SQL database connector
            vector_store: Vector store instance
            graph_connector: Knowledge graph connector
        """
        self.sql = sql_connector
        self.vector = vector_store
        self.graph = graph_connector
        logging.info("DatabaseIntegrator initialized")
    
    def entity_to_vector_document(self, entity: EntityBase) -> Document:
        """
        Convert an entity to a vector document.
        
        Args:
            entity: Entity to convert
            
        Returns:
            Vector document
        """
        # Convert entity to dictionary
        entity_dict = entity.to_dict()
        
        # Create document text from entity attributes
        text_parts = [
            f"# {entity_dict['name']}",
            f"Type: {entity_dict['specific_type']}",
            f"Domain: {entity_dict.get('domain', 'Unknown')}",
        ]
        
        # Add description if available
        if entity_dict.get('description'):
            text_parts.append(f"Description: {entity_dict['description']}")
        
        # Add other important attributes
        for key, value in entity_dict.items():
            if value and key not in ['id', 'name', 'type', 'specific_type', 'domain', 'description', 'created_at', 'updated_at', 'uid']:
                text_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        # Join all parts into a single text
        text = "\n\n".join(text_parts)
        
        # Create document
        document = Document(
            text=text,
            metadata={
                "entity_type": entity_dict['specific_type'],
                "entity_id": entity_dict['id'],
                "entity_uid": entity_dict['uid'],
                "name": entity_dict['name'],
                "domain": entity_dict.get('domain'),
                "subdomain": entity_dict.get('subdomain')
            }
        )
        
        return document
    
    def entity_to_graph_node(self, entity: EntityBase) -> Node:
        """
        Convert an entity to a graph node.
        
        Args:
            entity: Entity to convert
            
        Returns:
            Graph node
        """
        # Convert entity to dictionary
        entity_dict = entity.to_dict()
        
        # Create properties for the node
        properties = {
            "sql_id": entity_dict['id'],
            "uid": entity_dict['uid'],
            "name": entity_dict['name'],
            "domain": entity_dict.get('domain'),
            "subdomain": entity_dict.get('subdomain')
        }
        
        # Create the node
        node = self.graph.create_entity(entity_dict['specific_type'], properties)
        
        return node
    
    def sync_entity_to_all_databases(self, entity: EntityBase) -> Tuple[EntityBase, Document, Node]:
        """
        Sync an entity to all databases.
        
        Args:
            entity: Entity to sync
            
        Returns:
            Tuple of (SQL entity, Vector document, Graph node)
        """
        try:
            # First ensure the entity is in the SQL database
            if not entity.id:
                entity = self.sql.add_entity(entity)
            
            # Convert to vector document and store
            document = self.entity_to_vector_document(entity)
            self.vector.add_document(document)
            
            # Convert to graph node and store
            node = self.entity_to_graph_node(entity)
            
            logging.info(f"Synced {entity.__class__.__name__} '{entity.name}' to all databases")
            return (entity, document, node)
        
        except Exception as e:
            logging.error(f"Error syncing entity to all databases: {e}")
            raise
    
    def create_relationship_between_entities(
        self, 
        source_entity: EntityBase, 
        target_entity: EntityBase, 
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Relationship:
        """
        Create a relationship between two entities in the knowledge graph.
        
        Args:
            source_entity: Source entity
            target_entity: Target entity
            relationship_type: Type of relationship
            properties: Optional properties for the relationship
            
        Returns:
            Created relationship
        """
        try:
            # Ensure both entities are in the SQL database
            if not source_entity.id:
                source_entity = self.sql.add_entity(source_entity)
            if not target_entity.id:
                target_entity = self.sql.add_entity(target_entity)
            
            # Get or create nodes for both entities
            source_node = self.graph.get_entity_by_name(
                source_entity.specific_type, 
                source_entity.name
            )
            
            if not source_node:
                source_node = self.entity_to_graph_node(source_entity)
            
            target_node = self.graph.get_entity_by_name(
                target_entity.specific_type, 
                target_entity.name
            )
            
            if not target_node:
                target_node = self.entity_to_graph_node(target_entity)
            
            # Create the relationship
            relationship = self.graph.create_relationship(
                source_node, 
                target_node, 
                relationship_type, 
                properties
            )
            
            logging.info(f"Created relationship: {source_entity.name} -{relationship_type}-> {target_entity.name}")
            return relationship
        
        except Exception as e:
            logging.error(f"Error creating relationship between entities: {e}")
            raise
    
    def find_entity_across_databases(
        self, 
        entity_type: str, 
        query: str, 
        search_vector: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find entities across all databases.
        
        Args:
            entity_type: Type of entity to search for (e.g., "Character", "Location")
            query: Query string to search for
            search_vector: Whether to search in the vector database as well
            
        Returns:
            List of matching entities with database sources
        """
        results = []
        
        try:
            # Get corresponding model class
            model_class = None
            if entity_type == "Character":
                from ..models.character import Character
                model_class = Character
            elif entity_type == "Event":
                from ..models.event import Event
                model_class = Event
            elif entity_type == "Location":
                from ..models.location import Location
                model_class = Location
            elif entity_type == "Act":
                from ..models.act import Act
                model_class = Act
            elif entity_type == "Concept":
                from ..models.concept import Concept
                model_class = Concept
            
            # Search in SQL database
            if model_class:
                sql_results = self.sql.search_entities(model_class, query)
                for entity in sql_results:
                    results.append({
                        "source": "sql",
                        "entity_type": entity_type,
                        "entity": entity.to_dict(),
                        "score": 1.0  # No scoring in SQL search
                    })
            
            # Search in knowledge graph
            graph_query = f"""
            MATCH (n:{entity_type})
            WHERE n.name CONTAINS $query
            RETURN n
            """
            graph_results = self.graph.execute_query(graph_query, {"query": query})
            for result in graph_results:
                node = result['n']
                results.append({
                    "source": "graph",
                    "entity_type": entity_type,
                    "entity": dict(node),
                    "score": 1.0  # No scoring in graph search
                })
            
            # Search in vector database
            if search_vector:
                vector_results = self.vector.search(
                    query=query,
                    n_results=10,
                    filter_metadata={"entity_type": entity_type}
                )
                
                for doc in vector_results:
                    # Check if already in results
                    existing = next(
                        (r for r in results if r.get("entity", {}).get("uid") == doc.metadata.get("entity_uid")),
                        None
                    )
                    
                    if not existing:
                        # Get full entity from SQL if possible
                        entity = None
                        if model_class and doc.metadata.get("entity_id"):
                            entity = self.sql.get_entity_by_id(model_class, doc.metadata.get("entity_id"))
                        
                        results.append({
                            "source": "vector",
                            "entity_type": entity_type,
                            "entity": entity.to_dict() if entity else doc.metadata,
                            "vector_text": doc.text,
                            "score": 0.8  # Approximate relevance score
                        })
            
            logging.info(f"Found {len(results)} entities across databases for query '{query}'")
            return results
        
        except Exception as e:
            logging.error(f"Error finding entity across databases: {e}")
            raise
    
    def delete_entity_from_all_databases(self, entity: EntityBase) -> bool:
        """
        Delete an entity from all databases.
        
        Args:
            entity: Entity to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from SQL database
            sql_success = self.sql.delete_entity(entity)
            
            # Delete from vector database
            vector_filter = {
                "entity_type": entity.specific_type,
                "entity_uid": entity.uid
            }
            vector_docs = self.vector.search_by_metadata(vector_filter)
            for doc in vector_docs:
                self.vector.delete_document(doc.id)
            
            # Delete from knowledge graph
            graph_node = self.graph.get_entity_by_name(entity.specific_type, entity.name)
            if graph_node:
                self.graph.delete_entity(graph_node)
            
            logging.info(f"Deleted {entity.__class__.__name__} '{entity.name}' from all databases")
            return sql_success
        
        except Exception as e:
            logging.error(f"Error deleting entity from all databases: {e}")
            return False