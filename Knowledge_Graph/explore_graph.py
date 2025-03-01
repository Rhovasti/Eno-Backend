#!/usr/bin/env python3
"""
Script to explore the existing data in the Neo4j database.
This will help us understand the current schema and data model.
"""

import logging
import sys
import os

# Add parent directory to Python path to make modules importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Knowledge_Graph.graph_connector import KnowledgeGraphConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    # Initialize connector
    print("Connecting to Neo4j database...")
    connector = KnowledgeGraphConnector(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="nasukili12",
        database="population"
    )
    
    # Get node labels (types of entities)
    print("\nExploring node labels (entity types)...")
    query = "CALL db.labels()"
    labels = connector.execute_query(query)
    print("Node labels found:")
    for label in labels:
        print(f"- {label['label']}")
    
    # Get relationship types
    print("\nExploring relationship types...")
    query = "CALL db.relationshipTypes()"
    rel_types = connector.execute_query(query)
    print("Relationship types found:")
    for rel_type in rel_types:
        print(f"- {rel_type['relationshipType']}")
    
    # Get property keys
    print("\nExploring property keys...")
    query = "CALL db.propertyKeys()"
    prop_keys = connector.execute_query(query)
    print("Property keys found:")
    for prop_key in prop_keys:
        print(f"- {prop_key['propertyKey']}")
    
    # Count nodes by label
    print("\nCounting nodes by label...")
    for label in [item['label'] for item in labels]:
        query = f"MATCH (n:{label}) RETURN count(n) as count"
        count = connector.execute_query(query)[0]['count']
        print(f"- {label}: {count} nodes")
    
    # Sample nodes for each label
    print("\nSampling nodes for each label...")
    for label in [item['label'] for item in labels]:
        query = f"MATCH (n:{label}) RETURN n LIMIT 3"
        sample_nodes = connector.execute_query(query)
        if sample_nodes:
            print(f"\n{label} sample nodes:")
            for i, result in enumerate(sample_nodes, 1):
                node = result['n']
                node_props = dict(node)
                print(f"  Node {i}:")
                for key, value in node_props.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"    {key}: {value}")
    
    # Sample relationships
    print("\nSampling relationships...")
    for rel_type in [item['relationshipType'] for item in rel_types]:
        query = f"MATCH ()-[r:{rel_type}]->() RETURN r, startNode(r) as source, endNode(r) as target LIMIT 3"
        sample_rels = connector.execute_query(query)
        if sample_rels:
            print(f"\n{rel_type} sample relationships:")
            for i, result in enumerate(sample_rels, 1):
                rel = result['r']
                source = result['source']
                target = result['target']
                rel_props = dict(rel)
                print(f"  Relationship {i}:")
                print(f"    Source: {dict(source).get('name', 'unnamed')} ({', '.join(source.labels)})")
                print(f"    Target: {dict(target).get('name', 'unnamed')} ({', '.join(target.labels)})")
                if rel_props:
                    print("    Properties:")
                    for key, value in rel_props.items():
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"      {key}: {value}")

if __name__ == "__main__":
    main()