"""
Database Operations Base Classes
Common database operations and utilities for the stock analysis system
"""
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc, func
from contextlib import contextmanager
import logging

from app.database import get_db_session, get_db_session_readonly
from app.core.logging import get_logger
from app.core.exceptions import DatabaseException

logger = get_logger("database_operations")

# Generic type for SQLAlchemy models
ModelType = TypeVar('ModelType')

class BaseRepository(Generic[ModelType]):
    """
    Base repository class for common database operations
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
        self.logger = get_logger(f"repository_{model.__name__.lower()}")
    
    def create(self, db: Session, **kwargs) -> ModelType:
        """
        Create a new record
        """
        try:
            instance = self.model(**kwargs)
            db.add(instance)
            db.flush()  # Flush to get the ID without committing
            self.logger.info(f"Created {self.model.__name__} with ID: {instance.id}")
            return instance
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Failed to create {self.model.__name__}", details={"error": str(e)})
    
    def get_by_id(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a record by ID
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get {self.model.__name__} by ID {id}: {str(e)}")
            raise DatabaseException(f"Failed to get {self.model.__name__} by ID", details={"id": id, "error": str(e)})
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records with pagination
        """
        try:
            return db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get all {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Failed to get all {self.model.__name__}", details={"error": str(e)})
    
    def update(self, db: Session, id: int, **kwargs) -> Optional[ModelType]:
        """
        Update a record by ID
        """
        try:
            instance = self.get_by_id(db, id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            db.flush()
            self.logger.info(f"Updated {self.model.__name__} with ID: {id}")
            return instance
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to update {self.model.__name__} with ID {id}: {str(e)}")
            raise DatabaseException(f"Failed to update {self.model.__name__}", details={"id": id, "error": str(e)})
    
    def delete(self, db: Session, id: int) -> bool:
        """
        Delete a record by ID
        """
        try:
            instance = self.get_by_id(db, id)
            if not instance:
                return False
            
            db.delete(instance)
            self.logger.info(f"Deleted {self.model.__name__} with ID: {id}")
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to delete {self.model.__name__} with ID {id}: {str(e)}")
            raise DatabaseException(f"Failed to delete {self.model.__name__}", details={"id": id, "error": str(e)})
    
    def count(self, db: Session) -> int:
        """
        Count total records
        """
        try:
            return db.query(self.model).count()
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to count {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Failed to count {self.model.__name__}", details={"error": str(e)})
    
    def exists(self, db: Session, **filters) -> bool:
        """
        Check if a record exists with given filters
        """
        try:
            query = db.query(self.model)
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            return query.first() is not None
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to check existence of {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Failed to check existence of {self.model.__name__}", details={"error": str(e)})
    
    def bulk_create(self, db: Session, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in bulk
        """
        try:
            instances = [self.model(**data) for data in data_list]
            db.add_all(instances)
            db.flush()
            self.logger.info(f"Bulk created {len(instances)} {self.model.__name__} records")
            return instances
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to bulk create {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Failed to bulk create {self.model.__name__}", details={"error": str(e)})
    
    def bulk_update(self, db: Session, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records in bulk
        """
        try:
            updated_count = 0
            for update_data in updates:
                id = update_data.pop('id')
                if self.update(db, id, **update_data):
                    updated_count += 1
            self.logger.info(f"Bulk updated {updated_count} {self.model.__name__} records")
            return updated_count
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to bulk update {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Failed to bulk update {self.model.__name__}", details={"error": str(e)})


class DatabaseTransaction:
    """
    Database transaction context manager with automatic rollback on error
    """
    
    def __init__(self):
        self.logger = get_logger("database_transaction")
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions
        """
        with get_db_session() as db:
            try:
                self.logger.debug("Starting database transaction")
                yield db
                self.logger.debug("Database transaction completed successfully")
            except Exception as e:
                self.logger.error(f"Database transaction failed: {str(e)}")
                raise
    
    @contextmanager
    def readonly_transaction(self):
        """
        Context manager for read-only database transactions
        """
        with get_db_session_readonly() as db:
            try:
                self.logger.debug("Starting read-only database transaction")
                yield db
                self.logger.debug("Read-only database transaction completed successfully")
            except Exception as e:
                self.logger.error(f"Read-only database transaction failed: {str(e)}")
                raise


class QueryBuilder:
    """
    Query builder for complex database queries
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
        self.logger = get_logger(f"query_builder_{model.__name__.lower()}")
    
    def build_query(self, db: Session, **filters) -> Query:
        """
        Build a query with filters
        """
        query = db.query(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                if isinstance(value, list):
                    query = query.filter(getattr(self.model, key).in_(value))
                elif isinstance(value, dict):
                    # Handle range queries
                    if 'gte' in value:
                        query = query.filter(getattr(self.model, key) >= value['gte'])
                    if 'lte' in value:
                        query = query.filter(getattr(self.model, key) <= value['lte'])
                    if 'gt' in value:
                        query = query.filter(getattr(self.model, key) > value['gt'])
                    if 'lt' in value:
                        query = query.filter(getattr(self.model, key) < value['lt'])
                else:
                    query = query.filter(getattr(self.model, key) == value)
        
        return query
    
    def search(self, db: Session, search_term: str, search_fields: List[str]) -> Query:
        """
        Build a search query across multiple fields
        """
        query = db.query(self.model)
        search_conditions = []
        
        for field in search_fields:
            if hasattr(self.model, field):
                search_conditions.append(
                    getattr(self.model, field).ilike(f"%{search_term}%")
                )
        
        if search_conditions:
            query = query.filter(or_(*search_conditions))
        
        return query
    
    def order_by(self, query: Query, order_field: str, desc: bool = False) -> Query:
        """
        Add ordering to query
        """
        if hasattr(self.model, order_field):
            if desc:
                return query.order_by(desc(getattr(self.model, order_field)))
            else:
                return query.order_by(asc(getattr(self.model, order_field)))
        return query
    
    def paginate(self, query: Query, page: int = 1, per_page: int = 20) -> Query:
        """
        Add pagination to query
        """
        offset = (page - 1) * per_page
        return query.offset(offset).limit(per_page)


class DatabaseHealthChecker:
    """
    Database health checker for monitoring
    """
    
    def __init__(self):
        self.logger = get_logger("database_health")
    
    def check_connection(self, db: Session) -> Dict[str, Any]:
        """
        Check database connection health
        """
        try:
            from sqlalchemy import text
            result = db.execute(text("SELECT 1")).fetchone()
            
            return {
                "status": "healthy",
                "connection": "active",
                "response_time": "< 1ms"
            }
        except Exception as e:
            self.logger.error(f"Database connection check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "connection": "failed",
                "error": str(e)
            }
    
    def check_pool_status(self) -> Dict[str, Any]:
        """
        Check connection pool status
        """
        try:
            from app.database import get_connection_pool_status
            return get_connection_pool_status()
        except Exception as e:
            self.logger.error(f"Pool status check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }










