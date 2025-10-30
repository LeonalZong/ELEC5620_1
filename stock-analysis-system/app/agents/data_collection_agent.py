"""
Data Collection Agent
Collects stock data, news, and market information
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from app.agents.base_agent import BaseAgent
from app.external.stock_api_client import StockAPIClient
from app.external.news_api_client import NewsAPIClient
from app.services.ai_analysis_service import AIAnalysisService
from app.models.news import News as NewsModel
from app.models.stock_data import StockData as StockDataModel
from app.models.stock import Stock as StockModel

class DataCollectionAgent(BaseAgent):
    """
    Agent responsible for collecting data from external sources
    """
    
    def __init__(self, agent_id: str = "data_collection", db=None):
        """
        Initialize Data Collection Agent
        
        Args:
            agent_id: Agent identifier
            db: Database session
        """
        super().__init__(agent_id, "Data Collection Agent")
        self.db = db
        self.stock_api_client = StockAPIClient()
        self.news_api_client = NewsAPIClient()
        self.ai_service = AIAnalysisService()
        self.db = db
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute data collection task
        
        Args:
            task_data: Task parameters including stock symbol
            
        Returns:
            Collected data
        """
        symbol = task_data.get("symbol")
        if not symbol:
            raise ValueError("Stock symbol is required")
        
        # Collect data in parallel
        tasks = [
            self.collect_stock_data(symbol),
            self.collect_news_data(symbol),
            self.collect_market_data()
        ]
        
        stock_data, news_data, market_data = await asyncio.gather(*tasks)
        
        # Validate data quality
        if not self.validate_data_quality(stock_data):
            raise ValueError("Invalid stock data quality")
        
        # Store data in database if db session is available
        if self.db:
            try:
                # Get or create stock record
                stock_id = self.get_or_create_stock(symbol)
                
                if stock_id:
                    # Store news data
                    if news_data:
                        self.store_news_data(news_data, stock_id)
                    
                    # Store historical stock data
                    historical_data = stock_data.get("historical_data", [])
                    if historical_data:
                        self.store_stock_data(historical_data, stock_id)
                    
                    # Commit the transaction
                    if self.db:
                        self.db.commit()
                        self.logger.info(f"Successfully stored and committed data for {symbol}")
                    else:
                        self.logger.info(f"Successfully stored data for {symbol} (no db session)")
                
            except Exception as e:
                if self.db:
                    self.db.rollback()
                self.logger.error(f"Failed to store data for {symbol}: {str(e)}")
        
        return {
            "symbol": symbol,
            "stock_data": stock_data,
            "news_data": news_data,
            "market_data": market_data,
            "collected_at": datetime.utcnow().isoformat(),
            "data_quality": "valid",
            "stored_in_db": self.db is not None
        }
    
    async def collect_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Collect stock price and volume data
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock data dictionary
        """
        try:
            # Get current price and basic info
            current_data = await self.stock_api_client.get_current_price(symbol)
            
            # Get historical data (last 30 days)
            historical_data = await self.stock_api_client.get_historical_data(
                symbol, period="30d"
            )
            
            # Calculate multi-timeframe price changes
            price_analysis = self.calculate_multi_timeframe_changes(current_data, historical_data)
            
            return {
                "symbol": symbol,
                "current_price": current_data.get("price", 0),
                "price_change": price_analysis.get("daily_change", 0),
                "price_change_percent": price_analysis.get("daily_change_percent", 0),
                "short_term_change": price_analysis.get("short_term_change", 0),
                "short_term_change_percent": price_analysis.get("short_term_change_percent", 0),
                "medium_term_change": price_analysis.get("medium_term_change", 0),
                "medium_term_change_percent": price_analysis.get("medium_term_change_percent", 0),
                "long_term_change": price_analysis.get("long_term_change", 0),
                "long_term_change_percent": price_analysis.get("long_term_change_percent", 0),
                "trend_analysis": price_analysis.get("trend_analysis", {}),
                "volume": current_data.get("volume", 0),
                "market_cap": current_data.get("market_cap", 0),
                "historical_data": historical_data,
                "last_updated": current_data.get("last_updated", datetime.utcnow().isoformat())
            }
        except Exception as e:
            self.logger.error(f"Failed to collect stock data for {symbol}: {str(e)}")
            return {"symbol": symbol, "error": str(e)}
    
    async def collect_news_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Collect news articles related to stock
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of news articles
        """
        try:
            # Get news articles
            news_articles = await self.news_api_client.get_stock_news(symbol, limit=10)
            
            # Process and format news
            processed_news = []
            for article in news_articles:
                processed_news.append({
                    "title": article.get("title", ""),
                    "content": article.get("content", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("published_at", ""),
                    "source": article.get("source", ""),
                    "sentiment": article.get("sentiment", "neutral"),
                    "relevance_score": article.get("relevance_score", 0.5)
                })
            
            return processed_news
        except Exception as e:
            self.logger.error(f"Failed to collect news data for {symbol}: {str(e)}")
            return []
    
    async def collect_market_data(self) -> Dict[str, Any]:
        """
        Collect general market data
        
        Returns:
            Market data dictionary
        """
        try:
            # Get market indices
            market_indices = await self.stock_api_client.get_market_indices()
            
            # Get market sentiment using AI
            market_sentiment = await self.ai_service.get_market_sentiment()
            
            return {
                "indices": market_indices,
                "sentiment": market_sentiment,
                "market_status": "open" if datetime.utcnow().hour < 16 else "closed",
                "collected_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to collect market data: {str(e)}")
            return {"error": str(e)}
    
    def calculate_multi_timeframe_changes(self, current_data: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate price changes across multiple timeframes
        
        Args:
            current_data: Current stock data
            historical_data: Historical price data
            
        Returns:
            Multi-timeframe price analysis
        """
        current_price = current_data.get("price", 0)
        
        if not historical_data or len(historical_data) < 2:
            return {
                "daily_change": 0,
                "daily_change_percent": 0,
                "short_term_change": 0,
                "short_term_change_percent": 0,
                "medium_term_change": 0,
                "medium_term_change_percent": 0,
                "long_term_change": 0,
                "long_term_change_percent": 0,
                "trend_analysis": {
                    "short_term_trend": "NEUTRAL",
                    "medium_term_trend": "NEUTRAL",
                    "long_term_trend": "NEUTRAL"
                }
            }
        
        # Daily change (1 day)
        previous_price = historical_data[-2].get("close", current_price)
        daily_change = current_price - previous_price
        daily_change_percent = (daily_change / previous_price) * 100 if previous_price > 0 else 0
        
        # Short-term change (7 days)
        short_term_price = self.get_price_n_days_ago(historical_data, 7)
        short_term_change = current_price - short_term_price
        short_term_change_percent = (short_term_change / short_term_price) * 100 if short_term_price > 0 else 0
        
        # Medium-term change (14 days)
        medium_term_price = self.get_price_n_days_ago(historical_data, 14)
        medium_term_change = current_price - medium_term_price
        medium_term_change_percent = (medium_term_change / medium_term_price) * 100 if medium_term_price > 0 else 0
        
        # Long-term change (28 days)
        long_term_price = self.get_price_n_days_ago(historical_data, 28)
        long_term_change = current_price - long_term_price
        long_term_change_percent = (long_term_change / long_term_price) * 100 if long_term_price > 0 else 0
        
        # Trend analysis
        trend_analysis = self.analyze_trends(historical_data)
        
        return {
            "daily_change": round(daily_change, 2),
            "daily_change_percent": round(daily_change_percent, 2),
            "short_term_change": round(short_term_change, 2),
            "short_term_change_percent": round(short_term_change_percent, 2),
            "medium_term_change": round(medium_term_change, 2),
            "medium_term_change_percent": round(medium_term_change_percent, 2),
            "long_term_change": round(long_term_change, 2),
            "long_term_change_percent": round(long_term_change_percent, 2),
            "trend_analysis": trend_analysis
        }
    
    def get_price_n_days_ago(self, historical_data: List[Dict[str, Any]], days: int) -> float:
        """
        Get price from N days ago
        
        Args:
            historical_data: Historical price data
            days: Number of days ago
            
        Returns:
            Price from N days ago
        """
        if len(historical_data) <= days:
            return historical_data[0].get("close", 0) if historical_data else 0
        
        return historical_data[-days-1].get("close", 0)
    
    def analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Analyze price trends across different timeframes
        
        Args:
            historical_data: Historical price data
            
        Returns:
            Trend analysis for different timeframes
        """
        if len(historical_data) < 7:
            return {
                "short_term_trend": "NEUTRAL",
                "medium_term_trend": "NEUTRAL",
                "long_term_trend": "NEUTRAL"
            }
        
        # Short-term trend (7 days)
        short_term_trend = self.calculate_trend(historical_data, 7)
        
        # Medium-term trend (14 days)
        medium_term_trend = self.calculate_trend(historical_data, 14)
        
        # Long-term trend (28 days)
        long_term_trend = self.calculate_trend(historical_data, 28)
        
        return {
            "short_term_trend": short_term_trend,
            "medium_term_trend": medium_term_trend,
            "long_term_trend": long_term_trend
        }
    
    def calculate_trend(self, historical_data: List[Dict[str, Any]], days: int) -> str:
        """
        Calculate trend for a specific timeframe
        
        Args:
            historical_data: Historical price data
            days: Number of days to analyze
            
        Returns:
            Trend direction (UP, DOWN, NEUTRAL)
        """
        if len(historical_data) < days:
            return "NEUTRAL"
        
        # Get prices for the last N days
        recent_prices = [day.get("close", 0) for day in historical_data[-days:]]
        
        if len(recent_prices) < 2:
            return "NEUTRAL"
        
        # Calculate trend using linear regression slope
        x = list(range(len(recent_prices)))
        y = recent_prices
        
        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return "NEUTRAL"
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        # Determine trend based on slope
        if slope > 0.1:
            return "UP"
        elif slope < -0.1:
            return "DOWN"
        else:
            return "NEUTRAL"
    
    def validate_data_quality(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected data quality
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid
        """
        if not data or "error" in data:
            return False
        
        # Check required fields
        required_fields = ["symbol", "current_price"]
        for field in required_fields:
            if field not in data:
                return False
        
        # Check data ranges
        price = data.get("current_price", 0)
        if price <= 0 or price > 1000000:  # Reasonable price range
            return False
        
        # Check data freshness (should be within last hour)
        last_updated = data.get("last_updated")
        if last_updated:
            try:
                updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                if datetime.utcnow() - updated_time > timedelta(hours=1):
                    return False
            except:
                return False
        
        return True
    
    def store_news_data(self, news_articles: List[Dict[str, Any]], stock_id: int) -> None:
        """
        Store news articles in database
        
        Args:
            news_articles: List of news articles
            stock_id: Stock ID
        """
        if not self.db or not news_articles:
            return
        
        try:
            for article in news_articles:
                # Check if article already exists
                existing_news = self.db.query(NewsModel).filter(
                    NewsModel.stock_id == stock_id,
                    NewsModel.title == article.get('title', ''),
                    NewsModel.url == article.get('url', '')
                ).first()
                
                if not existing_news:
                    news = NewsModel(
                        stock_id=stock_id,
                        title=article.get('title', ''),
                        content=article.get('content', ''),
                        source=article.get('source', ''),
                        url=article.get('url', ''),
                        published_at=datetime.fromisoformat(article.get('published_at', '').replace('Z', '+00:00')) if article.get('published_at') else datetime.utcnow(),
                        sentiment_score=article.get('sentiment_score', 0.0),
                        relevance_score=article.get('relevance_score', 0.8),
                        impact_score=article.get('impact_score', 0.5),
                        category=article.get('category', 'general'),
                        created_at=datetime.utcnow()
                    )
                    self.db.add(news)
            
            # Note: commit is handled by the context manager
            self.logger.info(f"Stored {len(news_articles)} news articles for stock {stock_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to store news data: {str(e)}")
    
    def store_stock_data(self, historical_data: List[Dict[str, Any]], stock_id: int) -> None:
        """
        Store historical stock data in database
        
        Args:
            historical_data: List of historical price data
            stock_id: Stock ID
        """
        if not self.db or not historical_data:
            return
        
        try:
            for day_data in historical_data:
                # Check if data already exists for this date
                existing_data = self.db.query(StockDataModel).filter(
                    StockDataModel.stock_id == stock_id,
                    StockDataModel.timestamp == datetime.fromisoformat(day_data.get('date', '')).date()
                ).first()
                
                if not existing_data:
                    stock_data = StockDataModel(
                        stock_id=stock_id,
                        timestamp=datetime.fromisoformat(day_data.get('date', '')),
                        open_price=day_data.get('open', 0.0),
                        high_price=day_data.get('high', 0.0),
                        low_price=day_data.get('low', 0.0),
                        close_price=day_data.get('close', 0.0),
                        volume=day_data.get('volume', 0),
                        adjusted_close=day_data.get('adjusted_close', day_data.get('close', 0.0)),
                        data_source="API"
                    )
                    self.db.add(stock_data)
            
            # Note: commit is handled by the context manager
            self.logger.info(f"Stored {len(historical_data)} stock data records for stock {stock_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to store stock data: {str(e)}")
    
    def get_or_create_stock(self, symbol: str) -> int:
        """
        Get or create stock record and return stock_id
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock ID
        """
        if not self.db:
            return None
        
        try:
            # Check if stock exists
            stock = self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
            
            if not stock:
                # Create new stock record
                stock = StockModel(
                    symbol=symbol.upper(),
                    name=f"{symbol} Company",
                    current_price=0.0,
                    currency="USD",
                    exchange="NASDAQ",
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(stock)
                # Note: commit is handled by the context manager
                self.db.flush()  # Flush to get the ID
                self.logger.info(f"Created new stock record for {symbol}")
            
            return stock.id
            
        except Exception as e:
            self.logger.error(f"Failed to get or create stock: {str(e)}")
            return None




