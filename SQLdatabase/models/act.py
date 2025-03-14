from sqlalchemy import Column, String, Text
from .base import EntityBase

class Act(EntityBase):
    """
    Model for an act entity.
    """
    __tablename__ = 'acts'
    
    # Additional Act specific fields
    subject = Column(String(255))
    object = Column(String(255))
    verb = Column(String(100))
    preposition = Column(String(100))
    adjective = Column(String(100))
    
    def __init__(self, **kwargs):
        """
        Initialize an Act object.
        
        Args:
            **kwargs: Keyword arguments for act attributes
        """
        # Set specific type for acts
        kwargs['specific_type'] = 'Act'
        super().__init__(**kwargs)