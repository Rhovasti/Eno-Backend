from sqlalchemy import Column, String, Text, Float
from .base import EntityBase

class Location(EntityBase):
    """
    Model for a location entity.
    """
    __tablename__ = 'locations'
    
    # Additional Location specific fields
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    location_type = Column(String(100))  # Wilderness, Citystate or Soulsphere
    valley = Column(String(100))  # Night, Dawn, Day or Dusk
    
    def __init__(self, **kwargs):
        """
        Initialize a Location object.
        
        Args:
            **kwargs: Keyword arguments for location attributes
        """
        # Set specific type for locations
        kwargs['specific_type'] = 'Location'
        super().__init__(**kwargs)