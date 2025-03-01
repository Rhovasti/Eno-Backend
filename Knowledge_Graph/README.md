# Knowledge Graph Component

## Overview
The Knowledge Graph component provides a structured way to store and retrieve information about entities (characters, locations, events, etc.) in the narrative gaming world. It uses Neo4j as the underlying graph database to represent entities as nodes and their relationships as edges.

## Key Features
- Entity storage and retrieval (Characters, Locations, Events, Factions, Items, Concepts)
- Relationship management with typed relationships
- Querying capabilities for connected entities
- Type-safe interface through Python's dataclasses and type hints
- Schema adapter for working with existing database structures

## Architecture
The Knowledge Graph component consists of four main parts:
1. **Entity Models**: Dataclasses representing various entity types
2. **Graph Connector**: Low-level interface to Neo4j operations
3. **Schema Adapter**: Discovers and adapts to existing database schema
4. **Knowledge Graph Manager**: High-level API for working with the knowledge graph

## Usage

### Basic Setup
```python
from Knowledge_Graph import KnowledgeGraphManager

# Initialize the manager (automatically adapts to existing schema)
graph = KnowledgeGraphManager(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="nasukili12",
    database="population"
)
```

### Working with Existing Data
The system automatically adapts to existing database schema. To explore and work with existing data:

```bash
# Discover and explore existing schema
python Knowledge_Graph/import_from_existing.py --discover

# Count nodes by label
python Knowledge_Graph/import_from_existing.py --count

# Inspect sample nodes for a specific label
python Knowledge_Graph/import_from_existing.py --inspect Character --inspect-limit 3

# Import existing nodes as entities (and optionally save to JSON)
python Knowledge_Graph/import_from_existing.py --import characters --output existing_characters.json
```

### Creating Entities
```python
from Knowledge_Graph import Character, Location

# Create a character
character = Character(
    name="Aria Silverheart",
    description="A noble elf mage",
    race="Elf",
    culture="Valain",
    occupation="Royal Mage"
)

# Add to the graph
graph.add_entity(character)

# Create a location
location = Location(
    name="Elyndoria",
    description="Ancient forest realm",
    region="Eastern Continent",
    type="Forest Kingdom"
)

# Add to the graph
graph.add_entity(location)
```

### Creating Relationships
```python
from Knowledge_Graph import RelationshipType

# Create a relationship
graph.add_relationship(
    character, location, 
    RelationshipType.LOCATED_IN,
    since="Birth", role="Citizen"
)
```

### Querying the Graph
```python
# Get a specific character
character = graph.get_character("Aria Silverheart")

# Get all locations
locations = graph.get_all_locations()

# Find related entities
relationships = graph.get_related_entities(character)

# Find characters at a location
characters = graph.characters_at_location("Elyndoria")
```

## Testing
To verify the Knowledge Graph component is working correctly, run the test script:
```bash
python test_knowledge_graph.py
```

## Connection Details
- **URI**: bolt://localhost:7687
- **Username**: neo4j
- **Password**: nasukili12
- **Database**: population