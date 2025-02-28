import dspy
import random
import re
from typing import List, Dict, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

# ====== MEMORY COMPONENT DATA STRUCTURES ======

@dataclass
class GameMetadata:
    game_system: str = "Pathfinder Second Edition"
    source_books: List[str] = field(default_factory=list)
    theme: str = "High Fantasy"
    tonality: str = "Whimsical & Heroic"
    
@dataclass
class CharacterState:
    name: str = ""
    race: str = ""
    class_name: str = ""
    level: int = 1
    health: Dict[str, int] = field(default_factory=lambda: {"current": 0, "max": 0})
    experience: int = 0
    status_effects: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    abilities: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    currency: Dict[str, int] = field(default_factory=dict)
    
@dataclass
class WorldState:
    current_location: str = ""
    time: Dict[str, Union[str, int]] = field(default_factory=lambda: {
        "hour": 0, 
        "day": 1, 
        "month": 1, 
        "year": 1232, 
        "season": "summer"
    })
    weather: str = ""
    events: List[Dict[str, str]] = field(default_factory=list)
    visited_locations: Set[str] = field(default_factory=set)

@dataclass
class NPC:
    id: str
    name: str
    race: str
    occupation: str
    description: str
    location: str
    relationship: Dict[str, str] = field(default_factory=dict)  # Character name to relationship
    disposition: int = 0  # -100 to 100 scale
    secrets: List[Dict[str, str]] = field(default_factory=list)
    inventory: List[str] = field(default_factory=list)
    history_with_player: str = ""
    dialogue_style: str = ""
    
@dataclass
class QuestState:
    id: str
    title: str
    description: str
    status: str  # "active", "completed", "failed"
    steps: List[Dict[str, str]] = field(default_factory=list)
    rewards: Dict[str, Union[int, str]] = field(default_factory=dict)
    related_npcs: List[str] = field(default_factory=list)
    
@dataclass
class StoryThread:
    id: str
    description: str
    status: str  # "active", "resolved", "abandoned"
    importance: int  # 1-10 scale
    related_quests: List[str] = field(default_factory=list)
    related_npcs: List[str] = field(default_factory=list)
    
@dataclass
class GameAction:
    description: str
    brilliance_level: int  # 1-10 scale
    danger_level: int  # 1-10 scale
    requires_roll: bool = False
    skill_check: Optional[str] = None
    difficulty_class: Optional[int] = None

# ====== MAIN MEMORY SYSTEM ======

