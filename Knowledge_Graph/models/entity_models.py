from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

@dataclass
class Entity:
    """Base class for all knowledge graph entities"""
    name: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to a dictionary for Neo4j"""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

@dataclass
class Character(Entity):
    """Character entity for the knowledge graph"""
    race: str = ""
    culture: str = ""
    occupation: str = ""
    status: str = "alive"
    age: Optional[int] = None
    gender: str = ""
    traits: List[str] = field(default_factory=list)
    appearance: str = ""
    motivations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        character_dict = {
            "race": self.race,
            "culture": self.culture,
            "occupation": self.occupation,
            "status": self.status,
            "gender": self.gender,
            "appearance": self.appearance,
            "traits": ",".join(self.traits),
            "motivations": ",".join(self.motivations)
        }
        
        if self.age is not None:
            character_dict["age"] = self.age
            
        return {**base_dict, **character_dict}

@dataclass
class Location(Entity):
    """Location entity for the knowledge graph"""
    region: str = ""
    type: str = ""  # city, town, forest, etc.
    climate: str = ""
    population: Optional[int] = None
    resources: List[str] = field(default_factory=list)
    dangers: List[str] = field(default_factory=list)
    culture: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        location_dict = {
            "region": self.region,
            "type": self.type,
            "climate": self.climate,
            "culture": self.culture,
            "resources": ",".join(self.resources),
            "dangers": ",".join(self.dangers)
        }
        
        if self.population is not None:
            location_dict["population"] = self.population
            
        return {**base_dict, **location_dict}

@dataclass
class Event(Entity):
    """Event entity for the knowledge graph"""
    event_type: str = ""  # battle, celebration, catastrophe, etc.
    date: str = ""
    participants: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    consequences: List[str] = field(default_factory=list)
    importance: int = 1  # 1-10 scale of historical importance
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        event_dict = {
            "event_type": self.event_type,
            "date": self.date,
            "participants": ",".join(self.participants),
            "locations": ",".join(self.locations),
            "consequences": ",".join(self.consequences),
            "importance": self.importance
        }
            
        return {**base_dict, **event_dict}

@dataclass
class Faction(Entity):
    """Faction entity for the knowledge graph"""
    faction_type: str = ""  # government, guild, religion, etc.
    leader: str = ""
    headquarters: str = ""
    goals: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)
    allies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        faction_dict = {
            "faction_type": self.faction_type,
            "leader": self.leader,
            "headquarters": self.headquarters,
            "goals": ",".join(self.goals),
            "values": ",".join(self.values),
            "enemies": ",".join(self.enemies),
            "allies": ",".join(self.allies)
        }
            
        return {**base_dict, **faction_dict}

@dataclass
class Item(Entity):
    """Item entity for the knowledge graph"""
    item_type: str = ""  # weapon, artifact, tool, etc.
    owner: str = ""
    origin: str = ""
    powers: List[str] = field(default_factory=list)
    value: Optional[int] = None
    condition: str = "good"
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        item_dict = {
            "item_type": self.item_type,
            "owner": self.owner,
            "origin": self.origin,
            "powers": ",".join(self.powers),
            "condition": self.condition
        }
        
        if self.value is not None:
            item_dict["value"] = self.value
            
        return {**base_dict, **item_dict}

@dataclass
class Concept(Entity):
    """Concept entity for the knowledge graph - ideas, technologies, magic systems, etc."""
    concept_type: str = ""  # technology, magic, law, philosophy, etc.
    origins: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    practitioners: List[str] = field(default_factory=list)
    impact: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        concept_dict = {
            "concept_type": self.concept_type,
            "origins": ",".join(self.origins),
            "related_concepts": ",".join(self.related_concepts),
            "practitioners": ",".join(self.practitioners),
            "impact": self.impact
        }
            
        return {**base_dict, **concept_dict}