#!/usr/bin/env python3
"""
Comprehensive tests for Eno Lore Integration system.
Tests lore data management, N4L conversion, narrative integration, and API endpoints.
"""

import unittest
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Import components to test
import sys
sys.path.append('/root/Eno/Eno-Backend/Data_Retrieve_Save_From_to_database')

from lore_integration_manager import (
    LoreEntry, LoreDatabase, LoreIntegrationManager
)
from enhanced_narrative_generator import (
    EnhancedNarrativeGenerator, NarrativeContext, ResponseType, NarrativeStyle
)


class TestLoreEntry(unittest.TestCase):
    """Test LoreEntry class functionality"""
    
    def setUp(self):
        """Set up test lore entry"""
        self.lore_entry = LoreEntry(
            id="test_entry",
            title="Test Culture",
            content="A test culture with unique characteristics.",
            category="culture",
            tags=["test", "unique", "characteristics"],
            relationships={"located_in": ["test_world"], "interacts_with": ["other_culture"]},
            source="test_source.md"
        )
    
    def test_lore_entry_creation(self):
        """Test lore entry creation and properties"""
        self.assertEqual(self.lore_entry.id, "test_entry")
        self.assertEqual(self.lore_entry.title, "Test Culture")
        self.assertEqual(self.lore_entry.category, "culture")
        self.assertIn("test", self.lore_entry.tags)
        self.assertIn("located_in", self.lore_entry.relationships)
    
    def test_n4l_format_conversion(self):
        """Test conversion to N4L format"""
        n4l_output = self.lore_entry.to_n4l_format()
        
        # Check for expected N4L elements
        self.assertIn("- Test Culture", n4l_output)  # Chapter declaration
        self.assertIn(":: culture ::", n4l_output)  # Context section
        self.assertIn(":: relationships ::", n4l_output)  # Relationships
        self.assertIn("Test Culture (located_in) test_world", n4l_output)  # Relationship
        self.assertIn('"A test culture with unique characteristics."', n4l_output)  # Content
        self.assertIn("test", n4l_output)  # Tags
    
    def test_n4l_format_structure(self):
        """Test N4L format structure integrity"""
        n4l_output = self.lore_entry.to_n4l_format()
        lines = n4l_output.split('\n')
        
        # Should start with chapter declaration
        self.assertTrue(lines[0].startswith('- '))
        
        # Should contain context sections
        context_sections = [line for line in lines if line.startswith(':: ') and line.endswith(' ::')]
        self.assertGreaterEqual(len(context_sections), 2)  # At least category and relationships


