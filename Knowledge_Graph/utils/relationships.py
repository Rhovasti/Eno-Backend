from enum import Enum
from typing import Dict, Any

class RelationshipType(str, Enum):
    """Enumeration of relationship types for the knowledge graph"""
    
    # Character Relationships
    KNOWS = "KNOWS"
    MEMBER_OF = "MEMBER_OF"
    LEADS = "LEADS"
    ALLIED_WITH = "ALLIED_WITH"
    HOSTILE_TO = "HOSTILE_TO"
    RELATED_TO = "RELATED_TO"
    DESCENDED_FROM = "DESCENDED_FROM"
    SERVES = "SERVES"
    
    # Location Relationships
    LOCATED_IN = "LOCATED_IN"
    BORDERS = "BORDERS"
    TRADE_WITH = "TRADE_WITH"
    CONTROLS = "CONTROLS"
    TRAVELED_TO = "TRAVELED_TO"
    
    # Events
    PARTICIPATED_IN = "PARTICIPATED_IN"
    WITNESSED = "WITNESSED"
    CAUSED = "CAUSED"
    OCCURRED_AT = "OCCURRED_AT"
    
    # Items
    OWNS = "OWNS"
    CREATED = "CREATED"
    USES = "USES"
    STORED_AT = "STORED_AT"
    
    # Factions
    CONTROLS_FACTION = "CONTROLS_FACTION"
    AT_WAR_WITH = "AT_WAR_WITH"
    TRADING_WITH = "TRADING_WITH"
    ALLIED_WITH_FACTION = "ALLIED_WITH_FACTION"
    SUPPORTS = "SUPPORTS"
    
    # Concepts
    PRACTICES = "PRACTICES"
    DISCOVERED = "DISCOVERED"
    TEACHES = "TEACHES"
    RELATED_TO_CONCEPT = "RELATED_TO_CONCEPT"

def create_relationship_properties(relationship_type: RelationshipType, **kwargs) -> Dict[str, Any]:
    """
    Create properties for a relationship based on its type.
    
    Args:
        relationship_type: The type of relationship
        **kwargs: Additional properties for the relationship
        
    Returns:
        Dictionary of relationship properties
    """
    properties = {}
    
    # Add basic properties common to all relationships
    if 'since' in kwargs:
        properties['since'] = kwargs.pop('since')
    
    if 'strength' in kwargs:
        properties['strength'] = kwargs.pop('strength')
    
    # Add type-specific properties
    if relationship_type == RelationshipType.KNOWS:
        if 'relationship' in kwargs:
            properties['relationship'] = kwargs.pop('relationship')
        if 'trust_level' in kwargs:
            properties['trust_level'] = kwargs.pop('trust_level')
    
    elif relationship_type == RelationshipType.MEMBER_OF:
        if 'role' in kwargs:
            properties['role'] = kwargs.pop('role')
        if 'joined_date' in kwargs:
            properties['joined_date'] = kwargs.pop('joined_date')
    
    elif relationship_type == RelationshipType.HOSTILE_TO:
        if 'reason' in kwargs:
            properties['reason'] = kwargs.pop('reason')
        if 'conflict_type' in kwargs:
            properties['conflict_type'] = kwargs.pop('conflict_type')
    
    elif relationship_type == RelationshipType.ALLIED_WITH:
        if 'treaty_terms' in kwargs:
            properties['treaty_terms'] = kwargs.pop('treaty_terms')
        if 'treaty_date' in kwargs:
            properties['treaty_date'] = kwargs.pop('treaty_date')
    
    elif relationship_type == RelationshipType.PARTICIPATED_IN:
        if 'role' in kwargs:
            properties['role'] = kwargs.pop('role')
        if 'outcome' in kwargs:
            properties['outcome'] = kwargs.pop('outcome')
    
    elif relationship_type == RelationshipType.OWNS:
        if 'acquisition_method' in kwargs:
            properties['acquisition_method'] = kwargs.pop('acquisition_method')
        if 'acquisition_date' in kwargs:
            properties['acquisition_date'] = kwargs.pop('acquisition_date')
    
    # Add any remaining kwargs as properties
    properties.update(kwargs)
    
    return properties