"""
Smart Alert Service
Intelligent alert triggering with pattern analysis
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.database import get_db_session
from app.models.alert import Alert as AlertModel, AlertStatus, AlertType
from app.models.stock_data import StockData as StockDataModel
from app.services.ai_analysis_service import AIAnalysisService
from app.external.stock_api_client import StockAPIClient

logger = logging.getLogger(__name__)

class SmartAlertService:
    """Smart alert service with intelligent triggering logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.stock_api = StockAPIClient()
        self.ai_service = AIAnalysisService()
    
    async def check_smart_alerts(self) -> Dict[str, int]:
        """
        Check all pending alerts with smart triggering logic
        Returns statistics about alerts processed
        """
        try:
            # Get all pending alerts
            pending_alerts = self.db.query(AlertModel).filter(
                AlertModel.status == AlertStatus.PENDING
            ).all()
            
            self.logger.info(f"Checking {len(pending_alerts)} pending alerts with smart logic")
            
            stats = {
                "checked": 0,
                "triggered": 0,
                "skipped": 0,
                "errors": 0
            }
            
            for alert in pending_alerts:
                try:
                    stats["checked"] += 1
                    
                    # Check if alert should be triggered
                    should_trigger, analysis_data = await self._analyze_alert_pattern(alert)
                    
                    if should_trigger:
                        # Trigger the alert with analysis
                        await self._trigger_alert_with_analysis(alert, analysis_data)
                        stats["triggered"] += 1
                        self.logger.info(f"Smart alert triggered for {alert.stock.symbol}")
                    else:
                        stats["skipped"] += 1
                        self.logger.debug(f"Alert for {alert.stock.symbol} not triggered - conditions not met")
                        
                except Exception as e:
                    stats["errors"] += 1
                    self.logger.error(f"Error checking alert {alert.id}: {str(e)}")
            
            self.db.commit()
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in smart alert checking: {str(e)}")
            self.db.rollback()
            raise
    
    async def _analyze_alert_pattern(self, alert: AlertModel) -> Tuple[bool, Dict]:
        """
        Analyze alert pattern to determine if it should be triggered
        Returns (should_trigger, analysis_data)
        """
        try:
            symbol = alert.stock.symbol
            threshold = alert.threshold_value
            
            # Get historical price data for pattern analysis
            price_data = await self._get_historical_prices(symbol, days=7)
            
            if not price_data or len(price_data) < 3:
                return False, {}
            
            # Analyze price pattern
            analysis = self._analyze_price_pattern(price_data, threshold)
            
            # Smart triggering conditions
            should_trigger = self._evaluate_trigger_conditions(analysis, threshold)
            
            return should_trigger, analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing pattern for {alert.stock.symbol}: {str(e)}")
            return False, {}
    
    def _analyze_price_pattern(self, price_data: List[Dict], threshold: float) -> Dict:
        """Analyze price pattern for smart triggering"""
        if len(price_data) < 3:
            return {}
        
        prices = [float(p['close']) for p in price_data]
        volumes = [int(p.get('volume', 0)) for p in price_data]
        
        # Calculate metrics
        current_price = prices[0]
        previous_price = prices[1]
        week_ago_price = prices[-1] if len(prices) > 6 else prices[-1]
        
        # Daily changes
        daily_changes = []
        for i in range(len(prices) - 1):
            change = ((prices[i] - prices[i+1]) / prices[i+1]) * 100
            daily_changes.append(change)
        
        # Pattern analysis
        consecutive_drops = 0
        total_drop = 0
        max_drop = 0
        
        for change in daily_changes:
            if change < 0:  # Price drop
                consecutive_drops += 1
                total_drop += abs(change)
                max_drop = max(max_drop, abs(change))
            else:
                consecutive_drops = 0
        
        # Volume analysis
        avg_volume = sum(volumes) / len(volumes)
        recent_volume = volumes[0] if volumes else 0
        volume_spike = (recent_volume / avg_volume) if avg_volume > 0 else 1
        
        # Overall trend
        week_change = ((current_price - week_ago_price) / week_ago_price) * 100
        
        return {
            "current_price": current_price,
            "daily_change": daily_changes[0] if daily_changes else 0,
            "week_change": week_change,
            "consecutive_drops": consecutive_drops,
            "total_drop_percent": total_drop,
            "max_single_drop": max_drop,
            "volume_spike": volume_spike,
            "price_volatility": self._calculate_volatility(prices),
            "trend_strength": self._calculate_trend_strength(prices)
        }
    
    def _evaluate_trigger_conditions(self, analysis: Dict, threshold: float) -> bool:
        """Evaluate if alert should be triggered based on smart conditions"""
        if not analysis:
            return False
        
        # Condition 1: Significant single-day drop
        if analysis.get("daily_change", 0) <= threshold * 2:  # 2x threshold for single day
            return True
        
        # Condition 2: Multiple consecutive drops with cumulative effect
        consecutive_drops = analysis.get("consecutive_drops", 0)
        total_drop = analysis.get("total_drop_percent", 0)
        
        if consecutive_drops >= 3 and total_drop >= abs(threshold) * 1.5:
            return True
        
        # Condition 3: Gradual decline over week with volume spike
        week_change = analysis.get("week_change", 0)
        volume_spike = analysis.get("volume_spike", 1)
        
        if (week_change <= threshold and 
            volume_spike >= 1.5 and 
            analysis.get("consecutive_drops", 0) >= 2):
            return True
        
        # Condition 4: High volatility with significant drop
        volatility = analysis.get("price_volatility", 0)
        if (volatility > 0.05 and  # 5% volatility
            analysis.get("daily_change", 0) <= threshold and
            analysis.get("max_single_drop", 0) >= abs(threshold)):
            return True
        
        return False
    
    async def _trigger_alert_with_analysis(self, alert: AlertModel, analysis_data: Dict):
        """Trigger alert and generate specialized analysis"""
        try:
            # Update alert status
            alert.status = AlertStatus.TRIGGERED
            alert.triggered_at = datetime.utcnow()
            
            # Generate specialized analysis
            analysis_report = await self._generate_drop_analysis(alert, analysis_data)
            
            # Update alert message with analysis
            alert.message = f"Smart Alert: {alert.stock.symbol} triggered - {analysis_report.get('summary', 'Price pattern analysis completed')}"
            
            self.logger.info(f"Alert {alert.id} triggered with smart analysis")
            
        except Exception as e:
            self.logger.error(f"Error triggering alert {alert.id}: {str(e)}")
            raise
    
    async def _generate_drop_analysis(self, alert: AlertModel, analysis_data: Dict) -> Dict:
        """Generate specialized analysis for price drop"""
        try:
            symbol = alert.stock.symbol
            stock_name = alert.stock.name
            
            # Get recent news for context
            news_data = await self._get_recent_news(symbol)
            
            # Create specialized prompt for drop analysis
            prompt = f"""
            Analyze the recent price drop for {stock_name} ({symbol}) and provide a comprehensive analysis.
            
            Price Analysis Data:
            - Current Price: ${analysis_data.get('current_price', 0):.2f}
            - Daily Change: {analysis_data.get('daily_change', 0):.2f}%
            - Week Change: {analysis_data.get('week_change', 0):.2f}%
            - Consecutive Drops: {analysis_data.get('consecutive_drops', 0)} days
            - Total Drop: {analysis_data.get('total_drop_percent', 0):.2f}%
            - Volume Spike: {analysis_data.get('volume_spike', 1):.2f}x
            - Volatility: {analysis_data.get('price_volatility', 0):.2f}%
            
            Recent News Context:
            {self._format_news_for_analysis(news_data)}
            
            Please provide:
            1. Root Cause Analysis - What's driving the price drop?
            2. Technical Analysis - Chart patterns and indicators
            3. Fundamental Analysis - Company-specific factors
            4. Market Context - Sector and market conditions
            5. Risk Assessment - Is this a temporary dip or structural issue?
            6. Investment Recommendation - Hold, Buy more, or Sell?
            7. Key Metrics to Monitor - What to watch going forward
            
            Format as a structured analysis report.
            """
            
            # Generate AI analysis using the available method
            analysis_data = {
                "symbol": symbol,
                "name": stock_name,
                "custom_prompt": prompt
            }
            analysis = await self.ai_service.analyze_stock_with_ai(analysis_data, [])
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error generating drop analysis: {str(e)}")
            return {"summary": "Analysis generation failed", "error": str(e)}
    
    async def _get_historical_prices(self, symbol: str, days: int = 7) -> List[Dict]:
        """Get historical price data"""
        try:
            # Convert days to period string
            if days <= 1:
                period = "1d"
            elif days <= 7:
                period = "7d"
            elif days <= 30:
                period = "1mo"
            elif days <= 90:
                period = "3mo"
            else:
                period = "1y"
            
            return await self.stock_api.get_historical_data(symbol, period)
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return []
    
    async def _get_recent_news(self, symbol: str) -> List[Dict]:
        """Get recent news for the stock"""
        try:
            # This would integrate with your news API
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Error getting news for {symbol}: {str(e)}")
            return []
    
    def _format_news_for_analysis(self, news_data: List[Dict]) -> str:
        """Format news data for analysis prompt"""
        if not news_data:
            return "No recent news available"
        
        formatted_news = []
        for news in news_data[:5]:  # Limit to 5 most recent
            formatted_news.append(f"- {news.get('title', 'No title')} ({news.get('published_at', 'Unknown date')})")
        
        return "\n".join(formatted_news)
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        if len(prices) < 2:
            return 0
        
        returns = []
        for i in range(len(prices) - 1):
            ret = (prices[i] - prices[i+1]) / prices[i+1]
            returns.append(ret)
        
        if not returns:
            return 0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
    
    def _calculate_trend_strength(self, prices: List[float]) -> float:
        """Calculate trend strength"""
        if len(prices) < 2:
            return 0
        
        # Simple linear regression slope
        n = len(prices)
        x = list(range(n))
        y = prices
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope
