#!/usr/bin/env python3
"""
Script to examine and import entities from existing Neo4j database.
This will allow us to work with the existing data structure.
"""

import logging
import sys
import os
import json
import argparse

# Add parent directory to Python path to make modules importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Knowledge_Graph.graph_connector import KnowledgeGraphConnector
from Knowledge_Graph.schema_adapter import SchemaAdapter
from Knowledge_Graph.knowledge_manager import KnowledgeGraphManager
from Knowledge_Graph.models.entity_models import Character, Location, Event, Faction

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def discover_schema(connector):
    """Discover and print the database schema."""
    adapter = SchemaAdapter(connector)
    adapter.discover_schema()
    
    print("\n=== Database Schema ===")
    print(f"\nNode Labels: {', '.join(adapter.node_labels)}")
    print(f"\nRelationship Types: {', '.join(adapter.relationship_types)}")
    print(f"\nProperty Keys: {', '.join(sorted(adapter.property_keys))}")
    
    print("\n=== Node Label Properties ===")
    for label, props in adapter.label_properties.items():
        print(f"\n{label} Properties: {', '.join(sorted(props))}")
    
    print("\n=== Relationship Type Properties ===")
    for rel_type, props in adapter.relationship_properties.items():
        print(f"\n{rel_type} Properties: {', '.join(sorted(props))}")
    
    return adapter

def count_nodes_by_label(connector):
    """Count and print the number of nodes for each label."""
    query = """
    CALL db.labels() YIELD label
    CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value
    RETURN label, value.count as count
    ORDER BY label
    """
    
    try:
        results = connector.execute_query(query)
        
        print("\n=== Node Counts by Label ===")
        for result in results:
            print(f"{result['label']}: {result['count']} nodes")
    except Exception as e:
        print(f"Error counting nodes: {e}")
        # Fallback to simpler approach
        query = "CALL db.labels()"
        labels = connector.execute_query(query)
        
        for label_info in labels:
            label = label_info['label']
            count_query = f"MATCH (n:{label}) RETURN count(n) as count"
            count = connector.execute_query(count_query)[0]['count']
            print(f"{label}: {count} nodes")

def inspect_sample_nodes(connector, label, limit=5):
    """Inspect sample nodes for a specific label."""
    query = f"""
    MATCH (n:{label})
    RETURN n
    LIMIT {limit}
    """
    
    sample_nodes = connector.execute_query(query)
    if not sample_nodes:
        print(f"No nodes found with label: {label}")
        return
    
    print(f"\n=== Sample {label} Nodes ===")
    for i, result in enumerate(sample_nodes, 1):
        node = result['n']
        node_props = dict(node)
        print(f"\nNode {i}:")
        for key, value in sorted(node_props.items()):
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"  {key}: {value}")

def import_nodes_as_entities(graph_manager, label, entity_class, limit=None):
    """Import nodes as entity objects."""
    # Map the label to the appropriate database label
    db_label = graph_manager.schema_adapter.map_entity_model(label)
    
    # Query to get nodes
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
    MATCH (n:{db_label})
    RETURN n
    {limit_clause}
    """
    
    nodes = graph_manager.connector.execute_query(query)
    if not nodes:
        print(f"No nodes found with label: {db_label}")
        return []
    
    print(f"\nImporting {len(nodes)} {db_label} nodes as {entity_class.__name__} entities...")
    
    entities = []
    for result in nodes:
        node = result['n']
        entity = graph_manager._node_to_entity(node, entity_class)
        if entity:
            entities.append(entity)
    
    print(f"Successfully imported {len(entities)} entities")
    return entities

def main():
    parser = argparse.ArgumentParser(description="Examine and import entities from Neo4j database")
    parser.add_argument("--discover", action="store_true", help="Discover and print database schema")
    parser.add_argument("--count", action="store_true", help="Count nodes by label")
    parser.add_argument("--inspect", type=str, help="Inspect sample nodes for a specific label")
    parser.add_argument("--inspect-limit", type=int, default=5, help="Number of sample nodes to inspect")
    parser.add_argument("--import", type=str, choices=["characters", "locations", "events", "factions"], 
                        help="Import nodes as entities")
    parser.add_argument("--import-limit", type=int, help="Limit the number of nodes to import")
    parser.add_argument("--output", type=str, help="Output file for imported entities (JSON format)")
    
    args = parser.parse_args()
    
    # Initialize connector
    print("Connecting to Neo4j database...")
    try:
        connector = KnowledgeGraphConnector(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="nasukili12",
            database="population"
        )
        print("Successfully connected to Neo4j database")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return 1
    
    # Discover schema
    if args.discover:
        try:
            adapter = discover_schema(connector)
        except Exception as e:
            print(f"Error discovering schema: {e}")
            return 1
    
    # Count nodes by label
    if args.count:
        try:
            count_nodes_by_label(connector)
        except Exception as e:
            print(f"Error counting nodes: {e}")
            return 1
    
    # Inspect sample nodes
    if args.inspect:
        try:
            inspect_sample_nodes(connector, args.inspect, args.inspect_limit)
        except Exception as e:
            print(f"Error inspecting nodes: {e}")
            return 1
    
    # Import nodes as entities
    if args.import:
        try:
            # Initialize the knowledge graph manager
            graph_manager = KnowledgeGraphManager(
                uri="bolt://localhost:7687",
                username="neo4j",
                password="nasukili12",
                database="population"
            )
            
            # Import entities based on type
            if args.import == "characters":
                entities = import_nodes_as_entities(graph_manager, "Character", Character, args.import_limit)
                entity_type = "characters"
            elif args.import == "locations":
                entities = import_nodes_as_entities(graph_manager, "Location", Location, args.import_limit)
                entity_type = "locations"
            elif args.import == "events":
                entities = import_nodes_as_entities(graph_manager, "Event", Event, args.import_limit)
                entity_type = "events"
            elif args.import == "factions":
                entities = import_nodes_as_entities(graph_manager, "Faction", Faction, args.import_limit)
                entity_type = "factions"
            
            # Save to output file if specified
            if args.output and entities:
                # Convert entities to dictionaries
                entity_dicts = [entity.to_dict() for entity in entities]
                
                # Save to JSON file
                with open(args.output, 'w') as f:
                    json.dump({entity_type: entity_dicts}, f, indent=2)
                
                print(f"Saved {len(entities)} {entity_type} to {args.output}")
        
        except Exception as e:
            print(f"Error importing entities: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())