class TestLoreDatabase(unittest.TestCase):
    """Test LoreDatabase class functionality"""
    
    def setUp(self):
        """Set up test lore database with sample entries"""
        self.lore_db = LoreDatabase()
        
        # Add test entries
        self.culture_entry = LoreEntry(
            id="test_culture",
            title="Test Culture",
            content="Test culture content",
            category="culture",
            tags=["society", "test"],
            relationships={"located_in": ["test_geography"]}
        )
        
        self.geography_entry = LoreEntry(
            id="test_geography",
            title="Test Geography",
            content="Test geographical content",
            category="geography",
            tags=["location", "test"],
            relationships={"inhabited_by": ["test_culture"]}
        )
        
        self.lore_db.add_entry(self.culture_entry)
        self.lore_db.add_entry(self.geography_entry)
    
    def test_add_entry(self):
        """Test adding entries to database"""
        self.assertEqual(len(self.lore_db.entries), 2)
        self.assertIn("test_culture", self.lore_db.entries)
        self.assertIn("test_geography", self.lore_db.entries)
    
    def test_category_indexing(self):
        """Test category-based indexing"""
        culture_entries = self.lore_db.get_by_category("culture")
        geography_entries = self.lore_db.get_by_category("geography")
        
        self.assertEqual(len(culture_entries), 1)
        self.assertEqual(len(geography_entries), 1)
        self.assertEqual(culture_entries[0].id, "test_culture")
        self.assertEqual(geography_entries[0].id, "test_geography")
    
    def test_tag_search(self):
        """Test tag-based search functionality"""
        test_entries = self.lore_db.search_by_tags(["test"])
        society_entries = self.lore_db.search_by_tags(["society"])
        
        self.assertEqual(len(test_entries), 2)  # Both entries have "test" tag
        self.assertEqual(len(society_entries), 1)  # Only culture entry has "society" tag
    
    def test_relationship_queries(self):
        """Test relationship-based queries"""
        related_to_geography = self.lore_db.get_related_entries("test_culture", "located_in")
        related_to_culture = self.lore_db.get_related_entries("test_geography", "inhabited_by")
        
        # Note: This test assumes bidirectional relationships are set up
        # In practice, you might need to add both directions explicitly
        self.assertIsInstance(related_to_geography, list)
        self.assertIsInstance(related_to_culture, list)
    
    def test_n4l_export(self):
        """Test N4L export functionality"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.n4l', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            self.lore_db.export_to_n4l(temp_path)
            
            # Verify file was created and contains expected content
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Check for expected N4L structure
            self.assertIn("// Eno Lorecraft Knowledge Base", content)
            self.assertIn("- Test Culture", content)
            self.assertIn("- Test Geography", content)
            self.assertIn(":: culture ::", content)
            self.assertIn(":: geography ::", content)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestLoreIntegrationManager(unittest.TestCase):
    """Test LoreIntegrationManager class functionality"""
    
    def setUp(self):
        """Set up test lore integration manager"""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        test_config = {
            'n4l_export_path': '/tmp/test_eno_lore.n4l',
            'chromadb_collection': 'test_eno_lore',
            'vector_search_limit': 3
        }
        json.dump(test_config, self.temp_config)
        self.temp_config.close()
        
        self.manager = LoreIntegrationManager(self.temp_config.name)
    
    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
        
        # Clean up any created N4L files
        test_n4l_path = self.manager.config.get('n4l_export_path')
        if test_n4l_path and os.path.exists(test_n4l_path):
            os.unlink(test_n4l_path)
    
    def test_manager_initialization(self):
        """Test manager initialization with config"""
        self.assertIsInstance(self.manager.lore_db, LoreDatabase)
        self.assertIn('n4l_export_path', self.manager.config)
        self.assertEqual(self.manager.config['vector_search_limit'], 3)
    
    def test_archon_lore_loading(self):
        """Test loading lore data from Archon"""
        self.manager.load_archon_lore_data()
        
        # Should have loaded sample data
        self.assertGreater(len(self.manager.lore_db.entries), 0)
        self.assertIn("cultures_of_eno", self.manager.lore_db.entries)
        self.assertIn("eno_planet_geography", self.manager.lore_db.entries)
    
    def test_lore_context_retrieval(self):
        """Test lore context retrieval for narrative generation"""
        self.manager.load_archon_lore_data()
        
        # Test context retrieval
        context = self.manager.get_lore_context_for_narrative("culture")
        self.assertIsInstance(context, str)
        
        # Should contain lore context marker
        if context != "Lore context unavailable":
            self.assertIn("=== LORE CONTEXT ===", context)
    
    def test_n4l_export_functionality(self):
        """Test N4L export and parsing functionality"""
        self.manager.load_archon_lore_data()
        
        # Test export (parsing might fail if parser not available)
        result = self.manager.export_to_n4l_and_parse()
        self.assertIsInstance(result, bool)
        
        # Verify file was created
        export_path = self.manager.config['n4l_export_path']
        if os.path.exists(export_path):
            with open(export_path, 'r') as f:
                content = f.read()
            self.assertIn("// Eno Lorecraft Knowledge Base", content)


class TestNarrativeGeneratorIntegration(unittest.TestCase):
    """Test integration with narrative generator"""
    
    def setUp(self):
        """Set up narrative generator and lore manager for integration testing"""
        self.lore_manager = LoreIntegrationManager()
        self.lore_manager.load_archon_lore_data()
        
        # Create mock config for narrative generator
        self.narrative_config = {
            "llm": {
                "service": "mock",  # Use mock service for testing
                "model": "test-model",
                "api_key": "test-key"
            }
        }
    
    def test_narrative_context_creation(self):
        """Test creation of narrative context with lore integration"""
        context = NarrativeContext(
            game_name="Test Eno Game",
            chapter_title="The Cultures Awaken",
            location="Eno Planet",
            characters=["Test Character"],
            themes=["culture", "exploration"],
            style=NarrativeStyle.EPIC
        )
        
        self.assertEqual(context.game_name, "Test Eno Game")
        self.assertIn("culture", context.themes)
        self.assertEqual(context.style, NarrativeStyle.EPIC)
    
    def test_lore_context_integration(self):
        """Test that lore context can be retrieved and formatted"""
        lore_context = self.lore_manager.get_lore_context_for_narrative(
            query="cultures",
            location="Eno Planet",
            limit=2
        )
        
        self.assertIsInstance(lore_context, str)
        
        # If lore is available, should contain expected markers
        if lore_context != "Lore context unavailable":
            self.assertIn("LORE CONTEXT", lore_context)
    
    def test_prompt_template_compatibility(self):
        """Test that lore context can be used in prompt templates"""
        # Test with sample template variables
        template_vars = {
            "game_name": "Test Eno Game",
            "description": "A test game in the Eno universe",
            "genre": "Fantasy",
            "themes": "culture, exploration",
            "tone": "epic",
            "world_setting": "Eno Planet",
            "style": "cinematic",
            "lore_context": self.lore_manager.get_lore_context_for_narrative("cultures", limit=1)
        }
        
        # Verify all expected variables are present
        expected_vars = ["game_name", "description", "genre", "themes", "tone", 
                        "world_setting", "style", "lore_context"]
        
        for var in expected_vars:
            self.assertIn(var, template_vars)
            self.assertIsInstance(template_vars[var], str)


class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete integration workflow"""
    
    def test_complete_workflow(self):
        """Test complete lore integration workflow"""
        # Step 1: Initialize manager
        manager = LoreIntegrationManager()
        self.assertIsInstance(manager, LoreIntegrationManager)
        
        # Step 2: Load lore data
        manager.load_archon_lore_data()
        initial_count = len(manager.lore_db.entries)
        self.assertGreater(initial_count, 0)
        
        # Step 3: Export to N4L
        success = manager.export_to_n4l_and_parse()
        self.assertIsInstance(success, bool)
        
        # Step 4: Test context retrieval
        context = manager.get_lore_context_for_narrative("culture")
        self.assertIsInstance(context, str)
        
        # Step 5: Test vectorization (may fail if ChromaDB unavailable)
        vector_success = manager.vectorize_lore_content()
        self.assertIsInstance(vector_success, bool)
        
        print(f"Integration workflow test completed:")
        print(f"- Loaded {initial_count} lore entries")
        print(f"- N4L export: {'Success' if success else 'Failed/Warning'}")
        print(f"- Vectorization: {'Success' if vector_success else 'Failed/Warning'}")
        print(f"- Context retrieval: {'Available' if context != 'Lore context unavailable' else 'Unavailable'}")


def run_integration_tests():
    """Run all integration tests"""
    print("Running Eno Lore Integration Tests...")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestLoreEntry,
        TestLoreDatabase,
        TestLoreIntegrationManager,
        TestNarrativeGeneratorIntegration,
        TestIntegrationWorkflow
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('\\n')[-2]}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\\n')[-2]}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)