"""
Stock Data Model (Price History)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class StockData(Base):
    __tablename__ = "stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    adjusted_close = Column(Float, nullable=True)
    data_source = Column(String(50), default="API", nullable=False)  # API, CSV, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    stock = relationship("Stock", back_populates="stock_data")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_stock_timestamp', 'stock_id', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),  # For time-based queries
    )




