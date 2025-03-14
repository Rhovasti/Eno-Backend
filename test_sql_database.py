import unittest
import os
import json
import logging
from SQLdatabase.db_connector import SQLDatabaseConnector
from SQLdatabase.models.character import Character
from SQLdatabase.models.location import Location
from SQLdatabase.models.event import Event

class TestSQLDatabase(unittest.TestCase):
    """
    Test cases for SQL database functionality.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Use in-memory SQLite database for testing
        cls.db = SQLDatabaseConnector("sqlite:///:memory:")
        
        # Create test data
        cls.test_character = Character(
            name="Test Character",
            type="Player",
            domain="Aumian",
            subdomain="Warrior",
            imperative="Explore",
            ethos="Balance",
            birth_cycle="Dawn",
            reproductive_type="Humanoid",
            culture="Citadel",
            traits="Brave, Strong",
            demeanor="Stoic"
        )
        
        cls.test_location = Location(
            name="Test City",
            type="Citystate",
            domain="Dawn Valley",
            latitude=45.5,
            longitude=30.2,
            altitude=100.0,
            location_type="Citystate",
            valley="Dawn"
        )
        
        cls.test_event = Event(
            name="Great Battle",
            type="Historical",
            domain="War",
            subdomain="Conflict",
            cycle="Third Era"
        )
    
    def setUp(self):
        """Reset database before each test."""
        # Clear all tables
        for table in self.db.engine.table_names():
            self.db.engine.execute(f"DELETE FROM {table}")
    
    def test_add_entity(self):
        """Test adding entities to the database."""
        # Add test character
        character = self.db.add_entity(self.test_character)
        self.assertIsNotNone(character.id)
        self.assertEqual(character.name, "Test Character")
        
        # Add test location
        location = self.db.add_entity(self.test_location)
        self.assertIsNotNone(location.id)
        self.assertEqual(location.name, "Test City")
        
        # Add test event
        event = self.db.add_entity(self.test_event)
        self.assertIsNotNone(event.id)
        self.assertEqual(event.name, "Great Battle")
    
    def test_get_entity_by_id(self):
        """Test retrieving entities by ID."""
        # Add entity first
        character = self.db.add_entity(self.test_character)
        
        # Retrieve by ID
        retrieved_character = self.db.get_entity_by_id(Character, character.id)
        self.assertIsNotNone(retrieved_character)
        self.assertEqual(retrieved_character.name, "Test Character")
        self.assertEqual(retrieved_character.domain, "Aumian")
    
    def test_get_entity_by_name(self):
        """Test retrieving entities by name."""
        # Add entity first
        self.db.add_entity(self.test_character)
        
        # Retrieve by name
        retrieved_character = self.db.get_entity_by_name(Character, "Test Character")
        self.assertIsNotNone(retrieved_character)
        self.assertEqual(retrieved_character.domain, "Aumian")
        self.assertEqual(retrieved_character.specific_type, "Character")
    
    def test_update_entity(self):
        """Test updating entity attributes."""
        # Add entity first
        character = self.db.add_entity(self.test_character)
        
        # Update entity
        update_data = {
            "name": "Updated Character",
            "domain": "Valain",
            "subdomain": "Mage",
            "birth_cycle": "Dusk"
        }
        
        updated_character = self.db.update_entity(character, update_data)
        
        # Verify updates
        self.assertEqual(updated_character.name, "Updated Character")
        self.assertEqual(updated_character.domain, "Valain")
        self.assertEqual(updated_character.subdomain, "Mage")
        self.assertEqual(updated_character.birth_cycle, "Dusk")
        
        # Original attributes should remain unchanged
        self.assertEqual(updated_character.type, "Player")
        self.assertEqual(updated_character.imperative, "Explore")
    
    def test_query_entities(self):
        """Test querying entities with filters."""
        # Add multiple entities
        self.db.add_entity(Character(
            name="Alia", 
            type="Player", 
            domain="Aumian", 
            subdomain="Warrior"
        ))
        
        self.db.add_entity(Character(
            name="Lorath", 
            type="NPC", 
            domain="Aumian", 
            subdomain="Mage"
        ))
        
        self.db.add_entity(Character(
            name="Keth", 
            type="Player", 
            domain="Valain", 
            subdomain="Scout"
        ))
        
        # Query by domain
        aumian_characters = self.db.query_entities(
            Character, 
            filters={"domain": "Aumian"}
        )
        self.assertEqual(len(aumian_characters), 2)
        
        # Query by type and domain
        aumian_players = self.db.query_entities(
            Character, 
            filters={"domain": "Aumian", "type": "Player"}
        )
        self.assertEqual(len(aumian_players), 1)
        self.assertEqual(aumian_players[0].name, "Alia")
    
    def test_search_entities(self):
        """Test searching entities by text."""
        # Add entities
        self.db.add_entity(Character(
            name="Alia the Brave", 
            type="Player", 
            domain="Aumian", 
            description="A brave warrior from the eastern citadels."
        ))
        
        self.db.add_entity(Character(
            name="Lorath", 
            type="NPC", 
            domain="Aumian", 
            description="A merchant known for selling brave weapons."
        ))
        
        # Search by name
        name_results = self.db.search_entities(Character, "Alia")
        self.assertEqual(len(name_results), 1)
        
        # Search by description
        desc_results = self.db.search_entities(Character, "brave")
        self.assertEqual(len(desc_results), 2)
    
    def test_delete_entity(self):
        """Test deleting entities."""
        # Add entity
        character = self.db.add_entity(self.test_character)
        
        # Verify it exists
        retrieved = self.db.get_entity_by_id(Character, character.id)
        self.assertIsNotNone(retrieved)
        
        # Delete it
        result = self.db.delete_entity(character)
        self.assertTrue(result)
        
        # Verify it's gone
        deleted = self.db.get_entity_by_id(Character, character.id)
        self.assertIsNone(deleted)
    
    def test_count_entities(self):
        """Test counting entities."""
        # Add entities
        self.db.add_entity(Character(name="Char1", type="Player", domain="Aumian"))
        self.db.add_entity(Character(name="Char2", type="NPC", domain="Aumian"))
        self.db.add_entity(Character(name="Char3", type="Player", domain="Valain"))
        
        # Count all
        all_count = self.db.count_entities(Character)
        self.assertEqual(all_count, 3)
        
        # Count with filter
        aumian_count = self.db.count_entities(Character, {"domain": "Aumian"})
        self.assertEqual(aumian_count, 2)
        
        player_count = self.db.count_entities(Character, {"type": "Player"})
        self.assertEqual(player_count, 2)

if __name__ == "__main__":
    unittest.main()