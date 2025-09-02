#!/usr/bin/env python3
"""
Enhanced narrative generator module for the Eno game platform.
Implements advanced AI integration with Neo4j knowledge graph and ChromaDB vector search.
"""

import logging
import os
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import hashlib

# AI service imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from Vector_Database.context_manager import ContextManager, NarrativeContext
from Knowledge_Graph.knowledge_manager import KnowledgeGraphManager
from Knowledge_Graph.models.entity_models import Character, Location, Event

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NarrativeStyle(Enum):
    """Narrative styles for different types of content"""
    DRAMATIC = "dramatic"
    COMEDIC = "comedic"
    HORROR = "horror"
    MYSTERY = "mystery"
    EPIC = "epic"
    NOIR = "noir"
    WHIMSICAL = "whimsical"
    GRITTY = "gritty"


class ResponseType(Enum):
    """Types of responses the generator can create"""
    GAME_INTRO = "game_intro"
    CHAPTER_INTRO = "chapter_intro"
    BEAT_NARRATIVE = "beat_narrative"
    GM_RESPONSE = "gm_response"
    NPC_DIALOGUE = "npc_dialogue"
    SCENE_DESCRIPTION = "scene_description"
    ACTION_OUTCOME = "action_outcome"


@dataclass
class PromptTemplate:
    """Template for generating prompts"""
    name: str
    system_message: str
    user_template: str
    variables: List[str]
    max_tokens: int = 1500
    temperature: float = 0.7
    
    def format(self, **kwargs) -> Tuple[str, str]:
        """Format the template with provided variables"""
        missing_vars = set(self.variables) - set(kwargs.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")
        
        user_message = self.user_template.format(**kwargs)
        return self.system_message, user_message


@dataclass
class NarrativeContext:
    """Enhanced context for narrative generation"""
    game_name: str
    chapter_title: Optional[str] = None
    beat_title: Optional[str] = None
    location: Optional[str] = None
    characters: List[str] = field(default_factory=list)
    recent_events: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    mood: str = "neutral"
    style: NarrativeStyle = NarrativeStyle.DRAMATIC
    player_actions: List[str] = field(default_factory=list)
    world_state: Dict[str, Any] = field(default_factory=dict)
    
    def to_prompt_context(self) -> str:
        """Convert context to a string for prompt inclusion"""
        lines = []
        lines.append(f"Game: {self.game_name}")
        
        if self.chapter_title:
            lines.append(f"Chapter: {self.chapter_title}")
        
        if self.beat_title:
            lines.append(f"Current Beat: {self.beat_title}")
        
        if self.location:
            lines.append(f"Location: {self.location}")
        
        if self.characters:
            lines.append(f"Characters Present: {', '.join(self.characters)}")
        
        if self.recent_events:
            lines.append("Recent Events:")
            for event in self.recent_events[:5]:
                lines.append(f"  - {event}")
        
        if self.themes:
            lines.append(f"Themes: {', '.join(self.themes)}")
        
        lines.append(f"Mood: {self.mood}")
        lines.append(f"Style: {self.style.value}")
        
        if self.player_actions:
            lines.append("Recent Player Actions:")
            for action in self.player_actions[:3]:
                lines.append(f"  - {action}")
        
        return "\n".join(lines)


class PromptLibrary:
    """Library of prompt templates for different narrative generation tasks"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[ResponseType, PromptTemplate]:
        """Initialize all prompt templates"""
        templates = {}
        
        # Game introduction template
        templates[ResponseType.GAME_INTRO] = PromptTemplate(
            name="game_intro",
            system_message="""You are a master storyteller and game master for tabletop RPGs. 
            Your task is to create immersive, engaging narratives that draw players into the game world.
            Focus on atmosphere, themes, and hooks that make players want to explore and interact.""",
            user_template="""Create a compelling narrative introduction for a new tabletop RPG game:

Game Name: {game_name}
Description: {description}
Genre: {genre}
Themes: {themes}
Tone: {tone}
World Setting: {world_setting}

Requirements:
- Write an engaging introduction that sets the stage for this game world
- Include key themes, conflicts, and atmosphere
- Create a sense of mystery and adventure
- End with a hook that excites players to begin
- Length: 500-1000 words
- Style: {style}

Make the narrative immersive and cinematic, using vivid descriptions and emotional resonance.""",
            variables=["game_name", "description", "genre", "themes", "tone", "world_setting", "style"],
            max_tokens=2000,
            temperature=0.8
        )
        
        # Chapter introduction template
        templates[ResponseType.CHAPTER_INTRO] = PromptTemplate(
            name="chapter_intro",
            system_message="""You are a narrative designer crafting chapter transitions in an ongoing RPG campaign.
            Build on established lore while introducing new elements. Create smooth transitions that maintain continuity.""",
            user_template="""Create a chapter introduction for an ongoing game:

{context}

Chapter Title: {chapter_title}
Description: {chapter_description}
Setting: {setting}
Goals: {goals}
Key Characters: {key_characters}

Previous Context:
{previous_context}

Requirements:
- Bridge from previous events to new chapter
- Introduce setting and atmosphere
- Present key characters naturally
- Establish chapter goals and conflicts
- Create anticipation for upcoming events
- Length: 300-600 words

Write cinematically, focusing on sensory details and emotional stakes.""",
            variables=["context", "chapter_title", "chapter_description", "setting", "goals", 
                      "key_characters", "previous_context"],
            max_tokens=1500,
            temperature=0.7
        )
        
        # Beat narrative template
        templates[ResponseType.BEAT_NARRATIVE] = PromptTemplate(
            name="beat_narrative",
            system_message="""You are directing a scene in an interactive narrative. 
            Create dynamic moments that invite player participation while advancing the story.""",
            user_template="""Create a narrative beat for the current scene:

{context}

Beat Title: {beat_title}
Description: {beat_description}
Mood: {mood}
Location Details: {location_details}
Character Dynamics: {character_dynamics}
Immediate Goals: {goals}

Knowledge Graph Context:
{kg_context}

Vector Memory Context:
{vector_context}

Requirements:
- Set the scene with atmospheric details
- Show character interactions and tensions
- Progress toward beat goals
- Create decision points for players
- End with situation requiring response
- Length: 300-500 words
- Maintain {mood} mood throughout

Focus on show-don't-tell, using action and dialogue to reveal information.""",
            variables=["context", "beat_title", "beat_description", "mood", "location_details",
                      "character_dynamics", "goals", "kg_context", "vector_context"],
            max_tokens=1200,
            temperature=0.7
        )
        
        # GM response template
        templates[ResponseType.GM_RESPONSE] = PromptTemplate(
            name="gm_response",
            system_message="""You are a responsive game master reacting to player actions.
            Acknowledge player choices, show consequences, and keep the narrative moving forward.
            Be fair but maintain dramatic tension.""",
            user_template="""Generate a GM response to player action:

{context}

Player Action: {player_action}
Character Name: {character_name}
Current Scene: {scene_description}

Related Knowledge:
{kg_context}

Recent Narrative:
{vector_context}

Requirements:
- Acknowledge the player's action
- Show immediate consequences
- Reveal new information or complications
- Maintain narrative consistency
- Set up next decision point
- Length: 200-400 words

React dynamically while respecting established facts and maintaining story coherence.""",
            variables=["context", "player_action", "character_name", "scene_description",
                      "kg_context", "vector_context"],
            max_tokens=1000,
            temperature=0.6
        )
        
        # NPC dialogue template
        templates[ResponseType.NPC_DIALOGUE] = PromptTemplate(
            name="npc_dialogue",
            system_message="""You are voicing a non-player character in an RPG.
            Give them personality, motivations, and authentic dialogue that serves the narrative.""",
            user_template="""Generate NPC dialogue:

{context}

NPC Name: {npc_name}
NPC Description: {npc_description}
NPC Personality: {npc_personality}
Current Situation: {situation}
Player Statement/Question: {player_input}

NPC Knowledge:
{npc_knowledge}

NPC Goals:
{npc_goals}

Requirements:
- Stay in character
- Respond naturally to player input
- Reveal information appropriately
- Show personality through speech patterns
- Include relevant actions/gestures
- Length: 100-300 words

Make the NPC feel like a real person with their own agenda and perspective.""",
            variables=["context", "npc_name", "npc_description", "npc_personality",
                      "situation", "player_input", "npc_knowledge", "npc_goals"],
            max_tokens=800,
            temperature=0.8
        )
        
        # Scene description template
        templates[ResponseType.SCENE_DESCRIPTION] = PromptTemplate(
            name="scene_description",
            system_message="""You are painting vivid scenes for an RPG. 
            Create immersive environments that engage all senses and establish mood.""",
            user_template="""Describe the following scene:

{context}

Location: {location}
Time: {time_of_day}
Weather/Conditions: {conditions}
Mood: {mood}
Notable Features: {features}

Recent Events Here:
{recent_events}

Requirements:
- Engage multiple senses (sight, sound, smell, touch)
- Establish atmosphere and mood
- Include interactive elements players might notice
- Hint at potential dangers or opportunities
- Length: 150-300 words

Create a living environment that feels dynamic and reactive.""",
            variables=["context", "location", "time_of_day", "conditions", 
                      "mood", "features", "recent_events"],
            max_tokens=800,
            temperature=0.7
        )
        
        # Action outcome template
        templates[ResponseType.ACTION_OUTCOME] = PromptTemplate(
            name="action_outcome",
            system_message="""You are determining and narrating the outcomes of player actions. 
            Be fair, logical, and dramatic. Success and failure should both lead to interesting story developments.""",
            user_template="""Narrate the outcome of this action:

{context}

Action Attempted: {action}
Character Skills: {skills}
Difficulty: {difficulty}
Roll Result: {roll_result}
Environmental Factors: {factors}

Requirements:
- Describe the immediate result
- Show ripple effects if applicable
- Maintain cause-and-effect logic
- Create new opportunities or complications
- Keep the story moving forward
- Length: 150-300 words

Make outcomes feel earned and consequential.""",
            variables=["context", "action", "skills", "difficulty", "roll_result", "factors"],
            max_tokens=800,
            temperature=0.6
        )
        
        return templates
    
    def get_template(self, response_type: ResponseType) -> PromptTemplate:
        """Get a specific template"""
        if response_type not in self.templates:
            raise ValueError(f"Unknown response type: {response_type}")
        return self.templates[response_type]


