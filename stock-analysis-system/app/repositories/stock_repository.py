"""
Stock Repository
"""
from sqlalchemy.orm import Session
from typing import List, Optional

# TODO: Import models
# from app.models.stock import Stock
# from app.models.tracked_stock import TrackedStock

class StockRepository:
    """
    Repository for Stock data access
    """
    
    def __init__(self, db: Session):
        """
        Initialize Stock Repository
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, stock_data):
        """
        Create new stock
        
        Args:
            stock_data: Stock data
            
        Returns:
            Created stock
        """
        # TODO: Create stock object
        # TODO: Add to database
        # TODO: Commit and refresh
        # TODO: Return stock
        pass
    
    def get_by_symbol(self, symbol: str):
        """
        Get stock by symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock object or None
        """
        # TODO: Query stock by symbol
        # TODO: Return stock
        pass
    
    def get_by_id(self, stock_id: int):
        """
        Get stock by ID
        
        Args:
            stock_id: Stock ID
            
        Returns:
            Stock object or None
        """
        # TODO: Query stock by ID
        # TODO: Return stock
        pass
    
    def search(self, query: str):
        """
        Search stocks
        
        Args:
            query: Search query
            
        Returns:
            List of matching stocks
        """
        # TODO: Search by symbol or name
        # TODO: Return results
        pass
    
    def add_tracked_stock(self, user_id: int, stock_id: int):
        """
        Add stock to user's tracking list
        
        Args:
            user_id: User ID
            stock_id: Stock ID
            
        Returns:
            TrackedStock object
        """
        # TODO: Create TrackedStock object
        # TODO: Add to database
        # TODO: Commit and return
        pass
    
    def remove_tracked_stock(self, user_id: int, stock_id: int):
        """
        Remove stock from user's tracking list
        
        Args:
            user_id: User ID
            stock_id: Stock ID
        """
        # TODO: Find TrackedStock
        # TODO: Delete from database
        # TODO: Commit
        pass
    
    def get_tracked_stocks(self, user_id: int):
        """
        Get all stocks tracked by user
        
        Args:
            user_id: User ID
            
        Returns:
            List of stocks
        """
        # TODO: Query tracked stocks for user
        # TODO: Return stock list
        pass