class NarrativeMemory(dspy.Module):
    def __init__(self):
        super().__init__()
        
        # Game state
        self.metadata = GameMetadata()
        self.character = CharacterState()
        self.world = WorldState()
        self.npcs = {}  # id -> NPC
        self.quests = {}  # id -> QuestState
        self.story_threads = {}  # id -> StoryThread
        self.interaction_history = []
        
        # Memory modules
        self.context_manager = dspy.ChainOfThought("context_management")
        self.npc_manager = dspy.ChainOfThought("npc_management")
        self.quest_manager = dspy.ChainOfThought("quest_management")
        self.story_manager = dspy.ChainOfThought("story_management")
        self.action_generator = dspy.ChainOfThought("action_generation")
        self.dice_roller = dspy.ChainOfThought("dice_rolling")
        self.narrative_generator = dspy.ChainOfThought("narrative_generation")
        
        # LLM predictors for specific tasks
        self.summarizer = SummarizationPredictor()
        self.relationship_analyzer = RelationshipPredictor()
        self.memory_pruner = MemoryPruningPredictor()
        self.status_updater = StatusUpdatePredictor()
        
    def forward(self, player_input: str) -> Dict:
        # Parse player input
        parsed_input = self.parse_player_input(player_input)
        
        # Update game state based on input
        updated_state = self.update_game_state(parsed_input)
        
        # Generate narrative response
        narrative_response = self.generate_narrative_response(updated_state)
        
        # Update memory with new information
        self.update_memory(parsed_input, narrative_response)
        
        # Prune and optimize memory
        self.optimize_memory()
        
        return {
            "narrative_response": narrative_response,
            "character_state": self.character,
            "world_state": self.world,
            "available_actions": self.generate_available_actions()
        }
    
    def parse_player_input(self, player_input: str) -> Dict:
        # Extract character speech ("like this")
        speech_pattern = r'"([^"]*)"'
        character_speech = re.findall(speech_pattern, player_input)
        
        # Extract OOC commands (<like this>)
        ooc_pattern = r'<([^>]*)>'
        ooc_commands = re.findall(ooc_pattern, player_input)
        
        # Extract actions {like this}
        action_pattern = r'{([^}]*)}'
        character_actions = re.findall(action_pattern, player_input)
        
        # Regular input (everything else)
        regular_input = re.sub(speech_pattern, '', player_input)
        regular_input = re.sub(ooc_pattern, '', regular_input)
        regular_input = re.sub(action_pattern, '', regular_input)
        regular_input = regular_input.strip()
        
        return {
            "character_speech": character_speech,
            "ooc_commands": ooc_commands,
            "character_actions": character_actions,
            "regular_input": regular_input
        }
    
    def update_game_state(self, parsed_input: Dict) -> Dict:
        # Process character actions
        for action in parsed_input.get("character_actions", []):
            self.process_character_action(action)
        
        # Process OOC commands
        for command in parsed_input.get("ooc_commands", []):
            self.process_ooc_command(command)
        
        # Update time if needed
        self.advance_time_if_needed(parsed_input)
        
        # Check for triggered events
        triggered_events = self.check_for_triggered_events()
        
        # Update character status
        self.update_character_status()
        
        # Update NPC relationships based on interactions
        self.update_npc_relationships(parsed_input)
        
        # Return the updated state
        return {
            "character": self.character,
            "world": self.world,
            "triggered_events": triggered_events,
            "parsed_input": parsed_input
        }
    
    def generate_narrative_response(self, state: Dict) -> str:
        # Generate base narrative response
        narrative = self.narrative_generator(
            character=state["character"],
            world=state["world"],
            triggered_events=state["triggered_events"],
            player_input=state["parsed_input"]
        )
        
        # Generate available actions
        available_actions = self.generate_available_actions()
        
        # Format the response according to guidelines
        formatted_response = self.format_response(narrative, available_actions)
        
        # Ensure length requirements (1000-3000 characters)
        formatted_response = self.ensure_length_requirements(formatted_response)
        
        return formatted_response
    
    def update_memory(self, parsed_input: Dict, narrative_response: str) -> None:
        # Add to interaction history
        self.interaction_history.append({
            "timestamp": datetime.now(),
            "player_input": parsed_input,
            "system_response": narrative_response
        })
        
        # Update context map
        context_updates = self.context_manager(
            interaction_history=self.interaction_history[-5:],  # Last 5 interactions
            current_world=self.world,
            current_character=self.character
        )
        
        # Update knowledge state
        knowledge_updates = self.summarizer(
            new_content=narrative_response,
            current_world=self.world,
            current_character=self.character,
            current_npcs=self.npcs
        )
        
        # Apply updates
        self.apply_context_updates(context_updates)
        self.apply_knowledge_updates(knowledge_updates)
    
    def optimize_memory(self) -> None:
        # Prune irrelevant information
        pruning_results = self.memory_pruner(
            interaction_history=self.interaction_history,
            current_quests=self.quests,
            current_story_threads=self.story_threads,
            current_npcs=self.npcs
        )
        
        # Apply pruning
        self.apply_memory_pruning(pruning_results)
        
        # Compress repeated patterns
        self.compress_patterns()
        
        # Archive resolved threads
        self.archive_resolved_threads()
    
    def generate_available_actions(self) -> List[GameAction]:
        # Generate 5 potential actions
        actions = self.action_generator(
            character=self.character,
            world=self.world,
            location=self.world.current_location,
            npcs=[npc for npc in self.npcs.values() if npc.location == self.world.current_location]
        )
        
        # Ensure one action is brilliant, ridiculous, or dangerous
        self.ensure_special_action(actions)
        
        return actions
    
    def process_character_action(self, action: str) -> None:
        # Check if action requires dice roll
        if self.action_requires_roll(action):
            result = self.dice_roller(action=action, character=self.character)
            self.apply_roll_result(result)
        else:
            # Process standard action
            self.apply_standard_action(action)
    
    def process_ooc_command(self, command: str) -> None:
        # Process commands like character sheet request, etc.
        if "character sheet" in command.lower():
            # Will be handled by the response formatter
            pass
        elif "time skip" in command.lower():
            # Extract time to skip
            self.process_time_skip(command)
    
    def format_response(self, narrative: str, available_actions: List[GameAction]) -> str:
        # Format character status
        status = self.format_character_status()
        
        # Format narrative text
        formatted_narrative = self.format_narrative_text(narrative)
        
        # Format available actions as numbered list with {}
        actions_text = self.format_available_actions(available_actions)
        
        # Combine all elements
        response = f"{status}\n\n{formatted_narrative}\n\n{actions_text}"
        
        return response
    
    def ensure_length_requirements(self, response: str) -> str:
        # Check if response is within 1000-3000 characters
        if len(response) < 1000:
            # Expand narrative with more details
            return self.expand_narrative(response)
        elif len(response) > 3000:
            # Trim narrative while preserving key elements
            return self.trim_narrative(response)
        return response

# ====== PREDICTOR IMPLEMENTATIONS ======

