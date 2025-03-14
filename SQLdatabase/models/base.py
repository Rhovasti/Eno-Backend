from typing import Any, Dict, List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class EntityBase(Base):
    """
    Base class for all entities in the database.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    specific_type = Column(String(100), nullable=False)
    domain = Column(String(100))
    subdomain = Column(String(100))
    seed = Column(String(255))
    
    # Function attributes
    imperative = Column(String(100))
    ethos = Column(String(100))
    root = Column(String(100))
    manner = Column(String(100))
    aspects = Column(Text)
    qualia = Column(Text)
    soulscape = Column(Text)
    
    # Form attributes
    legacy = Column(String(255))
    crest = Column(String(255))
    archetype = Column(String(100))
    persona = Column(String(100))
    personality_type = Column(String(100))
    description = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to dictionary.
        
        Returns:
            Dictionary representation of the entity
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update entity from dictionary.
        
        Args:
            data: Dictionary of attributes to update
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()