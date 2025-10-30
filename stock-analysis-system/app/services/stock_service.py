"""
Stock Service
Business logic for stock operations
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import logging

from app.agents.agent_manager import AgentManager
from app.schemas.stock import Stock, StockCreate, StockData, TrackStockRequest, TrackedStock
from app.models.stock import Stock as StockModel
from app.models.tracked_stock import TrackedStock as TrackedStockModel
from app.models.stock_data import StockData as StockDataModel
from app.models.user import User as UserModel
from app.external.stock_api_client import StockAPIClient

class StockService:
    """
    Service for stock-related operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_manager = AgentManager(db)
        self.stock_api_client = StockAPIClient()
        self.logger = logging.getLogger("stock_service")
    
    def add_stock(self, symbol: str, name: str, sector: str = None, industry: str = None, 
                  market_cap: float = None, current_price: float = None, 
                  currency: str = "USD", exchange: str = None) -> StockModel:
        """
        Add a new stock to the database
        
        Args:
            symbol: Stock symbol
            name: Company name
            sector: Business sector
            industry: Industry
            market_cap: Market capitalization
            current_price: Current stock price
            currency: Currency code
            exchange: Stock exchange
            
        Returns:
            Created stock model
        """
        # Check if stock already exists
        existing_stock = self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
        if existing_stock:
            raise ValueError(f"Stock {symbol} already exists")
        
        # Create new stock
        stock = StockModel(
            symbol=symbol.upper(),
            name=name,
            sector=sector,
            industry=industry,
            market_cap=market_cap,
            current_price=current_price,
            currency=currency,
            exchange=exchange,
            is_active=True
        )
        
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)
        
        self.logger.info(f"Added new stock: {symbol} - {name}")
        return stock
    
    def get_stock(self, stock_id: int) -> Optional[StockModel]:
        """
        Get stock by ID
        
        Args:
            stock_id: Stock ID
            
        Returns:
            Stock model or None
        """
        return self.db.query(StockModel).filter(StockModel.id == stock_id).first()
    
    def get_stock_by_symbol_sync(self, symbol: str) -> Optional[StockModel]:
        """
        Get stock by symbol (synchronous version)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock model or None
        """
        return self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
    
    def update_stock(self, stock_id: int, **kwargs) -> Optional[StockModel]:
        """
        Update stock information
        
        Args:
            stock_id: Stock ID
            **kwargs: Fields to update
            
        Returns:
            Updated stock model or None
        """
        stock = self.get_stock(stock_id)
        if not stock:
            return None
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(stock, key):
                setattr(stock, key, value)
        
        stock.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(stock)
        
        self.logger.info(f"Updated stock: {stock.symbol}")
        return stock
    
    def delete_stock(self, stock_id: int) -> bool:
        """
        Delete stock (soft delete)
        
        Args:
            stock_id: Stock ID
            
        Returns:
            True if deleted, False if not found
        """
        stock = self.get_stock(stock_id)
        if not stock:
            return False
        
        # Soft delete
        stock.is_active = False
        stock.updated_at = datetime.utcnow()
        self.db.commit()
        
        self.logger.info(f"Deleted stock: {stock.symbol}")
        return True
    
    def list_stocks(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[StockModel]:
        """
        List stocks with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Only return active stocks
            
        Returns:
            List of stock models
        """
        query = self.db.query(StockModel)
        
        if active_only:
            query = query.filter(StockModel.is_active == "Y")
        
        return query.offset(skip).limit(limit).all()
    
    def search_stocks_by_name(self, name: str, limit: int = 10) -> List[StockModel]:
        """
        Search stocks by name
        
        Args:
            name: Name to search for
            limit: Maximum number of results
            
        Returns:
            List of matching stocks
        """
        return self.db.query(StockModel).filter(
            and_(
                StockModel.is_active == "Y",
                StockModel.name.ilike(f"%{name}%")
            )
        ).limit(limit).all()
    
    def search_stocks_by_sector(self, sector: str, limit: int = 10) -> List[StockModel]:
        """
        Search stocks by sector
        
        Args:
            sector: Sector to search for
            limit: Maximum number of results
            
        Returns:
            List of matching stocks
        """
        return self.db.query(StockModel).filter(
            and_(
                StockModel.is_active == "Y",
                StockModel.sector.ilike(f"%{sector}%")
            )
        ).limit(limit).all()
    
    def get_tracked_stocks_by_user(self, user_id: int) -> List[TrackedStockModel]:
        """
        Get all tracked stocks for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of tracked stocks
        """
        from sqlalchemy.orm import joinedload
        
        return self.db.query(TrackedStockModel).options(
            joinedload(TrackedStockModel.stock)
        ).filter(
            and_(
                TrackedStockModel.user_id == user_id,
                TrackedStockModel.is_active == "Y"
            )
        ).all()
    
    
    async def track_stock(
        self, 
        symbol: str, 
        user_id: int, 
        custom_alert_threshold: Optional[float] = None,
        quantity: Optional[float] = None,
        purchase_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Track a stock for a user
        
        Args:
            symbol: Stock symbol to track
            user_id: User ID
            custom_alert_threshold: Custom alert threshold
            
        Returns:
            Tracking result
        """
        try:
            # Check if stock exists in database
            stock = self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
            
            if not stock:
                # Get stock info from API and create in database
                stock_data = await self.stock_api_client.get_current_price(symbol)
                if "error" in stock_data:
                    raise ValueError(f"Stock {symbol} not found: {stock_data['error']}")
                
                # Create new stock record
                stock = StockModel(
                    symbol=symbol.upper(),
                    name=stock_data.get("name", f"{symbol} Company"),
                    sector=stock_data.get("sector", "Unknown"),
                    industry=stock_data.get("industry", "Unknown"),
                    current_price=stock_data.get("price", 0),
                    currency=stock_data.get("currency", "USD"),
                    exchange=stock_data.get("exchange", "NASDAQ"),
                    market_cap=stock_data.get("market_cap", 0),
                    is_active="Y",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(stock)
                self.db.commit()
                self.db.refresh(stock)
            
            # Check if user is already tracking this stock
            existing_track = self.db.query(TrackedStockModel).filter(
                and_(
                    TrackedStockModel.user_id == user_id,
                    TrackedStockModel.stock_id == stock.id
                )
            ).first()
            
            if existing_track:
                self.logger.info(f"Found existing track for {symbol}: is_active={existing_track.is_active}, user_id={user_id}")
                if existing_track.is_active == "Y":
                    raise ValueError(f"Stock {symbol} is already being tracked")
                else:
                    # Reactivate tracking
                    self.logger.info(f"Reactivating tracking for {symbol} with threshold {custom_alert_threshold}")
                    existing_track.is_active = "Y"
                    existing_track.custom_alert_threshold = custom_alert_threshold
                    existing_track.updated_at = datetime.utcnow()
            else:
                # Create new tracking record
                tracked_stock = TrackedStockModel(
                    user_id=user_id,
                    stock_id=stock.id,
                    custom_alert_threshold=custom_alert_threshold,
                    baseline_price=stock.current_price,  # Set baseline price for cumulative change tracking
                    is_active="Y",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(tracked_stock)
            
            # Create alert record for price drop monitoring
            from app.models.alert import Alert as AlertModel, AlertType, AlertStatus
            from app.services.alert_service import AlertService
            
            alert_service = AlertService(self.db)
            threshold = custom_alert_threshold if custom_alert_threshold is not None else -5.0  # Default -5%
            
            # Create price drop alert
            alert = AlertModel(
                user_id=user_id,
                stock_id=stock.id,
                alert_type=AlertType.PRICE_DROP,
                threshold_value=threshold,
                current_value=stock.current_price,
                message=f"Price drop alert for {symbol} at {threshold}%",
                status=AlertStatus.PENDING,
                created_at=datetime.utcnow()
            )
            self.db.add(alert)
            
            # Create portfolio entry if quantity and purchase_price are provided
            portfolio_id = None
            if quantity is not None and purchase_price is not None:
                from app.models.portfolio import Portfolio as PortfolioModel
                
                # Check if portfolio entry already exists
                existing_portfolio = self.db.query(PortfolioModel).filter(
                    and_(
                        PortfolioModel.user_id == user_id,
                        PortfolioModel.stock_id == stock.id
                    )
                ).first()
                
                if existing_portfolio:
                    # Update existing portfolio
                    existing_portfolio.quantity = quantity
                    existing_portfolio.purchase_price = purchase_price
                    existing_portfolio.updated_at = datetime.utcnow()
                    portfolio_id = existing_portfolio.id
                    self.logger.info(f"Updated portfolio for {symbol}: {quantity} shares @ ${purchase_price}")
                else:
                    # Create new portfolio entry
                    portfolio = PortfolioModel(
                        user_id=user_id,
                        stock_id=stock.id,
                        quantity=quantity,
                        purchase_price=purchase_price,
                        purchase_date=datetime.utcnow()
                    )
                    self.db.add(portfolio)
                    self.db.flush()  # Get the ID
                    portfolio_id = portfolio.id
                    self.logger.info(f"Created portfolio for {symbol}: {quantity} shares @ ${purchase_price}")
            
            self.db.commit()
            
            self.logger.info(f"Created price drop alert for {symbol} with threshold {threshold}%")
            
            return {
                "symbol": symbol,
                "stock_id": stock.id,
                "custom_alert_threshold": custom_alert_threshold,
                "alert_id": alert.id,
                "portfolio_id": portfolio_id,
                "tracked_at": datetime.utcnow().isoformat(),
                "status": "tracking"
            }
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to track stock {symbol}: {str(e)}")
            raise Exception(f"Failed to track stock: {str(e)}")
    
    async def update_track_threshold(self, symbol: str, user_id: int, custom_alert_threshold: Optional[float] = None) -> None:
        """
        Update alert threshold for a tracked stock
        
        Args:
            symbol: Stock symbol
            user_id: User ID
            custom_alert_threshold: New alert threshold
        """
        try:
            # Find the stock
            stock = self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
            if not stock:
                raise ValueError(f"Stock {symbol} not found")
            
            # Find the tracking record
            tracked_stock = self.db.query(TrackedStockModel).filter(
                and_(
                    TrackedStockModel.user_id == user_id,
                    TrackedStockModel.stock_id == stock.id,
                    TrackedStockModel.is_active == "Y"
                )
            ).first()
            
            if not tracked_stock:
                raise ValueError(f"Stock {symbol} is not being tracked")
            
            # Update threshold
            tracked_stock.custom_alert_threshold = custom_alert_threshold
            tracked_stock.updated_at = datetime.utcnow()
            self.db.commit()
            
            self.logger.info(f"Updated threshold for {symbol} to {custom_alert_threshold}")
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to update threshold for {symbol}: {str(e)}")
            raise Exception(f"Failed to update threshold: {str(e)}")

    async def untrack_stock(self, symbol: str, user_id: int) -> None:
        """
        Stop tracking a stock
        
        Args:
            symbol: Stock symbol to untrack
            user_id: User ID
        """
        try:
            # Find the stock
            stock = self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
            if not stock:
                raise ValueError(f"Stock {symbol} not found")
            
            # Find the tracking record
            tracked_stock = self.db.query(TrackedStockModel).filter(
                and_(
                    TrackedStockModel.user_id == user_id,
                    TrackedStockModel.stock_id == stock.id
                )
            ).first()
            
            if not tracked_stock:
                raise ValueError(f"Stock {symbol} is not being tracked")
            
            # Deactivate tracking
            tracked_stock.is_active = "N"
            tracked_stock.updated_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to untrack stock {symbol}: {str(e)}")
            raise Exception(f"Failed to untrack stock: {str(e)}")
    
    async def get_tracked_stocks(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all tracked stocks for a user with portfolio information
        
        Args:
            user_id: User ID
            
        Returns:
            List of tracked stocks with portfolio data
        """
        try:
            from app.models.portfolio import Portfolio as PortfolioModel
            
            # Query tracked stocks with stock information
            tracked_stocks = self.db.query(TrackedStockModel).join(StockModel).filter(
                and_(
                    TrackedStockModel.user_id == user_id,
                    TrackedStockModel.is_active == "Y"
                )
            ).all()
            
            # Enhance with portfolio information
            result = []
            for tracked in tracked_stocks:
                # Get portfolio for this stock if exists
                portfolio = self.db.query(PortfolioModel).filter(
                    and_(
                        PortfolioModel.user_id == user_id,
                        PortfolioModel.stock_id == tracked.stock_id
                    )
                ).first()
                
                # Build response dict
                tracked_dict = {
                    "id": tracked.id,
                    "user_id": tracked.user_id,
                    "stock_id": tracked.stock_id,
                    "stock": tracked.stock,
                    "custom_alert_threshold": tracked.custom_alert_threshold,
                    "is_active": tracked.is_active,
                    "created_at": tracked.created_at,
                    "updated_at": tracked.updated_at,
                    "portfolio": None
                }
                
                # Add portfolio data if exists
                if portfolio:
                    current_price = tracked.stock.current_price or 0
                    tracked_dict["portfolio"] = {
                        "id": portfolio.id,
                        "quantity": portfolio.quantity,
                        "purchase_price": portfolio.purchase_price,
                        "purchase_date": portfolio.purchase_date,
                        "current_value": portfolio.calculate_current_value(current_price),
                        "cost_basis": portfolio.calculate_cost_basis(),
                        "profit_loss": portfolio.calculate_profit_loss(current_price),
                        "profit_loss_pct": portfolio.calculate_profit_loss_pct(current_price)
                    }
                
                result.append(tracked_dict)
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to get tracked stocks for user {user_id}: {str(e)}")
            raise Exception(f"Failed to get tracked stocks: {str(e)}")
    
    async def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """
        Get stock information by symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock information
        """
        try:
            # Check database first
            stock = self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
            
            if stock:
                # Update price from API if data is older than 1 hour
                if (datetime.utcnow() - stock.updated_at).seconds > 3600:
                    try:
                        current_data = await self.stock_api_client.get_current_price(symbol)
                        if "error" not in current_data:
                            stock.current_price = current_data.get("price", stock.current_price)
                            stock.updated_at = datetime.utcnow()
                            self.db.commit()
                    except Exception as e:
                        self.logger.warning(f"Failed to update price for {symbol}: {str(e)}")
                
                return Stock(
                    id=stock.id,
                    symbol=stock.symbol,
                    name=stock.name,
                    sector=stock.sector,
                    industry=stock.industry,
                    market_cap=stock.market_cap,
                    current_price=stock.current_price,
                    currency=stock.currency,
                    exchange=stock.exchange,
                    is_active=stock.is_active,
                    created_at=stock.created_at.isoformat(),
                    updated_at=stock.updated_at.isoformat()
                )
            else:
                # Get from API and create in database
                stock_data = await self.stock_api_client.get_current_price(symbol)
                if "error" in stock_data:
                    return None
                
                # Create new stock record
                new_stock = StockModel(
                    symbol=symbol.upper(),
                    name=stock_data.get("name", f"{symbol} Company"),
                    current_price=stock_data.get("price", 0),
                    currency=stock_data.get("currency", "USD"),
                    exchange=stock_data.get("exchange", "NASDAQ"),
                    market_cap=stock_data.get("market_cap", 0),
                    is_active="Y",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_stock)
                self.db.commit()
                self.db.refresh(new_stock)
                
                return Stock(
                    id=new_stock.id,
                    symbol=new_stock.symbol,
                    name=new_stock.name,
                    sector=new_stock.sector,
                    industry=new_stock.industry,
                    market_cap=new_stock.market_cap,
                    current_price=new_stock.current_price,
                    currency=new_stock.currency,
                    exchange=new_stock.exchange,
                    is_active=new_stock.is_active,
                    created_at=new_stock.created_at.isoformat(),
                    updated_at=new_stock.updated_at.isoformat()
                )
        except Exception as e:
            self.logger.error(f"Failed to get stock {symbol}: {str(e)}")
            raise Exception(f"Failed to get stock: {str(e)}")
    
    async def get_stock_data(self, symbol: str, period: str = "1d") -> List[StockData]:
        """
        Get historical stock data
        
        Args:
            symbol: Stock symbol
            period: Data period
            
        Returns:
            Historical stock data
        """
        try:
            # Get stock from database
            stock = self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
            if not stock:
                raise ValueError(f"Stock {symbol} not found")
            
            # Get historical data from API
            historical_data = await self.stock_api_client.get_historical_data(symbol, period)
            
            result = []
            for i, data_point in enumerate(historical_data):
                # Store in database for caching
                stock_data = StockDataModel(
                    stock_id=stock.id,
                    timestamp=datetime.fromisoformat(data_point["date"]),
                    open_price=data_point["open"],
                    high_price=data_point["high"],
                    low_price=data_point["low"],
                    close_price=data_point["close"],
                    volume=data_point["volume"],
                    adjusted_close=data_point["close"],
                    data_source="yahoo_finance"
                )
                self.db.add(stock_data)
                result.append(StockData(
                    id=i + 1,
                    stock_id=stock.id,
                    timestamp=stock_data.timestamp.isoformat(),
                    open_price=stock_data.open_price,
                    high_price=stock_data.high_price,
                    low_price=stock_data.low_price,
                    close_price=stock_data.close_price,
                    volume=stock_data.volume,
                    adjusted_close=stock_data.adjusted_close,
                    data_source=stock_data.data_source
                ))
            
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to get stock data for {symbol}: {str(e)}")
            raise Exception(f"Failed to get stock data: {str(e)}")
    
    async def search_stocks(self, query: str) -> List[Stock]:
        """
        Search for stocks
        
        Args:
            query: Search query
            
        Returns:
            List of matching stocks
        """
        try:
            # Search in database first
            stocks = self.db.query(StockModel).filter(
                and_(
                    StockModel.is_active == "1",  # Database stores '1' not 'Y'
                    or_(
                        StockModel.symbol.ilike(f"%{query}%"),
                        StockModel.name.ilike(f"%{query}%")
                    )
                )
            ).limit(10).all()
            
            result = []
            for stock in stocks:
                result.append(Stock(
                    id=stock.id,
                    symbol=stock.symbol,
                    name=stock.name,
                    sector=stock.sector,
                    industry=stock.industry,
                    market_cap=stock.market_cap,
                    current_price=stock.current_price,
                    currency=stock.currency,
                    exchange=stock.exchange,
                    is_active=stock.is_active,
                    created_at=stock.created_at.isoformat(),
                    updated_at=stock.updated_at.isoformat()
                ))
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to search stocks: {str(e)}")
            raise Exception(f"Failed to search stocks: {str(e)}")
    
    async def get_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get portfolio summary for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Portfolio summary
        """
        try:
            # Get tracked stocks for user
            tracked_stocks = self.get_tracked_stocks_by_user(user_id)
            
            # Calculate basic statistics
            total_value = 0.0
            for tracked in tracked_stocks:
                if tracked.stock and tracked.stock.current_price:
                    total_value += tracked.stock.current_price * 100  # Assume 100 shares
            
            # Count active alerts (PENDING + TRIGGERED)
            from app.models.alert import Alert as AlertModel, AlertStatus
            active_alerts = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.user_id == user_id,
                    AlertModel.status.in_([AlertStatus.PENDING, AlertStatus.TRIGGERED])
                )
            ).count()
            
            return {
                "total_stocks": len(tracked_stocks),
                "total_value": total_value,
                "daily_change": 0.0,
                "daily_change_percent": 0.0,
                "active_alerts": active_alerts,
                "top_performer": None,
                "worst_performer": None
            }
        except Exception as e:
            self.logger.error(f"Failed to get portfolio summary: {str(e)}")
            raise Exception(f"Failed to get portfolio summary: {str(e)}")