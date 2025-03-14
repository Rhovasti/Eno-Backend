# SQL Database for Structured Game Data

This component provides a relational database interface for storing structured game data like character sheets, locations, events, acts, and concepts. It uses SQLAlchemy ORM for database operations.

## Features

- SQL database connection using SQLAlchemy
- Models for Character, Event, Location, Act, and Concept entities
- CRUD operations for all entity types
- Integration with Knowledge Graph and Vector Database components

## Usage

```python
from SQLdatabase.db_connector import SQLDatabaseConnector
from SQLdatabase.models.character import Character

# Initialize the connector
db = SQLDatabaseConnector()

# Create a character
character = Character(
    name="Alia Vorn",
    type="Player",
    domain="Aumian",
    subdomain="Artificer",
    imperative="Discover",
    ethos="Balance"
)

# Save to database
db.add_entity(character)

# Query characters
characters = db.query_entities(Character, {"domain": "Aumian"})
```
