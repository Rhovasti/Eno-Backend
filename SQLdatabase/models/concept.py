from sqlalchemy import Column, String, Text
from .base import EntityBase

class Concept(EntityBase):
    """
    Model for a concept entity.
    """
    __tablename__ = 'concepts'
    
    # Additional Concept specific fields
    descriptor_1 = Column(String(255))
    descriptor_2 = Column(String(255))
    descriptor_3 = Column(String(255))
    
    def __init__(self, **kwargs):
        """
        Initialize a Concept object.
        
        Args:
            **kwargs: Keyword arguments for concept attributes
        """
        # Set specific type for concepts
        kwargs['specific_type'] = 'Concept'
        super().__init__(**kwargs)