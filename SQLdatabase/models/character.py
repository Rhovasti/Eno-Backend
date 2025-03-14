from sqlalchemy import Column, String, Text
from .base import EntityBase

class Character(EntityBase):
    """
    Model for a character entity.
    """
    __tablename__ = 'characters'
    
    # Additional Character specific fields
    birth_cycle = Column(String(100))
    reproductive_type = Column(String(100))
    culture = Column(String(255))
    traits = Column(Text)
    demeanor = Column(Text)
    
    def __init__(self, **kwargs):
        """
        Initialize a Character object.
        
        Args:
            **kwargs: Keyword arguments for character attributes
        """
        # Set specific type for characters
        kwargs['specific_type'] = 'Character'
        super().__init__(**kwargs)