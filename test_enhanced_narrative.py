#!/usr/bin/env python3
"""
Test script for the enhanced narrative generation system.
Tests integration with Neo4j, ChromaDB, and AI services.
"""

import unittest
import json
import logging
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from Data_Retrieve_Save_From_to_database.enhanced_narrative_generator import (
    EnhancedNarrativeGenerator,
    NarrativeContext,
    NarrativeStyle,
    ResponseType,
    PromptTemplate,
    PromptLibrary
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPromptTemplates(unittest.TestCase):
    """Test prompt template functionality"""
    
    def setUp(self):
        self.template = PromptTemplate(
            name="test_template",
            system_message="You are a test assistant.",
            user_template="Generate {type} for {name} with {style}.",
            variables=["type", "name", "style"],
            max_tokens=100,
            temperature=0.7
        )
    
    def test_template_formatting(self):
        """Test that templates format correctly"""
        system, user = self.template.format(
            type="story",
            name="TestGame",
            style="dramatic"
        )
        
        self.assertEqual(system, "You are a test assistant.")
        self.assertEqual(user, "Generate story for TestGame with dramatic.")
    
    def test_missing_variables(self):
        """Test that missing variables raise errors"""
        with self.assertRaises(ValueError):
            self.template.format(type="story", name="TestGame")
    
    def test_extra_variables(self):
        """Test that extra variables are ignored"""
        system, user = self.template.format(
            type="story",
            name="TestGame",
            style="dramatic",
            extra="ignored"
        )
        self.assertIn("TestGame", user)


class TestNarrativeContext(unittest.TestCase):
    """Test narrative context functionality"""
    
    def test_context_to_prompt(self):
        """Test context conversion to prompt string"""
        context = NarrativeContext(
            game_name="TestGame",
            chapter_title="Chapter 1",
            location="Test Location",
            characters=["Alice", "Bob"],
            themes=["adventure", "mystery"],
            mood="tense",
            style=NarrativeStyle.DRAMATIC
        )
        
        prompt_text = context.to_prompt_context()
        
        self.assertIn("TestGame", prompt_text)
        self.assertIn("Chapter 1", prompt_text)
        self.assertIn("Test Location", prompt_text)
        self.assertIn("Alice", prompt_text)
        self.assertIn("adventure", prompt_text)
        self.assertIn("tense", prompt_text)
        self.assertIn("dramatic", prompt_text)


class TestPromptLibrary(unittest.TestCase):
    """Test prompt library functionality"""
    
    def setUp(self):
        self.library = PromptLibrary()
    
    def test_all_templates_exist(self):
        """Test that all response types have templates"""
        for response_type in ResponseType:
            template = self.library.get_template(response_type)
            self.assertIsNotNone(template)
            self.assertIsInstance(template, PromptTemplate)
    
    def test_template_variables(self):
        """Test that key templates have expected variables"""
        gm_template = self.library.get_template(ResponseType.GM_RESPONSE)
        self.assertIn("player_action", gm_template.variables)
        self.assertIn("kg_context", gm_template.variables)
        self.assertIn("vector_context", gm_template.variables)


class TestEnhancedNarrativeGenerator(unittest.TestCase):
    """Test the enhanced narrative generator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = EnhancedNarrativeGenerator(
            vector_db_path="./test_narrative_db",
            llm_service="openai",
            llm_model="gpt-4"
        )
        
        # Mock the AI client
        self.generator.openai_client = MagicMock()
        
        # Mock the context manager
        self.generator.context_manager = MagicMock()
        self.generator.context_manager.kg_connected = True
        self.generator.context_manager.kg_manager = MagicMock()
    
    def test_initialization(self):
        """Test generator initialization"""
        self.assertIsNotNone(self.generator.prompt_library)
        self.assertIsNotNone(self.generator.context_manager)
        self.assertEqual(self.generator.llm_service, "openai")
        self.assertEqual(self.generator.llm_model, "gpt-4")
    
    @patch('Data_Retrieve_Save_From_to_database.enhanced_narrative_generator.openai')
    def test_ai_generation(self, mock_openai):
        """Test AI text generation"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated narrative text"
        
        self.generator.openai_client.chat.completions.create.return_value = mock_response
        
        result = self.generator._generate_with_ai(
            system_message="System prompt",
            user_message="User prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        self.assertEqual(result, "Generated narrative text")
    
    def test_mock_response_generation(self):
        """Test mock response when AI is unavailable"""
        self.generator.openai_client = None
        
        result = self.generator._generate_with_ai(
            system_message="System",
            user_message="User"
        )
        
        self.assertIn("Mock Response", result)
        self.assertIn(self.generator.llm_model, result)
    
    def test_knowledge_graph_context(self):
        """Test knowledge graph context retrieval"""
        # Mock character retrieval
        mock_character = MagicMock()
        mock_character.description = "A brave warrior"
        self.generator.context_manager.kg_manager.get_character.return_value = mock_character
        
        # Mock location retrieval
        mock_location = MagicMock()
        mock_location.description = "A dark forest"
        self.generator.context_manager.kg_manager.get_location.return_value = mock_location
        
        context = self.generator._get_knowledge_graph_context([
            ("Alice", "Character"),
            ("Dark Forest", "Location")
        ])
        
        self.assertIn("Alice", context)
        self.assertIn("brave warrior", context)
        self.assertIn("Dark Forest", context)
        self.assertIn("dark forest", context)
    
    def test_vector_memory_context(self):
        """Test vector memory context retrieval"""
        mock_context = MagicMock()
        mock_context.to_text.return_value = "Previous narrative context"
        self.generator.context_manager.get_context_for_query.return_value = mock_context
        
        context = self.generator._get_vector_memory_context(
            query="test query",
            n_memories=5
        )
        
        self.assertEqual(context, "Previous narrative context")
    
    def test_game_intro_generation(self):
        """Test game introduction generation"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Epic game introduction"
        self.generator.openai_client.chat.completions.create.return_value = mock_response
        
        result = self.generator.generate_game_intro(
            game_name="Test Chronicles",
            description="A test game",
            genre="Fantasy",
            themes=["adventure", "friendship"],
            tone="hopeful",
            world_setting="Magical realm",
            style=NarrativeStyle.EPIC
        )
        
        self.assertEqual(result, "Epic game introduction")
        
        # Verify storage was called
        self.generator.context_manager.add_narrative_memory.assert_called()
    
    def test_gm_response_generation(self):
        """Test GM response generation"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "GM responds to action"
        self.generator.openai_client.chat.completions.create.return_value = mock_response
        
        # Mock context retrieval
        mock_context = MagicMock()
        mock_context.to_text.return_value = "Context text"
        self.generator.context_manager.get_context_for_query.return_value = mock_context
        
        context = NarrativeContext(
            game_name="TestGame",
            chapter_title="Chapter 1",
            location="Tavern"
        )
        
        result = self.generator.generate_gm_response(
            context=context,
            player_action="I search the room",
            character_name="Alice",
            scene_description="A dimly lit tavern"
        )
        
        self.assertEqual(result, "GM responds to action")
    
    def test_npc_dialogue_generation(self):
        """Test NPC dialogue generation"""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "NPC speaks eloquently"
        self.generator.openai_client.chat.completions.create.return_value = mock_response
        
        context = NarrativeContext(
            game_name="TestGame",
            location="Market"
        )
        
        result = self.generator.generate_npc_dialogue(
            context=context,
            npc_name="Merchant",
            npc_description="A shrewd trader",
            npc_personality="Cunning and greedy",
            situation="Negotiating prices",
            player_input="I'll give you 10 gold",
            npc_knowledge="Knows item is worth 50 gold",
            npc_goals="Maximize profit"
        )
        
        self.assertEqual(result, "NPC speaks eloquently")
    
    def test_narrative_storage(self):
        """Test that narratives are stored correctly"""
        context = NarrativeContext(
            game_name="TestGame",
            location="Castle",
            characters=["Knight", "Princess"]
        )
        
        self.generator._store_narrative(
            text="Test narrative",
            context=context,
            response_type=ResponseType.BEAT_NARRATIVE
        )
        
        # Verify storage was called with correct parameters
        self.generator.context_manager.add_narrative_memory.assert_called_once()
        call_args = self.generator.context_manager.add_narrative_memory.call_args
        
        self.assertEqual(call_args.kwargs['text'], "Test narrative")
        self.assertEqual(call_args.kwargs['source'], "ai_generated")
        self.assertEqual(call_args.kwargs['location'], "Castle")
        self.assertEqual(call_args.kwargs['importance'], 7)
    
    def test_knowledge_graph_update(self):
        """Test that knowledge graph is updated correctly"""
        context = NarrativeContext(
            game_name="TestGame",
            chapter_title="Chapter 1",
            beat_title="Opening",
            location="Village",
            characters=["Hero"],
            mood="peaceful",
            style=NarrativeStyle.WHIMSICAL
        )
        
        self.generator._update_knowledge_graph(
            text="Narrative text",
            context=context,
            response_type=ResponseType.BEAT_NARRATIVE
        )
        
        # Verify event creation was called
        self.generator.context_manager.kg_manager.create_event.assert_called_once()
        call_args = self.generator.context_manager.kg_manager.create_event.call_args
        event = call_args[0][0]
        
        self.assertEqual(event.event_type, "beat_narrative")
        self.assertEqual(event.properties['game_name'], "TestGame")
        self.assertEqual(event.properties['location'], "Village")
        self.assertEqual(event.properties['style'], "whimsical")
    
    def test_response_caching(self):
        """Test that responses are cached correctly"""
        # First call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Cached response"
        self.generator.openai_client.chat.completions.create.return_value = mock_response
        
        result1 = self.generator._generate_with_ai(
            system_message="System",
            user_message="User"
        )
        
        # Second call with same inputs
        result2 = self.generator._generate_with_ai(
            system_message="System",
            user_message="User"
        )
        
        self.assertEqual(result1, result2)
        # AI should only be called once due to caching
        self.generator.openai_client.chat.completions.create.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    @patch('Data_Retrieve_Save_From_to_database.enhanced_narrative_generator.ContextManager')
    @patch('Data_Retrieve_Save_From_to_database.enhanced_narrative_generator.openai')
    def test_full_narrative_flow(self, mock_openai, mock_context_manager):
        """Test complete narrative generation flow"""
        # Set up mocks
        mock_context = MagicMock()
        mock_context.kg_connected = True
        mock_context.kg_manager = MagicMock()
        mock_context_manager.return_value = mock_context
        
        # Initialize generator
        generator = EnhancedNarrativeGenerator(
            llm_service="openai",
            llm_model="gpt-4"
        )
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated narrative"
        mock_client.chat.completions.create.return_value = mock_response
        generator.openai_client = mock_client
        
        # Create game intro
        intro = generator.generate_game_intro(
            game_name="Epic Quest",
            description="An epic adventure",
            genre="Fantasy",
            themes=["heroism", "sacrifice"],
            tone="epic",
            world_setting="Ancient kingdom",
            style=NarrativeStyle.EPIC
        )
        
        self.assertEqual(intro, "Generated narrative")
        
        # Verify all components were called
        mock_context.add_narrative_memory.assert_called()
        mock_context.kg_manager.create_location.assert_called()
        mock_context.kg_manager.create_event.assert_called()


class TestPromptTemplateLoading(unittest.TestCase):
    """Test loading prompt templates from JSON"""
    
    def test_load_templates_from_json(self):
        """Test that prompt templates can be loaded from JSON file"""
        with open('/root/Eno/Eno-Backend/Data_Retrieve_Save_From_to_database/prompt_templates.json', 'r') as f:
            templates_data = json.load(f)
        
        self.assertIn('templates', templates_data)
        self.assertIn('game_intro', templates_data['templates'])
        self.assertIn('style_modifiers', templates_data)
        self.assertIn('context_integration', templates_data)
        
        # Verify template structure
        game_intro = templates_data['templates']['game_intro']
        self.assertIn('system_prompt', game_intro)
        self.assertIn('user_template', game_intro)
        self.assertIn('variables', game_intro)
        self.assertIn('max_tokens', game_intro)
        self.assertIn('temperature', game_intro)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)