"""
Tracked Stock Model (Association Table)
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class TrackedStock(Base):
    __tablename__ = "tracked_stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    custom_alert_threshold = Column(Float, nullable=True)  # User-specific threshold
    baseline_price = Column(Float, nullable=True)  # Price when tracking started (for cumulative change calculation)
    is_active = Column(String(1), default="Y", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tracked_stocks")
    stock = relationship("Stock", back_populates="tracked_by")
    
    # Ensure a user can only track a stock once
    __table_args__ = (
        UniqueConstraint('user_id', 'stock_id', name='uq_user_stock'),
    )




