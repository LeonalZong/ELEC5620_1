"""
Portfolio Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.schemas.stock import Stock


class PortfolioBase(BaseModel):
    """Base portfolio schema"""
    stock_id: int
    quantity: float = Field(..., gt=0, description="Number of shares (must be positive)")
    purchase_price: float = Field(..., gt=0, description="Purchase price per share (must be positive)")
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    """Schema for creating a portfolio entry"""
    pass


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio entry"""
    quantity: Optional[float] = Field(None, gt=0)
    purchase_price: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None


class Portfolio(PortfolioBase):
    """Schema for portfolio response"""
    id: int
    user_id: int
    stock: Optional[Stock] = None
    
    # Calculated fields (optional, will be computed on demand)
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    cost_basis: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    """Schema for portfolio summary statistics"""
    total_holdings: int = 0
    total_cost_basis: float = 0.0
    total_value: float = 0.0
    total_profit_loss: float = 0.0
    total_profit_loss_pct: float = 0.0
    today_gain: float = 0.0
    today_gain_pct: float = 0.0
    active_alerts: int = 0




