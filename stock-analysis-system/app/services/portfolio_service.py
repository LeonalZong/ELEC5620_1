"""
Portfolio Service
Business logic for portfolio operations (tracking only, no actual trading)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import logging

from app.schemas.portfolio import Portfolio, PortfolioCreate, PortfolioUpdate, PortfolioSummary
from app.models.portfolio import Portfolio as PortfolioModel
from app.models.stock import Stock as StockModel
from app.models.alert import Alert as AlertModel, AlertStatus
from app.models.stock_data import StockData as StockDataModel
from app.services.monitoring_service import MonitoringService


class PortfolioService:
    """
    Service for portfolio operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.monitoring_service = MonitoringService()
        self.logger = logging.getLogger("portfolio_service")
    
    async def add_holding(self, user_id: int, portfolio_data: PortfolioCreate) -> Portfolio:
        """
        Add a new stock holding to user's portfolio
        
        Args:
            user_id: User ID
            portfolio_data: Portfolio creation data
            
        Returns:
            Created portfolio entry
        """
        try:
            # Check if stock exists
            stock = self.db.query(StockModel).filter(StockModel.id == portfolio_data.stock_id).first()
            if not stock:
                raise ValueError(f"Stock with ID {portfolio_data.stock_id} not found")
            
            # Check if user already has this stock in portfolio
            existing = self.db.query(PortfolioModel).filter(
                and_(
                    PortfolioModel.user_id == user_id,
                    PortfolioModel.stock_id == portfolio_data.stock_id
                )
            ).first()
            
            if existing:
                raise ValueError(f"Stock {stock.symbol} is already in your portfolio. Use update to modify.")
            
            # Create new portfolio entry
            portfolio = PortfolioModel(
                user_id=user_id,
                stock_id=portfolio_data.stock_id,
                quantity=portfolio_data.quantity,
                purchase_price=portfolio_data.purchase_price,
                purchase_date=portfolio_data.purchase_date or datetime.utcnow(),
                notes=portfolio_data.notes
            )
            
            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)
            
            self.logger.info(f"Added {portfolio_data.quantity} shares of {stock.symbol} to user {user_id}'s portfolio")
            
            return await self._enrich_portfolio(portfolio)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to add holding: {str(e)}")
            raise Exception(f"Failed to add holding: {str(e)}")
    
    async def get_user_portfolio(self, user_id: int) -> List[Portfolio]:
        """
        Get all holdings in user's portfolio
        
        Args:
            user_id: User ID
            
        Returns:
            List of portfolio entries with current values
        """
        try:
            holdings = self.db.query(PortfolioModel).filter(
                PortfolioModel.user_id == user_id
            ).all()
            
            result = []
            for holding in holdings:
                enriched = await self._enrich_portfolio(holding)
                result.append(enriched)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get user portfolio: {str(e)}")
            raise Exception(f"Failed to get user portfolio: {str(e)}")
    
    async def update_holding(self, user_id: int, portfolio_id: int, update_data: PortfolioUpdate) -> Portfolio:
        """
        Update a portfolio holding
        
        Args:
            user_id: User ID
            portfolio_id: Portfolio entry ID
            update_data: Update data
            
        Returns:
            Updated portfolio entry
        """
        try:
            holding = self.db.query(PortfolioModel).filter(
                and_(
                    PortfolioModel.id == portfolio_id,
                    PortfolioModel.user_id == user_id
                )
            ).first()
            
            if not holding:
                raise ValueError(f"Portfolio entry {portfolio_id} not found")
            
            # Update fields
            if update_data.quantity is not None:
                holding.quantity = update_data.quantity
            if update_data.purchase_price is not None:
                holding.purchase_price = update_data.purchase_price
            if update_data.notes is not None:
                holding.notes = update_data.notes
            
            holding.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(holding)
            
            self.logger.info(f"Updated portfolio entry {portfolio_id} for user {user_id}")
            
            return await self._enrich_portfolio(holding)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to update holding: {str(e)}")
            raise Exception(f"Failed to update holding: {str(e)}")
    
    async def delete_holding(self, user_id: int, portfolio_id: int) -> None:
        """
        Delete a portfolio holding
        
        Args:
            user_id: User ID
            portfolio_id: Portfolio entry ID
        """
        try:
            holding = self.db.query(PortfolioModel).filter(
                and_(
                    PortfolioModel.id == portfolio_id,
                    PortfolioModel.user_id == user_id
                )
            ).first()
            
            if not holding:
                raise ValueError(f"Portfolio entry {portfolio_id} not found")
            
            self.db.delete(holding)
            self.db.commit()
            
            self.logger.info(f"Deleted portfolio entry {portfolio_id} for user {user_id}")
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to delete holding: {str(e)}")
            raise Exception(f"Failed to delete holding: {str(e)}")
    
    async def get_portfolio_summary(self, user_id: int) -> PortfolioSummary:
        """
        Get portfolio summary with calculated values
        
        Args:
            user_id: User ID
            
        Returns:
            Portfolio summary with total value, profit/loss, etc.
        """
        try:
            holdings = await self.get_user_portfolio(user_id)
            
            total_cost_basis = 0.0
            total_value = 0.0
            total_profit_loss = 0.0
            
            for holding in holdings:
                total_cost_basis += holding.cost_basis or 0.0
                total_value += holding.current_value or 0.0
                total_profit_loss += holding.profit_loss or 0.0
            
            # Calculate percentages
            total_profit_loss_pct = 0.0
            if total_cost_basis > 0:
                total_profit_loss_pct = (total_profit_loss / total_cost_basis) * 100
            
            # Compute today's gain based on previous close vs latest close per holding
            yesterday_total_value = 0.0
            today_total_value = 0.0
            try:
                for holding in self.db.query(PortfolioModel).filter(PortfolioModel.user_id == user_id).all():
                    # Fetch last two closing prices (latest first)
                    prices = self.db.query(StockDataModel).filter(
                        StockDataModel.stock_id == holding.stock_id
                    ).order_by(StockDataModel.timestamp.desc()).limit(2).all()
                    if len(prices) >= 2:
                        latest_close = float(prices[0].close_price)
                        prev_close = float(prices[1].close_price)
                    elif len(prices) == 1:
                        latest_close = float(prices[0].close_price)
                        prev_close = float(prices[0].close_price)
                    else:
                        # Fall back to current price and purchase price if no history
                        latest_close = float(holding.stock.current_price or holding.purchase_price)
                        prev_close = float(holding.stock.current_price or holding.purchase_price)
                    today_total_value += holding.quantity * latest_close
                    yesterday_total_value += holding.quantity * prev_close
            except Exception as e:
                self.logger.warning(f"Failed to compute today's gain from history: {str(e)}")
                yesterday_total_value = 0.0
                today_total_value = total_value
            
            today_gain_amount = today_total_value - yesterday_total_value if yesterday_total_value > 0 else 0.0
            today_gain_pct = (today_gain_amount / yesterday_total_value * 100) if yesterday_total_value > 0 else 0.0
            
            # Get active alerts count
            active_alerts = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.user_id == user_id,
                    AlertModel.status.in_([AlertStatus.PENDING, AlertStatus.TRIGGERED])
                )
            ).count()
            
            return PortfolioSummary(
                total_holdings=len(holdings),
                total_cost_basis=total_cost_basis,
                total_value=total_value,
                total_profit_loss=total_profit_loss,
                total_profit_loss_pct=total_profit_loss_pct,
                today_gain=today_gain_amount,
                today_gain_pct=today_gain_pct,
                active_alerts=active_alerts
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get portfolio summary: {str(e)}")
            raise Exception(f"Failed to get portfolio summary: {str(e)}")
    
    async def _enrich_portfolio(self, holding: PortfolioModel) -> Portfolio:
        """
        Enrich portfolio entry with current prices and calculated values
        
        Args:
            holding: Portfolio model instance
            
        Returns:
            Enriched portfolio schema
        """
        try:
            # Get current price
            current_price = await self.monitoring_service.get_current_price(holding.stock.symbol)
            if current_price is None:
                current_price = holding.stock.current_price or holding.purchase_price
            
            # Calculate values
            current_value = holding.calculate_current_value(current_price)
            cost_basis = holding.calculate_cost_basis()
            profit_loss = holding.calculate_profit_loss(current_price)
            profit_loss_pct = holding.calculate_profit_loss_pct(current_price)
            
            # Build stock schema
            from app.schemas.stock import Stock as StockSchema
            stock_schema = StockSchema(
                id=holding.stock.id,
                symbol=holding.stock.symbol,
                name=holding.stock.name,
                sector=holding.stock.sector,
                industry=holding.stock.industry,
                market_cap=holding.stock.market_cap,
                current_price=current_price,
                currency=holding.stock.currency,
                exchange=holding.stock.exchange,
                is_active=holding.stock.is_active == "1",
                created_at=holding.stock.created_at.isoformat(),
                updated_at=holding.stock.updated_at.isoformat()
            )
            
            return Portfolio(
                id=holding.id,
                user_id=holding.user_id,
                stock_id=holding.stock_id,
                quantity=holding.quantity,
                purchase_price=holding.purchase_price,
                purchase_date=holding.purchase_date,
                notes=holding.notes,
                stock=stock_schema,
                current_price=current_price,
                current_value=current_value,
                cost_basis=cost_basis,
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct,
                created_at=holding.created_at,
                updated_at=holding.updated_at
            )
            
        except Exception as e:
            self.logger.error(f"Failed to enrich portfolio: {str(e)}")
            # Return basic portfolio without enrichment
            from app.schemas.stock import Stock as StockSchema
            stock_schema = StockSchema(
                id=holding.stock.id,
                symbol=holding.stock.symbol,
                name=holding.stock.name,
                sector=holding.stock.sector,
                industry=holding.stock.industry,
                market_cap=holding.stock.market_cap,
                current_price=holding.stock.current_price,
                currency=holding.stock.currency,
                exchange=holding.stock.exchange,
                is_active=holding.stock.is_active == "1",
                created_at=holding.stock.created_at.isoformat(),
                updated_at=holding.stock.updated_at.isoformat()
            )
            
            return Portfolio(
                id=holding.id,
                user_id=holding.user_id,
                stock_id=holding.stock_id,
                quantity=holding.quantity,
                purchase_price=holding.purchase_price,
                purchase_date=holding.purchase_date,
                notes=holding.notes,
                stock=stock_schema,
                created_at=holding.created_at,
                updated_at=holding.updated_at
            )