class EnhancedNarrativeGenerator:
    """
    Enhanced narrative generator with advanced AI integration,
    context management, and prompt engineering.
    """
    
    def __init__(
        self,
        vector_db_path: str = "./narrative_db",
        embedding_model: str = "all-MiniLM-L6-v2",
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
        neo4j_database: str = "neo4j",
        llm_service: str = "openai",
        llm_model: str = "gpt-4",
        api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None
    ):
        """Initialize the enhanced narrative generator"""
        
        # Initialize context manager
        self.context_manager = ContextManager(
            vector_db_path=vector_db_path,
            embedding_model=embedding_model,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            neo4j_database=neo4j_database
        )
        
        # Initialize prompt library
        self.prompt_library = PromptLibrary()
        
        # Configure LLM service
        self.llm_service = llm_service
        self.llm_model = llm_model
        
        # Initialize AI clients
        self._initialize_ai_clients(api_key, anthropic_api_key)
        
        # Cache for generated content
        self.response_cache = {}
        
        logger.info(f"Initialized EnhancedNarrativeGenerator with {llm_service} using {llm_model}")
    
    def _initialize_ai_clients(self, openai_key: Optional[str], anthropic_key: Optional[str]):
        """Initialize AI service clients"""
        self.openai_client = None
        self.anthropic_client = None
        
        if self.llm_service == "openai" and OPENAI_AVAILABLE:
            api_key = openai_key or os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not provided")
        
        elif self.llm_service == "anthropic" and ANTHROPIC_AVAILABLE:
            api_key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                logger.info("Anthropic client initialized")
            else:
                logger.warning("Anthropic API key not provided")
    
    def _get_knowledge_graph_context(
        self,
        entities: List[Tuple[str, str]],
        max_depth: int = 2
    ) -> str:
        """Retrieve relevant context from the knowledge graph"""
        if not hasattr(self.context_manager, 'kg_manager') or not self.context_manager.kg_connected:
            return "Knowledge graph not available"
        
        context_parts = []
        
        for entity_name, entity_type in entities:
            try:
                if entity_type == "Character":
                    entity = self.context_manager.kg_manager.get_character(entity_name)
                    if entity:
                        context_parts.append(f"Character - {entity_name}: {entity.description}")
                        # Get relationships
                        relationships = self.context_manager.kg_manager.get_character_relationships(
                            entity_name, max_depth=max_depth
                        )
                        if relationships:
                            context_parts.append(f"  Relationships: {relationships}")
                
                elif entity_type == "Location":
                    entity = self.context_manager.kg_manager.get_location(entity_name)
                    if entity:
                        context_parts.append(f"Location - {entity_name}: {entity.description}")
                        # Get connected events
                        events = self.context_manager.kg_manager.get_location_events(entity_name)
                        if events:
                            context_parts.append(f"  Recent events: {', '.join([e.name for e in events[:3]])}")
                
                elif entity_type == "Event":
                    entity = self.context_manager.kg_manager.get_event(entity_name)
                    if entity:
                        context_parts.append(f"Event - {entity_name}: {entity.description}")
                        if entity.properties:
                            context_parts.append(f"  Details: {json.dumps(entity.properties, indent=2)}")
            
            except Exception as e:
                logger.error(f"Error retrieving {entity_type} {entity_name}: {e}")
        
        return "\n".join(context_parts) if context_parts else "No relevant entities found"
    
    def _get_vector_memory_context(
        self,
        query: str,
        n_memories: int = 5,
        location: Optional[str] = None
    ) -> str:
        """Retrieve relevant context from vector memory"""
        try:
            context = self.context_manager.get_context_for_query(
                query=query,
                location_name=location,
                n_memories=n_memories
            )
            return context.to_text()
        except Exception as e:
            logger.error(f"Error retrieving vector context: {e}")
            return "Vector memory not available"
    
    def _generate_with_ai(
        self,
        system_message: str,
        user_message: str,
        max_tokens: int = 1500,
        temperature: float = 0.7
    ) -> str:
        """Generate text using configured AI service"""
        
        # Check cache first
        cache_key = hashlib.md5(f"{system_message}{user_message}".encode()).hexdigest()
        if cache_key in self.response_cache:
            logger.info("Using cached response")
            return self.response_cache[cache_key]
        
        response = ""
        
        try:
            if self.llm_service == "openai" and self.openai_client:
                completion = self.openai_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                response = completion.choices[0].message.content
            
            elif self.llm_service == "anthropic" and self.anthropic_client:
                message = self.anthropic_client.messages.create(
                    model=self.llm_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                )
                response = message.content[0].text
            
            else:
                # Fallback to mock response
                response = self._generate_mock_response(user_message)
        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            response = self._generate_mock_response(user_message)
        
        # Cache the response
        self.response_cache[cache_key] = response
        
        return response
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate a mock response for testing"""
        return f"""[Mock Response - In production, this would be generated by {self.llm_model}]

