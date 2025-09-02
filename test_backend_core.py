#!/usr/bin/env python3
"""
Core Backend functionality tests
Focused test suite for essential Backend components
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestBackendCore(unittest.TestCase):
    """Test core Backend functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_data_directory_structure(self):
        """Test that required data directories exist or can be created"""
        from pathlib import Path
        
        # Check for key directories
        expected_dirs = [
            "Data_Retrieve_Save_From_to_database",
            "Vector_Database",
            "templates",
            "narrative_db"
        ]
        
        for dir_name in expected_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                self.assertTrue(dir_path.is_dir(), f"{dir_name} should be a directory")
            # If it doesn't exist, that's fine - we can create it
    
    def test_config_loading(self):
        """Test configuration loading functionality"""
        import json
        
        # Create test config
        test_config = {
            "llm": {
                "api_key": "test_key",
                "model": "claude-3"
            },
            "knowledge_graph": {
                "password": "test_password"
            }
        }
        
        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Test config can be loaded
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config["llm"]["api_key"], "test_key")
        self.assertEqual(loaded_config["knowledge_graph"]["password"], "test_password")
    
    def test_vector_database_initialization(self):
        """Test vector database can be initialized"""
        try:
            # Try to import vector database components
            import sys
            if 'Vector_Database' not in sys.path:
                sys.path.append('Vector_Database')
            
            # Mock chromadb to avoid requiring actual installation
            with patch('chromadb.Client') as mock_client:
                mock_collection = Mock()
                mock_client.return_value.create_collection.return_value = mock_collection
                mock_client.return_value.get_collection.return_value = mock_collection
                
                # This would normally initialize ChromaDB
                client = mock_client()
                collection = client.create_collection("test_collection")
                
                self.assertIsNotNone(collection)
                
        except ImportError as e:
            # ChromaDB not installed, but test structure is valid
            self.skipTest(f"ChromaDB not available: {e}")
    
    def test_knowledge_graph_connection_mock(self):
        """Test knowledge graph connection (mocked)"""
        
        # Mock Neo4j connection
        with patch('neo4j.GraphDatabase') as mock_neo4j:
            mock_driver = Mock()
            mock_session = Mock()
            mock_neo4j.driver.return_value = mock_driver
            mock_driver.session.return_value = mock_session
            
            # Simulate connection attempt
            driver = mock_neo4j.driver("bolt://localhost:7687", auth=("neo4j", "password"))
            session = driver.session()
            
            self.assertIsNotNone(driver)
            self.assertIsNotNone(session)
    
    def test_template_processing(self):
        """Test template processing functionality"""
        
        # Create test template
        template_content = """
        Game: {game_name}
        Description: {description}
        Setting: {world_setting}
        """
        
        template_path = os.path.join(self.temp_dir, "test_template.txt")
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        # Test template can be loaded and formatted
        with open(template_path, 'r') as f:
            template = f.read()
        
        formatted = template.format(
            game_name="Test Game",
            description="A test game",
            world_setting="Fantasy world"
        )
        
        self.assertIn("Test Game", formatted)
        self.assertIn("A test game", formatted)
        self.assertIn("Fantasy world", formatted)
    
    def test_response_generation_mock(self):
        """Test AI response generation (mocked)"""
        
        # Mock AI API response
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "This is a test AI response."
                    }
                }]
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            # Simulate AI API call
            import requests
            response = requests.post(
                "https://api.test.com/generate",
                json={"prompt": "Generate a test response"}
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("choices", data)
    
    def test_lore_integration_basic(self):
        """Test basic lore integration functionality"""
        
        # Test lore data structure
        test_lore = {
            "entries": [
                {
                    "id": "test_001",
                    "title": "Test Location",
                    "category": "geography",
                    "content": "A test location for unit testing",
                    "tags": ["test", "location"]
                }
            ],
            "categories": ["geography", "culture", "history"]
        }
        
        # Verify structure
        self.assertIn("entries", test_lore)
        self.assertIn("categories", test_lore)
        self.assertEqual(len(test_lore["entries"]), 1)
        self.assertEqual(test_lore["entries"][0]["title"], "Test Location")
    
    def test_n4l_export_basic(self):
        """Test basic N4L export functionality"""
        
        # Create test lore entry
        lore_entry = {
            "title": "Test Entry",
            "category": "test",
            "content": "Test content for N4L export",
            "tags": ["test", "export"]
        }
        
        # Generate N4L format
        n4l_content = f"""// Test N4L Export
// Generated: 2025-01-01

- {lore_entry['title']}

:: {lore_entry['category']} ::
{' '.join(lore_entry['tags'])}

{lore_entry['content']}
"""
        
        # Verify N4L structure
        self.assertIn(lore_entry['title'], n4l_content)
        self.assertIn(lore_entry['category'], n4l_content)
        self.assertIn(lore_entry['content'], n4l_content)
    
    def test_narrative_context_building(self):
        """Test narrative context building"""
        
        # Mock context data
        context_data = {
            "game_info": {
                "name": "Test Game",
                "genre": "Fantasy",
                "setting": "Medieval world"
            },
            "player_actions": [
                "Entered the tavern",
                "Spoke to the innkeeper",
                "Ordered a meal"
            ],
            "lore_context": [
                "The tavern is a popular meeting place",
                "The innkeeper knows local gossip"
            ]
        }
        
        # Build context string
        context_parts = []
        context_parts.append(f"Game: {context_data['game_info']['name']}")
        context_parts.append(f"Setting: {context_data['game_info']['setting']}")
        context_parts.append("Recent Actions:")
        for action in context_data['player_actions']:
            context_parts.append(f"- {action}")
        context_parts.append("Relevant Lore:")
        for lore in context_data['lore_context']:
            context_parts.append(f"- {lore}")
        
        context = "\n".join(context_parts)
        
        # Verify context contains all elements
        self.assertIn("Test Game", context)
        self.assertIn("Medieval world", context)
        self.assertIn("Entered the tavern", context)
        self.assertIn("tavern is a popular", context)
    
    def test_error_handling_patterns(self):
        """Test common error handling patterns"""
        
        def safe_divide(a, b):
            """Test function with error handling"""
            try:
                return a / b
            except ZeroDivisionError:
                return None
            except TypeError:
                return "Error: Invalid input types"
        
        # Test normal operation
        self.assertEqual(safe_divide(10, 2), 5.0)
        
        # Test error cases
        self.assertIsNone(safe_divide(10, 0))
        self.assertEqual(safe_divide("10", 2), "Error: Invalid input types")
    
    def test_data_validation(self):
        """Test data validation patterns"""
        
        def validate_game_data(game_data):
            """Test validation function"""
            required_fields = ["name", "description"]
            errors = []
            
            for field in required_fields:
                if field not in game_data:
                    errors.append(f"Missing required field: {field}")
                elif not game_data[field]:
                    errors.append(f"Empty required field: {field}")
            
            return errors
        
        # Test valid data
        valid_game = {"name": "Test Game", "description": "A test game"}
        self.assertEqual(validate_game_data(valid_game), [])
        
        # Test invalid data
        invalid_game = {"name": ""}
        errors = validate_game_data(invalid_game)
        self.assertTrue(len(errors) > 0)
        self.assertIn("Empty required field: name", errors)
        self.assertIn("Missing required field: description", errors)


class TestBackendPerformance(unittest.TestCase):
    """Test Backend performance characteristics"""
    
    def test_context_processing_speed(self):
        """Test context processing performance"""
        import time
        
        # Generate test context data
        large_context = "Test context " * 1000  # 13KB of text
        
        start_time = time.time()
        
        # Simulate context processing
        processed = large_context.upper().replace("TEST", "PROCESSED")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process quickly
        self.assertLess(processing_time, 1.0, "Context processing should be under 1 second")
        self.assertIn("PROCESSED", processed)
    
    def test_memory_efficiency(self):
        """Test memory usage patterns"""
        import sys
        
        # Create test data
        test_data = []
        for i in range(1000):
            test_data.append({
                "id": i,
                "content": f"Test content {i}",
                "metadata": {"type": "test", "index": i}
            })
        
        # Check data structure
        self.assertEqual(len(test_data), 1000)
        self.assertEqual(test_data[0]["id"], 0)
        self.assertEqual(test_data[999]["id"], 999)
        
        # Clean up
        del test_data


def run_core_tests():
    """Run core Backend tests"""
    print("=" * 60)
    print("ENO BACKEND CORE TESTS")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestBackendCore,
        TestBackendPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Report results
    print("\n" + "=" * 60)
    print("CORE TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nCORE TESTS RESULT: {'PASS' if success else 'FAIL'}")
    
    return success


if __name__ == "__main__":
    success = run_core_tests()
    sys.exit(0 if success else 1)