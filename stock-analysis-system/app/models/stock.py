"""
Stock Model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    sector = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    exchange = Column(String(20), nullable=True)  # NYSE, NASDAQ, etc.
    is_active = Column(String(1), default="Y", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_data = relationship("StockData", back_populates="stock", cascade="all, delete-orphan")
    news = relationship("News", back_populates="stock", cascade="all, delete-orphan")
    tracked_by = relationship("TrackedStock", back_populates="stock", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="stock", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="stock", cascade="all, delete-orphan")




