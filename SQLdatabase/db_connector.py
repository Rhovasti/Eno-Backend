import logging
import os
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generic
from sqlalchemy import create_engine, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker, Session, query
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime
import json

from .models.base import Base, EntityBase

# Set up logging
logging.basicConfig(
    filename='sql_database.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Type for entity models
T = TypeVar('T', bound=EntityBase)

class SQLDatabaseConnector:
    """
    Main connector class for the SQL database.
    Handles connections, queries, and mutations.
    """
    
    def __init__(
        self, 
        database_url: Optional[str] = None,
        echo: bool = False
    ):
        """
        Initialize the SQL database connection.
        
        Args:
            database_url: SQLAlchemy database URL (e.g., sqlite:///game_data.db)
            echo: Whether to echo SQL statements (for debugging)
        """
        # Default to SQLite if no URL is provided
        if database_url is None:
            database_url = "sqlite:///game_data.db"
            
        try:
            # Initialize engine and session
            self.engine = create_engine(database_url, echo=echo)
            self.Session = sessionmaker(bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            logging.info(f"Successfully connected to SQL database at {database_url}")
        except Exception as e:
            logging.error(f"Failed to connect to SQL database: {e}")
            raise
    
    def add_entity(self, entity: T) -> T:
        """
        Add a new entity to the database.
        
        Args:
            entity: Entity to add
            
        Returns:
            The added entity with ID
        """
        try:
            session = self.Session()
            session.add(entity)
            session.commit()
            
            # Refresh to get the ID
            session.refresh(entity)
            
            logging.info(f"Added {entity.__class__.__name__} with ID {entity.id}: {entity.name}")
            return entity
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding entity: {e}")
            raise
        finally:
            session.close()
    
    def get_entity_by_id(self, model_class: Type[T], entity_id: int) -> Optional[T]:
        """
        Get an entity by its ID.
        
        Args:
            model_class: Entity model class
            entity_id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            session = self.Session()
            entity = session.query(model_class).filter(model_class.id == entity_id).first()
            return entity
        except Exception as e:
            logging.error(f"Error getting entity by ID: {e}")
            raise
        finally:
            session.close()
    
    def get_entity_by_uid(self, model_class: Type[T], uid: str) -> Optional[T]:
        """
        Get an entity by its UID.
        
        Args:
            model_class: Entity model class
            uid: Entity UID
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            session = self.Session()
            entity = session.query(model_class).filter(model_class.uid == uid).first()
            return entity
        except Exception as e:
            logging.error(f"Error getting entity by UID: {e}")
            raise
        finally:
            session.close()
    
    def get_entity_by_name(self, model_class: Type[T], name: str) -> Optional[T]:
        """
        Get an entity by its name.
        
        Args:
            model_class: Entity model class
            name: Entity name
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            session = self.Session()
            entity = session.query(model_class).filter(model_class.name == name).first()
            return entity
        except Exception as e:
            logging.error(f"Error getting entity by name: {e}")
            raise
        finally:
            session.close()
    
    def update_entity(self, entity: T, data: Dict[str, Any]) -> T:
        """
        Update an entity with new data.
        
        Args:
            entity: Entity to update
            data: Dictionary of attributes to update
            
        Returns:
            Updated entity
        """
        try:
            session = self.Session()
            
            # Get the entity if it's not attached to a session
            if not session.is_active:
                entity = session.merge(entity)
            
            # Update the entity
            entity.update_from_dict(data)
            session.commit()
            
            logging.info(f"Updated {entity.__class__.__name__} with ID {entity.id}: {entity.name}")
            return entity
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating entity: {e}")
            raise
        finally:
            session.close()
    
    def delete_entity(self, entity: T) -> bool:
        """
        Delete an entity from the database.
        
        Args:
            entity: Entity to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.Session()
            
            # Get the entity if it's not attached to a session
            if not session.is_active:
                entity = session.merge(entity)
            
            # Delete the entity
            session.delete(entity)
            session.commit()
            
            logging.info(f"Deleted {entity.__class__.__name__} with ID {entity.id}: {entity.name}")
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting entity: {e}")
            return False
        finally:
            session.close()
    
    def query_entities(
        self, 
        model_class: Type[T], 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Query entities with optional filters and sorting.
        
        Args:
            model_class: Entity model class
            filters: Dictionary of attribute filters
            order_by: Attribute to order by
            order_desc: Whether to order in descending order
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of matching entities
        """
        try:
            session = self.Session()
            q = session.query(model_class)
            
            # Apply filters
            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    if hasattr(model_class, key):
                        filter_clauses.append(getattr(model_class, key) == value)
                
                if filter_clauses:
                    q = q.filter(and_(*filter_clauses))
            
            # Apply ordering
            if order_by and hasattr(model_class, order_by):
                order_column = getattr(model_class, order_by)
                if order_desc:
                    q = q.order_by(desc(order_column))
                else:
                    q = q.order_by(asc(order_column))
            
            # Apply limit and offset
            if limit is not None:
                q = q.limit(limit)
            if offset is not None:
                q = q.offset(offset)
            
            # Execute query
            entities = q.all()
            
            logging.info(f"Queried {len(entities)} {model_class.__name__} entities")
            return entities
        except Exception as e:
            logging.error(f"Error querying entities: {e}")
            raise
        finally:
            session.close()
    
    def search_entities(
        self, 
        model_class: Type[T], 
        search_term: str,
        search_fields: List[str] = ['name', 'description'],
        limit: int = 20
    ) -> List[T]:
        """
        Search entities by text in specified fields.
        
        Args:
            model_class: Entity model class
            search_term: Text to search for
            search_fields: Fields to search in
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        try:
            session = self.Session()
            q = session.query(model_class)
            
            # Build search filters
            search_filters = []
            for field in search_fields:
                if hasattr(model_class, field):
                    search_filters.append(getattr(model_class, field).like(f"%{search_term}%"))
            
            # Apply search filters
            if search_filters:
                q = q.filter(or_(*search_filters))
            
            # Apply limit
            q = q.limit(limit)
            
            # Execute query
            entities = q.all()
            
            logging.info(f"Searched for '{search_term}' in {model_class.__name__}, found {len(entities)} results")
            return entities
        except Exception as e:
            logging.error(f"Error searching entities: {e}")
            raise
        finally:
            session.close()
    
    def get_all_entities(self, model_class: Type[T], limit: Optional[int] = None) -> List[T]:
        """
        Get all entities of a specific type.
        
        Args:
            model_class: Entity model class
            limit: Optional limit on number of results
            
        Returns:
            List of entities
        """
        try:
            session = self.Session()
            q = session.query(model_class)
            
            if limit is not None:
                q = q.limit(limit)
            
            entities = q.all()
            
            logging.info(f"Retrieved {len(entities)} {model_class.__name__} entities")
            return entities
        except Exception as e:
            logging.error(f"Error getting all entities: {e}")
            raise
        finally:
            session.close()
    
    def count_entities(self, model_class: Type[T], filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities with optional filters.
        
        Args:
            model_class: Entity model class
            filters: Dictionary of attribute filters
            
        Returns:
            Count of matching entities
        """
        try:
            session = self.Session()
            q = session.query(model_class)
            
            # Apply filters
            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    if hasattr(model_class, key):
                        filter_clauses.append(getattr(model_class, key) == value)
                
                if filter_clauses:
                    q = q.filter(and_(*filter_clauses))
            
            # Count entities
            count = q.count()
            
            logging.info(f"Counted {count} {model_class.__name__} entities")
            return count
        except Exception as e:
            logging.error(f"Error counting entities: {e}")
            raise
        finally:
            session.close()
    
    def export_entities(self, model_class: Type[T], output_file: str) -> bool:
        """
        Export all entities of a specific type to a JSON file.
        
        Args:
            model_class: Entity model class
            output_file: Path to output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entities = self.get_all_entities(model_class)
            entity_dicts = [entity.to_dict() for entity in entities]
            
            with open(output_file, 'w') as f:
                json.dump(entity_dicts, f, indent=2)
            
            logging.info(f"Exported {len(entities)} {model_class.__name__} entities to {output_file}")
            return True
        except Exception as e:
            logging.error(f"Error exporting entities: {e}")
            return False
    
    def import_entities(self, model_class: Type[T], input_file: str) -> List[T]:
        """
        Import entities from a JSON file.
        
        Args:
            model_class: Entity model class
            input_file: Path to input file
            
        Returns:
            List of imported entities
        """
        try:
            with open(input_file, 'r') as f:
                entity_dicts = json.load(f)
            
            imported_entities = []
            for entity_dict in entity_dicts:
                # Remove ID to let the database assign a new one
                if 'id' in entity_dict:
                    del entity_dict['id']
                
                entity = model_class(**entity_dict)
                self.add_entity(entity)
                imported_entities.append(entity)
            
            logging.info(f"Imported {len(imported_entities)} {model_class.__name__} entities from {input_file}")
            return imported_entities
        except Exception as e:
            logging.error(f"Error importing entities: {e}")
            raise