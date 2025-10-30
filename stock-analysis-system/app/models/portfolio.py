"""
Portfolio Model
Stores user's stock holdings for tracking purposes (no actual trading)
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Portfolio(Base):
    """
    Portfolio model for tracking user's stock holdings
    This is for tracking/calculation only, not actual trading
    """
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    
    # Holding information
    quantity = Column(Float, nullable=False)  # Number of shares
    purchase_price = Column(Float, nullable=False)  # Price per share when purchased
    purchase_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Notes (optional)
    notes = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolio")
    stock = relationship("Stock")
    
    def calculate_current_value(self, current_price: float) -> float:
        """Calculate current market value of this holding"""
        return self.quantity * current_price
    
    def calculate_profit_loss(self, current_price: float) -> float:
        """Calculate profit/loss in dollars"""
        return (current_price - self.purchase_price) * self.quantity
    
    def calculate_profit_loss_pct(self, current_price: float) -> float:
        """Calculate profit/loss percentage"""
        if self.purchase_price == 0:
            return 0.0
        return ((current_price - self.purchase_price) / self.purchase_price) * 100
    
    def calculate_cost_basis(self) -> float:
        """Calculate total cost basis (amount invested)"""
        return self.quantity * self.purchase_price




