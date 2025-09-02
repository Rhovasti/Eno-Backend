#!/usr/bin/env python3
"""
Test script for the response generation system.
"""

import logging
import unittest
import os
import json
from unittest.mock import patch, MagicMock

from Data_Retrieve_Save_From_to_database.response_generator import (
    ResponseGenerator,
    GameConfig,
    ChapterConfig,
    BeatConfig,
    PostResponse
)

from Data_Retrieve_Export_From_to_user.game_api import GameAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TestResponseGeneration(unittest.TestCase):
    """Test cases for the response generation system."""

    def setUp(self):
        """Set up for tests."""
        # Mock the LLM service
        self.response_generator = ResponseGenerator(
            vector_db_path="./test_db",
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="nasukili12",
            llm_service="mock"  # Use mock service for testing
        )
        
        # Mock the OpenAI client
        self.response_generator.llm_ready = True
        self.response_generator.client = MagicMock()
        self.response_generator._generate_llm_response = MagicMock(
            return_value="This is a test response."
        )
        
        # Set up game API with mock response generator
        self.game_api = GameAPI(
            base_url="http://localhost:3000/",
            response_generator=self.response_generator
        )
        
        # Mock game API methods
        self.game_api.login = MagicMock(return_value=True)
        self.game_api.token = "test_token"
        self.game_api.user = {"id": 1, "username": "test_user"}
        
        # Mock API methods
        self.game_api.create_post = MagicMock(
            return_value={"id": 123, "title": "Test Post", "content": "Test content"}
        )
        self.game_api.get_post = MagicMock(
            return_value={
                "id": 456,
                "title": "Test Post",
                "content": "This is a test post.",
                "postType": "player"
            }
        )
        self.game_api.get_game = MagicMock(
            return_value={"id": 789, "name": "Test Game", "description": "Test description"}
        )
        self.game_api.get_chapter = MagicMock(
            return_value={"id": 101, "title": "Test Chapter", "description": "Test chapter", "gameId": 789}
        )
        self.game_api.get_beat = MagicMock(
            return_value={"id": 102, "title": "Test Beat", "description": "Test beat", "chapterId": 101}
        )

    def test_game_narrative_generation(self):
        """Test generating a game narrative."""
        config = GameConfig(
            name="Test Game",
            description="A test game for unit testing",
            genre="Fantasy",
            themes=["heroic", "adventure"],
            tone="dramatic"
        )
        
        # Call the method
        narrative = self.response_generator.create_game_narrative(config)
        
        # Verify the result
        self.assertIsNotNone(narrative)
        self.assertTrue(len(narrative) > 0)
        
        # Verify the mock was called
        self.response_generator._generate_llm_response.assert_called_once()

    def test_chapter_narrative_generation(self):
        """Test generating a chapter narrative."""
        config = ChapterConfig(
            title="Test Chapter",
            description="A test chapter for unit testing",
            goals=["Find the treasure", "Defeat the villain"],
            setting="Ancient Temple",
            key_characters=["Hero", "Sidekick", "Villain"]
        )
        
        # Call the method
        narrative = self.response_generator.create_chapter_narrative("Test Game", config)
        
        # Verify the result
        self.assertIsNotNone(narrative)
        self.assertTrue(len(narrative) > 0)
        
        # Verify the mock was called
        self.assertEqual(self.response_generator._generate_llm_response.call_count, 2)

    def test_beat_narrative_generation(self):
        """Test generating a beat narrative."""
        config = BeatConfig(
            title="Test Beat",
            description="A test beat for unit testing",
            mood="tense",
            location="Dungeon",
            characters_present=["Hero", "Villain"],
            goals=["Escape the trap"]
        )
        
        # Call the method
        narrative = self.response_generator.create_beat_narrative(
            game_name="Test Game",
            chapter_title="Test Chapter",
            config=config
        )
        
        # Verify the result
        self.assertIsNotNone(narrative)
        self.assertTrue(len(narrative) > 0)
        
        # Verify the mock was called
        self.assertEqual(self.response_generator._generate_llm_response.call_count, 3)

    def test_post_response_generation(self):
        """Test generating a post response."""
        # Call the method
        post_response = self.response_generator.generate_post_response(
            beat_id=102,
            post_content="This is a test post content.\nLocation: Dungeon\nCharacters: Hero, Villain",
            character_name="GM",
            post_type="gm"
        )
        
        # Verify the result
        self.assertIsNotNone(post_response)
        self.assertIsInstance(post_response, PostResponse)
        self.assertEqual(post_response.beat_id, 102)
        self.assertEqual(post_response.post_type, "gm")
        self.assertTrue(hasattr(post_response, 'title'))
        self.assertTrue(hasattr(post_response, 'content'))
        
        # Verify the mock was called
        self.assertEqual(self.response_generator._generate_llm_response.call_count, 5)  # Content + title

    def test_game_api_create_post(self):
        """Test creating a post through the game API."""
        # Call the method
        post = self.game_api.create_post(
            beat_id=102,
            title="Test API Post",
            content="This is a test post from the API.",
            post_type="gm"
        )
        
        # Verify the result
        self.assertIsNotNone(post)
        self.assertEqual(post["id"], 123)
        self.assertEqual(post["title"], "Test Post")
        
        # Verify the mock was called
        self.game_api.create_post.assert_called_once()

    def test_game_api_generate_and_post_response(self):
        """Test generating and posting a response through the game API."""
        # Mock the response_generator.generate_post_response method
        self.response_generator.generate_post_response = MagicMock(
            return_value=PostResponse(
                title="Response Title",
                content="Response content",
                post_type="gm",
                beat_id=102
            )
        )
        
        # Call the method
        response = self.game_api.generate_and_post_response(
            beat_id=102,
            post_id=456,
            post_type="gm"
        )
        
        # Verify the result
        self.assertIsNotNone(response)
        self.assertEqual(response["id"], 123)
        
        # Verify the mocks were called
        self.game_api.get_post.assert_called_once()
        self.response_generator.generate_post_response.assert_called_once()
        self.game_api.create_post.assert_called()


if __name__ == "__main__":
    unittest.main()