class SummarizationPredictor(dspy.Predictor):
    def forward(self, new_content: str, current_world: WorldState, 
                current_character: CharacterState, current_npcs: Dict[str, NPC]) -> Dict:
        # Implement summarization logic
        return {
            "world_updates": {},
            "character_updates": {},
            "npc_updates": {},
            "key_insights": []
        }

class RelationshipPredictor(dspy.Predictor):
    def forward(self, character_speech: List[str], character_actions: List[str], 
                target_npc: NPC) -> Dict:
        # Implement relationship analysis logic
        return {
            "disposition_change": 0,
            "relationship_update": "",
            "new_secrets_revealed": []
        }

class MemoryPruningPredictor(dspy.Predictor):
    def forward(self, interaction_history: List, current_quests: Dict, 
                current_story_threads: Dict, current_npcs: Dict) -> Dict:
        # Implement memory pruning logic
        return {
            "prune_interactions": [],
            "prune_npcs": [],
            "prune_quests": [],
            "prune_story_threads": []
        }

class StatusUpdatePredictor(dspy.Predictor):
    def forward(self, character: CharacterState, world: WorldState, 
                recent_actions: List[str]) -> Dict:
        # Implement status update logic
        return {
            "status_line": "",
            "condition_updates": [],
            "stat_changes": {}
        }

class DiceRollPredictor(dspy.Predictor):
    def forward(self, action: str, skill: str, difficulty: int, 
                character_bonus: int) -> Dict:
        # Implement dice rolling logic for Pathfinder 2e
        roll = random.randint(1, 20)
        total = roll + character_bonus
        success_level = self.determine_success_level(roll, total, difficulty)
        
        return {
            "roll": roll,
            "total": total,
            "difficulty": difficulty,
            "success_level": success_level,
            "description": f"({roll} + {character_bonus} = {total} vs DC {difficulty})"
        }
    
    def determine_success_level(self, roll, total, difficulty):
        if roll == 20 or total >= difficulty + 10:
            return "critical_success"
        elif roll == 1 or total <= difficulty - 10:
            return "critical_failure"
        elif total >= difficulty:
            return "success"
        else:
            return "failure"

class NarrativeGenerationPredictor(dspy.Predictor):
    def forward(self, character: CharacterState, world: WorldState, 
                location_description: str, active_npcs: List[NPC], 
                recent_events: List[Dict]) -> Dict:
        # Implement narrative generation logic
        return {
            "description": "",
            "npc_dialogue": {},
            "atmosphere": "",
            "hooks": [],
            "complete_narrative": ""
        }

# ====== PIPELINE CONFIGURATION ======

def create_narrative_gaming_pipeline():
    memory = NarrativeMemory()
    
    # Configure pipeline
    pipeline = dspy.Pipeline(
        memory,
        predictor_configs={
            "context_management": dspy.PredictorConfig(
                predictor_class=dspy.ChainOfThought,
                config={"max_tokens": 1024}
            ),
            "npc_management": dspy.PredictorConfig(
                predictor_class=dspy.ChainOfThought,
                config={"max_tokens": 1024}
            ),
            "quest_management": dspy.PredictorConfig(
                predictor_class=dspy.ChainOfThought,
                config={"max_tokens": 1024}
            ),
            "story_management": dspy.PredictorConfig(
                predictor_class=dspy.ChainOfThought,
                config={"max_tokens": 1024}
            ),
            "action_generation": dspy.PredictorConfig(
                predictor_class=dspy.ChainOfThought,
                config={"max_tokens": 1024}
            ),
            "dice_rolling": dspy.PredictorConfig(
                predictor_class=DiceRollPredictor,
                config={"max_tokens": 512}
            ),
            "narrative_generation": dspy.PredictorConfig(
                predictor_class=NarrativeGenerationPredictor,
                config={"max_tokens": 2048}
            ),
        }
    )
    
    return pipeline

# ====== USAGE EXAMPLE ======

def initialize_game():
    pipeline = create_narrative_gaming_pipeline()
    
    # Initialize game state
    memory = pipeline.modules[0]
    memory.metadata = GameMetadata(
        game_system="Pathfinder Second Edition",
        source_books=["Core Rulebook", "Advanced Player's Guide"],
        theme="High Fantasy",
        tonality="Whimsical & Heroic"
    )
    
    memory.character = CharacterState(
        name="Sabrina",
        race="halfling",
        class_name="rogue",
        level=1,
        health={"current": 16, "max": 16},
        inventory=["clothes", "small purse"],
        currency={"gold": 1}
    )
    
    memory.world = WorldState(
        current_location="hometown",
        time={"hour": 8, "day": 1, "month": 6, "year": 1232, "season": "summer"},
        weather="clear skies"
    )
    
    # Generate initial game state response
    initial_state = pipeline(player_input="<Start game>")
    
    return pipeline, initial_state

def game_loop(pipeline, player_input):
    response = pipeline(player_input=player_input)
    return response