Based on the provided context and requirements, here is a narrative response:

The scene unfolds with careful attention to the established world and characters. 
Drawing from the knowledge graph and vector memories, the narrative continues 
to develop the story in a way that respects player agency while maintaining 
dramatic tension and thematic consistency.

The characters interact naturally, their dialogue reflecting their established 
personalities and current circumstances. The setting comes alive through 
sensory details that immerse players in the moment.

As events progress, new complications arise that challenge the players while 
offering opportunities for meaningful choices. The narrative threads weave 
together, building toward moments of revelation and decision.

This response would normally be much more specific and tailored to the exact 
context provided, incorporating all the relevant details from the game state, 
character information, and recent events."""
    
    def generate_narrative(
        self,
        response_type: ResponseType,
        context: NarrativeContext,
        **kwargs
    ) -> str:
        """
        Generate a narrative response using the appropriate template and context.
        
        Args:
            response_type: Type of response to generate
            context: Narrative context
            **kwargs: Additional variables for the template
            
        Returns:
            Generated narrative text
        """
        # Get the appropriate template
        template = self.prompt_library.get_template(response_type)
        
        # Prepare template variables
        template_vars = {
            "context": context.to_prompt_context()
        }
        
        # Add knowledge graph context if needed
        if "kg_context" in template.variables:
            entities = []
            if context.location:
                entities.append((context.location, "Location"))
            for char in context.characters:
                entities.append((char, "Character"))
            
            template_vars["kg_context"] = self._get_knowledge_graph_context(entities)
        
        # Add vector memory context if needed
        if "vector_context" in template.variables:
            query = f"{context.game_name} {context.chapter_title or ''} {context.beat_title or ''}"
            template_vars["vector_context"] = self._get_vector_memory_context(
                query, 
                location=context.location
            )
        
        # Add any additional kwargs
        template_vars.update(kwargs)
        
        # Format the template
        try:
            system_message, user_message = template.format(**template_vars)
        except ValueError as e:
            logger.error(f"Error formatting template: {e}")
            return f"Error: Missing required template variables - {e}"
        
        # Generate the response
        response = self._generate_with_ai(
            system_message=system_message,
            user_message=user_message,
            max_tokens=template.max_tokens,
            temperature=template.temperature
        )
        
        # Store in vector database
        self._store_narrative(response, context, response_type)
        
        # Update knowledge graph if appropriate
        self._update_knowledge_graph(response, context, response_type)
        
        return response
    
    def _store_narrative(
        self,
        text: str,
        context: NarrativeContext,
        response_type: ResponseType
    ):
        """Store generated narrative in vector database"""
        try:
            # Prepare related entities
            related_entities = []
            if context.location:
                related_entities.append((context.location, "Location"))
            for char in context.characters:
                related_entities.append((char, "Character"))
            
            # Determine importance based on response type
            importance_map = {
                ResponseType.GAME_INTRO: 10,
                ResponseType.CHAPTER_INTRO: 8,
                ResponseType.BEAT_NARRATIVE: 7,
                ResponseType.GM_RESPONSE: 6,
                ResponseType.NPC_DIALOGUE: 5,
                ResponseType.SCENE_DESCRIPTION: 5,
                ResponseType.ACTION_OUTCOME: 6
            }
            importance = importance_map.get(response_type, 5)
            
            # Store in vector database
            self.context_manager.add_narrative_memory(
                text=text,
                source="ai_generated",
                related_entities=related_entities,
                location=context.location,
                importance=importance,
                tags=[response_type.value, context.game_name] + context.themes
            )
            
            logger.info(f"Stored {response_type.value} narrative in vector database")
        
        except Exception as e:
            logger.error(f"Error storing narrative: {e}")
    
    def _update_knowledge_graph(
        self,
        text: str,
        context: NarrativeContext,
        response_type: ResponseType
    ):
        """Update knowledge graph based on generated narrative"""
        if not hasattr(self.context_manager, 'kg_manager') or not self.context_manager.kg_connected:
            return
        
        try:
            # Create event for significant narratives
            if response_type in [ResponseType.GAME_INTRO, ResponseType.CHAPTER_INTRO, ResponseType.BEAT_NARRATIVE]:
                event = Event(
                    name=f"{response_type.value}_{datetime.now().isoformat()}",
                    description=text[:500],  # Store first 500 chars as description
                    event_type=response_type.value,
                    date=datetime.now().isoformat(),
                    participants=context.characters if context.characters else [],
                    locations=[context.location] if context.location else [],
                    consequences=[],
                    importance=8
                )
                self.context_manager.kg_manager.create_event(event)
                
                logger.info(f"Created {response_type.value} event in knowledge graph")
        
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")
    
    def generate_game_intro(
        self,
        game_name: str,
        description: str,
        genre: str,
        themes: List[str],
        tone: str,
        world_setting: str,
        style: NarrativeStyle = NarrativeStyle.DRAMATIC
    ) -> str:
        """Generate a game introduction narrative"""
        context = NarrativeContext(
            game_name=game_name,
            themes=themes,
            style=style,
            mood=tone
        )
        
        return self.generate_narrative(
            ResponseType.GAME_INTRO,
            context,
            game_name=game_name,
            description=description,
            genre=genre,
            themes=", ".join(themes),
            tone=tone,
            world_setting=world_setting,
            style=style.value
        )
    
    def generate_gm_response(
        self,
        context: NarrativeContext,
        player_action: str,
        character_name: str,
        scene_description: str
    ) -> str:
        """Generate a GM response to player action"""
        return self.generate_narrative(
            ResponseType.GM_RESPONSE,
            context,
            player_action=player_action,
            character_name=character_name,
            scene_description=scene_description
        )
    
    def generate_npc_dialogue(
        self,
        context: NarrativeContext,
        npc_name: str,
        npc_description: str,
        npc_personality: str,
        situation: str,
        player_input: str,
        npc_knowledge: str = "",
        npc_goals: str = ""
    ) -> str:
        """Generate NPC dialogue"""
        return self.generate_narrative(
            ResponseType.NPC_DIALOGUE,
            context,
            npc_name=npc_name,
            npc_description=npc_description,
            npc_personality=npc_personality,
            situation=situation,
            player_input=player_input,
            npc_knowledge=npc_knowledge,
            npc_goals=npc_goals
        )


# Example usage and testing
if __name__ == "__main__":
    # Initialize generator
    generator = EnhancedNarrativeGenerator(
        llm_service="openai",
        llm_model="gpt-4"
    )
    
    # Test game introduction
    intro = generator.generate_game_intro(
        game_name="Chronicles of the Void",
        description="A space opera RPG set in a dying galaxy",
        genre="Science Fiction",
        themes=["survival", "hope", "sacrifice", "discovery"],
        tone="dark but hopeful",
        world_setting="The last inhabited systems of the Andromeda galaxy",
        style=NarrativeStyle.EPIC
    )
    print("Game Introduction:")
    print(intro)
    print("\n" + "="*80 + "\n")
    
    # Test GM response
    context = NarrativeContext(
        game_name="Chronicles of the Void",
        chapter_title="The Last Station",
        beat_title="Arrival at Haven",
        location="Haven Station Docking Bay",
        characters=["Captain Zara", "Engineer Krix", "Navigator Ela"],
        recent_events=["Ship damaged by asteroid field", "Low on fuel"],
        themes=["survival", "hope"],
        mood="tense",
        style=NarrativeStyle.GRITTY
    )
    
    response = generator.generate_gm_response(
        context=context,
        player_action="I scan the station for life signs and energy readings",
        character_name="Captain Zara",
        scene_description="The docking bay is eerily quiet, emergency lights casting red shadows"
    )
    print("GM Response:")
    print(response)