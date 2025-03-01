import logging
from typing import Dict, List, Optional, Any, Set, Tuple
import os
import json
from datetime import datetime

class SchemaAdapter:
    """
    Class that adapts to an existing Neo4j schema.
    It can discover the existing labels, relationship types, and properties,
    and provide an interface for mapping between our code's models and the
    existing database schema.
    """
    
    def __init__(self, connector=None):
        """
        Initialize the schema adapter.
        
        Args:
            connector: An optional connector to use for schema discovery
        """
        self.connector = connector
        self.node_labels = set()
        self.relationship_types = set()
        self.property_keys = set()
        self.label_properties = {}
        self.relationship_properties = {}
        
        # File path for cached schema
        self.schema_cache_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "schema_cache.json"
        )
        
        # Use cached schema if connector is not provided
        if not connector and os.path.exists(self.schema_cache_file):
            self._load_schema_from_cache()
        elif connector:
            try:
                self.discover_schema()
            except Exception as e:
                logging.error(f"Error discovering schema: {e}")
                if os.path.exists(self.schema_cache_file):
                    logging.info("Loading schema from cache due to discovery error")
                    self._load_schema_from_cache()
    
    def discover_schema(self) -> None:
        """
        Discover the schema from the Neo4j database.
        """
        if not self.connector:
            logging.warning("No connector provided for schema discovery")
            return
        
        try:
            # Get node labels
            labels_query = "CALL db.labels()"
            labels_result = self.connector.execute_query(labels_query)
            self.node_labels = {record['label'] for record in labels_result}
            
            # Get relationship types
            rel_types_query = "CALL db.relationshipTypes()"
            rel_types_result = self.connector.execute_query(rel_types_query)
            self.relationship_types = {record['relationshipType'] for record in rel_types_result}
            
            # Get property keys
            prop_keys_query = "CALL db.propertyKeys()"
            prop_keys_result = self.connector.execute_query(prop_keys_query)
            self.property_keys = {record['propertyKey'] for record in prop_keys_result}
            
            # Get properties for each node label
            for label in self.node_labels:
                # Sample a few nodes to get common properties
                query = f"""
                MATCH (n:{label})
                RETURN n LIMIT 10
                """
                sample_nodes = self.connector.execute_query(query)
                
                # Collect all properties from the sample nodes
                properties = set()
                for record in sample_nodes:
                    node = record['n']
                    properties.update(dict(node).keys())
                
                self.label_properties[label] = list(properties)
            
            # Get properties for each relationship type
            for rel_type in self.relationship_types:
                # Sample a few relationships to get common properties
                query = f"""
                MATCH ()-[r:{rel_type}]->()
                RETURN r LIMIT 10
                """
                sample_rels = self.connector.execute_query(query)
                
                # Collect all properties from the sample relationships
                properties = set()
                for record in sample_rels:
                    rel = record['r']
                    properties.update(dict(rel).keys())
                
                self.relationship_properties[rel_type] = list(properties)
            
            # Cache the discovered schema
            self._save_schema_to_cache()
            
            logging.info(f"Discovered schema: {len(self.node_labels)} labels, {len(self.relationship_types)} relationship types")
        
        except Exception as e:
            logging.error(f"Error during schema discovery: {e}")
            raise
    
    def _save_schema_to_cache(self) -> None:
        """
        Save the discovered schema to a cache file.
        """
        schema_data = {
            "timestamp": datetime.now().isoformat(),
            "node_labels": list(self.node_labels),
            "relationship_types": list(self.relationship_types),
            "property_keys": list(self.property_keys),
            "label_properties": self.label_properties,
            "relationship_properties": self.relationship_properties
        }
        
        try:
            with open(self.schema_cache_file, 'w') as f:
                json.dump(schema_data, f, indent=2)
            logging.info(f"Schema saved to cache: {self.schema_cache_file}")
        except Exception as e:
            logging.error(f"Error saving schema to cache: {e}")
    
    def _load_schema_from_cache(self) -> None:
        """
        Load the schema from the cache file.
        """
        try:
            with open(self.schema_cache_file, 'r') as f:
                schema_data = json.load(f)
            
            self.node_labels = set(schema_data.get("node_labels", []))
            self.relationship_types = set(schema_data.get("relationship_types", []))
            self.property_keys = set(schema_data.get("property_keys", []))
            self.label_properties = schema_data.get("label_properties", {})
            self.relationship_properties = schema_data.get("relationship_properties", {})
            
            logging.info(f"Loaded schema from cache: {len(self.node_labels)} labels, {len(self.relationship_types)} relationship types")
        except Exception as e:
            logging.error(f"Error loading schema from cache: {e}")
    
    def get_entity_labels(self) -> List[str]:
        """
        Get all entity labels (node types) from the schema.
        
        Returns:
            List of entity labels
        """
        return list(self.node_labels)
    
    def get_relationship_types(self) -> List[str]:
        """
        Get all relationship types from the schema.
        
        Returns:
            List of relationship types
        """
        return list(self.relationship_types)
    
    def get_entity_properties(self, label: str) -> List[str]:
        """
        Get all properties for a specific entity label.
        
        Args:
            label: The entity label
            
        Returns:
            List of property names
        """
        return self.label_properties.get(label, [])
    
    def get_relationship_properties(self, rel_type: str) -> List[str]:
        """
        Get all properties for a specific relationship type.
        
        Args:
            rel_type: The relationship type
            
        Returns:
            List of property names
        """
        return self.relationship_properties.get(rel_type, [])
    
    def map_entity_model(self, model_name: str) -> Optional[str]:
        """
        Map a model name to a database label.
        
        Args:
            model_name: Name of the model class
            
        Returns:
            Corresponding database label or None if not found
        """
        # Try exact match
        if model_name in self.node_labels:
            return model_name
        
        # Try case-insensitive match
        for label in self.node_labels:
            if label.lower() == model_name.lower():
                return label
        
        # If no match is found, return the model name to allow creation
        return model_name
    
    def map_relationship_type(self, rel_type: str) -> Optional[str]:
        """
        Map a relationship type to a database relationship type.
        
        Args:
            rel_type: Relationship type name
            
        Returns:
            Corresponding database relationship type or None if not found
        """
        # Try exact match
        if rel_type in self.relationship_types:
            return rel_type
        
        # Try case-insensitive match
        for db_rel_type in self.relationship_types:
            if db_rel_type.lower() == rel_type.lower():
                return db_rel_type
        
        # If no match is found, return the provided type to allow creation
        return rel_type
    
    def get_property_mapping(self, entity_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map property names from our model to the database schema.
        
        Args:
            entity_type: Type of entity or relationship
            properties: Dictionary of properties to map
            
        Returns:
            Mapped properties dictionary
        """
        # If entity_type is not in our known schema, return properties as-is
        if entity_type not in self.label_properties and entity_type not in self.relationship_properties:
            return properties
        
        # Get known properties for this type
        known_props = self.label_properties.get(entity_type, []) or self.relationship_properties.get(entity_type, [])
        
        mapped_props = {}
        for key, value in properties.items():
            # Try exact match
            if key in known_props:
                mapped_props[key] = value
                continue
            
            # Try case-insensitive match
            matched = False
            for prop in known_props:
                if prop.lower() == key.lower():
                    mapped_props[prop] = value
                    matched = True
                    break
            
            # If no match found, use the original key
            if not matched:
                mapped_props[key] = value
        
        return mapped_props