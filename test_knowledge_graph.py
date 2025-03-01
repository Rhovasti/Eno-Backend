#!/usr/bin/env python3
"""
Test script for the Knowledge Graph implementation.
Creates some sample entities and relationships to verify the implementation works.
This script is designed to work with both new and existing database structures.
"""

import logging
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Knowledge_Graph import (
    KnowledgeGraphManager,
    Character, Location, Event, Faction,
    RelationshipType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    # Initialize knowledge graph manager
    print("Initializing knowledge graph manager...")
    graph = KnowledgeGraphManager(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="nasukili12",
        database="population"
    )
    
    # Create sample characters
    print("\nCreating sample characters...")
    character1 = Character(
        name="Aria Silverheart",
        description="A noble elf mage from the ancient forests of Elyndoria",
        race="Elf",
        culture="Valain",
        occupation="Royal Mage",
        age=342,
        gender="Female",
        traits=["Intelligent", "Proud", "Diplomatic"],
        appearance="Tall with silver hair and piercing blue eyes",
        motivations=["Preserve elven traditions", "Expand magical knowledge"]
    )
    
    character2 = Character(
        name="Thorne Ironhammer",
        description="A gruff dwarf warrior known for his smithing skills",
        race="Dwarf",
        culture="Oonar",
        occupation="Blacksmith",
        age=127,
        gender="Male",
        traits=["Strong", "Stubborn", "Loyal"],
        appearance="Stocky with a long red beard and burn scars on his arms",
        motivations=["Craft legendary weapons", "Restore his clan's honor"]
    )
    
    # Add characters to graph
    graph.add_entity(character1)
    graph.add_entity(character2)
    
    # Create sample locations
    print("\nCreating sample locations...")
    location1 = Location(
        name="Elyndoria",
        description="Ancient forest realm of the high elves",
        region="Eastern Continent",
        type="Forest Kingdom",
        climate="Temperate",
        population=25000,
        resources=["Ancient Trees", "Crystal Springs", "Magical Herbs"],
        dangers=["Wild Beasts", "Forest Spirits"],
        culture="Valain"
    )
    
    location2 = Location(
        name="Ironforge",
        description="Mountain stronghold of the Ironhammer clan",
        region="Northern Mountains",
        type="Dwarven Stronghold",
        climate="Cold",
        population=5000,
        resources=["Iron", "Mithril", "Gems"],
        dangers=["Cave Collapses", "Mountain Trolls"],
        culture="Oonar"
    )
    
    # Add locations to graph
    graph.add_entity(location1)
    graph.add_entity(location2)
    
    # Create sample events
    print("\nCreating sample events...")
    event1 = Event(
        name="The Great Alliance",
        description="A historic treaty between elves and dwarves",
        event_type="Treaty",
        date="Year 573 of the Third Age",
        participants=["Aria Silverheart", "Thorne Ironhammer", "King Elodin", "High Thane Durin"],
        locations=["Elyndoria", "Neutral Grounds"],
        consequences=["Trade routes established", "Cultural exchange", "Mutual defense"],
        importance=8
    )
    
    # Add events to graph
    graph.add_entity(event1)
    
    # Create sample factions
    print("\nCreating sample factions...")
    faction1 = Faction(
        name="Council of Arcana",
        description="Elite organization of the most powerful mages",
        faction_type="Magical Order",
        leader="Archmage Elindra",
        headquarters="Tower of High Sorcery",
        goals=["Preserve magical knowledge", "Regulate dangerous magic"],
        values=["Knowledge", "Responsibility", "Balance"],
        enemies=["Cult of the Dark Flame"],
        allies=["Royal Court of Elyndoria"]
    )
    
    # Add factions to graph
    graph.add_entity(faction1)
    
    # Create relationships
    print("\nCreating relationships...")
    # Character lives in location
    graph.add_relationship(
        character1, location1, 
        RelationshipType.LOCATED_IN,
        since="Birth", role="Citizen"
    )
    
    graph.add_relationship(
        character2, location2, 
        RelationshipType.LOCATED_IN,
        since="Year 450", role="Guild Master"
    )
    
    # Characters know each other
    graph.add_relationship(
        character1, character2, 
        RelationshipType.KNOWS,
        relationship="Allies", trust_level=7
    )
    
    # Character is member of faction
    graph.add_relationship(
        character1, faction1, 
        RelationshipType.MEMBER_OF,
        role="Senior Councilor", joined_date="Year 650"
    )
    
    # Character participated in event
    graph.add_relationship(
        character1, event1, 
        RelationshipType.PARTICIPATED_IN,
        role="Ambassador", outcome="Success"
    )
    
    graph.add_relationship(
        character2, event1, 
        RelationshipType.PARTICIPATED_IN,
        role="Clan Representative", outcome="Success"
    )
    
    # Query the graph
    print("\nQuerying the graph...")
    print("\nAll characters:")
    characters = graph.get_all_characters()
    for character in characters:
        print(f"- {character.name} ({character.race}, {character.occupation})")
    
    print("\nAll locations:")
    locations = graph.get_all_locations()
    for location in locations:
        print(f"- {location.name} ({location.type}, population: {location.population})")
    
    print("\nRelationships for Aria Silverheart:")
    aria = graph.get_character("Aria Silverheart")
    if aria:
        relationships = graph.get_related_entities(aria)
        for rel in relationships:
            entity = rel['entity']
            rel_type = rel['relationship_type']
            print(f"- {rel_type} -> {entity.get('name')} ({', '.join(entity.get('labels', []))})")
    
    print("\nCharacters at Elyndoria:")
    characters = graph.characters_at_location("Elyndoria")
    for character in characters:
        print(f"- {character.name} ({character.occupation})")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()