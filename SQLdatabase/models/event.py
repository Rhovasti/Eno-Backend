from sqlalchemy import Column, String, Text
from .base import EntityBase

class Event(EntityBase):
    """
    Model for an event entity.
    """
    __tablename__ = 'events'
    
    # Additional Event specific fields
    cycle = Column(String(100))
    
    def __init__(self, **kwargs):
        """
        Initialize an Event object.
        
        Args:
            **kwargs: Keyword arguments for event attributes
        """
        # Set specific type for events
        kwargs['specific_type'] = 'Event'
        super().__init__(**kwargs)