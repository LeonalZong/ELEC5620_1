"""
Analysis Agent
Performs technical and fundamental analysis
"""
from typing import Dict, Any, List
import numpy as np
from datetime import datetime

from app.agents.base_agent import BaseAgent

class AnalysisAgent(BaseAgent):
    """
    Agent responsible for technical and fundamental analysis
    """
    
    def __init__(self, agent_id: str = "analysis"):
        """
        Initialize Analysis Agent
        
        Args:
            agent_id: Agent identifier
        """
        super().__init__(agent_id, "Analysis Agent")
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute analysis task
        
        Args:
            task_data: Task parameters including stock data
            
        Returns:
            Analysis results
        """
        stock_data = task_data.get("stock_data", {})
        if not stock_data:
            raise ValueError("Stock data is required for analysis")
        
        # Perform multi-timeframe technical analysis
        technical_analysis = self.multi_timeframe_technical_analysis(stock_data)
        
        # Perform fundamental analysis
        fundamental_analysis = self.fundamental_analysis(stock_data)
        
        # Generate trading signals
        trading_signal = self.generate_signals({
            "technical": technical_analysis,
            "fundamental": fundamental_analysis
        })
        
        # Calculate confidence score
        confidence_score = self.calculate_confidence_score(technical_analysis, fundamental_analysis)
        
        # Also perform basic technical analysis for compatibility
        basic_technical = self.technical_analysis(stock_data)
        
        return {
            "symbol": stock_data.get("symbol", ""),
            "technical_analysis": basic_technical,  # Use basic technical analysis for compatibility
            "multi_timeframe_analysis": technical_analysis,  # Keep multi-timeframe analysis
            "fundamental_analysis": fundamental_analysis,
            "trading_signal": trading_signal,
            "confidence_score": confidence_score,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def technical_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform technical analysis
        
        Args:
            stock_data: Stock price and volume data
            
        Returns:
            Technical analysis results
        """
        historical_data = stock_data.get("historical_data", [])
        self.logger.info(f"Historical data length: {len(historical_data)}")
        
        if not historical_data:
            self.logger.warning("No historical data available for technical analysis")
            return {"error": "No historical data available"}
        
        # Extract closing prices
        prices = [float(day.get("close", 0)) for day in historical_data if day.get("close")]
        self.logger.info(f"Extracted {len(prices)} prices for technical analysis")
        
        if len(prices) < 20:
            self.logger.warning(f"Insufficient data for technical analysis: {len(prices)} prices available, need at least 20")
            return {"error": "Insufficient data for technical analysis"}
        
        # Calculate technical indicators
        rsi = self.calculate_rsi(prices)
        macd = self.calculate_macd(prices)
        moving_averages = self.calculate_moving_averages(prices)
        trend = self.trend_analysis(prices)
        
        self.logger.info(f"Calculated RSI: {rsi}")
        self.logger.info(f"Calculated MACD: {macd}")
        self.logger.info(f"Calculated Moving Averages: {moving_averages}")
        
        return {
            "rsi": rsi,
            "macd": macd,
            "moving_averages": moving_averages,
            "trend": trend,
            "current_price": stock_data.get("current_price", 0),
            "price_change_percent": stock_data.get("price_change_percent", 0)
        }
    
    def multi_timeframe_technical_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform technical analysis across multiple timeframes
        
        Args:
            stock_data: Stock data including multi-timeframe price changes
            
        Returns:
            Multi-timeframe technical analysis
        """
        # Get price change data
        daily_change = stock_data.get("price_change_percent", 0)
        short_term_change = stock_data.get("short_term_change_percent", 0)
        medium_term_change = stock_data.get("medium_term_change_percent", 0)
        long_term_change = stock_data.get("long_term_change_percent", 0)
        
        # Get trend analysis
        trend_analysis = stock_data.get("trend_analysis", {})
        
        # Calculate technical indicators for each timeframe
        historical_data = stock_data.get("historical_data", [])
        
        # Short-term analysis (7 days)
        short_term_analysis = self.analyze_timeframe(historical_data, 7, "SHORT_TERM")
        
        # Medium-term analysis (14 days)
        medium_term_analysis = self.analyze_timeframe(historical_data, 14, "MEDIUM_TERM")
        
        # Long-term analysis (28 days)
        long_term_analysis = self.analyze_timeframe(historical_data, 28, "LONG_TERM")
        
        # Overall trend strength
        trend_strength = self.calculate_trend_strength(short_term_change, medium_term_change, long_term_change)
        
        # Multi-timeframe signals
        signals = self.generate_multi_timeframe_signals(
            short_term_analysis, medium_term_analysis, long_term_analysis
        )
        
        return {
            "daily_change": daily_change,
            "short_term": {
                "change_percent": short_term_change,
                "trend": trend_analysis.get("short_term_trend", "NEUTRAL"),
                "analysis": short_term_analysis
            },
            "medium_term": {
                "change_percent": medium_term_change,
                "trend": trend_analysis.get("medium_term_trend", "NEUTRAL"),
                "analysis": medium_term_analysis
            },
            "long_term": {
                "change_percent": long_term_change,
                "trend": trend_analysis.get("long_term_trend", "NEUTRAL"),
                "analysis": long_term_analysis
            },
            "trend_strength": trend_strength,
            "multi_timeframe_signals": signals,
            "overall_trend": self.determine_overall_trend(short_term_change, medium_term_change, long_term_change)
        }
    
    def analyze_timeframe(self, historical_data: List[Dict[str, Any]], days: int, timeframe: str) -> Dict[str, Any]:
        """
        Analyze a specific timeframe
        
        Args:
            historical_data: Historical price data
            days: Number of days to analyze
            timeframe: Timeframe label
            
        Returns:
            Timeframe analysis
        """
        if len(historical_data) < days:
            return {
                "rsi": 50,
                "trend": "NEUTRAL",
                "momentum": "NEUTRAL",
                "volatility": "LOW"
            }
        
        # Get data for the timeframe
        timeframe_data = historical_data[-days:]
        prices = [day.get("close", 0) for day in timeframe_data]
        
        # Calculate RSI for timeframe
        rsi = self.calculate_rsi(prices)
        
        # Calculate trend
        trend = self.calculate_trend_direction(prices)
        
        # Calculate momentum
        momentum = self.calculate_momentum(prices)
        
        # Calculate volatility
        volatility = self.calculate_volatility(prices)
        
        return {
            "rsi": rsi,
            "trend": trend,
            "momentum": momentum,
            "volatility": volatility
        }
    
    def calculate_trend_strength(self, short_term: float, medium_term: float, long_term: float) -> str:
        """
        Calculate overall trend strength
        
        Args:
            short_term: Short-term change percentage
            medium_term: Medium-term change percentage
            long_term: Long-term change percentage
            
        Returns:
            Trend strength (WEAK, MODERATE, STRONG)
        """
        # Count positive trends
        positive_trends = sum(1 for change in [short_term, medium_term, long_term] if change > 0)
        negative_trends = sum(1 for change in [short_term, medium_term, long_term] if change < 0)
        
        if positive_trends >= 2:
            return "STRONG_BULLISH" if positive_trends == 3 else "MODERATE_BULLISH"
        elif negative_trends >= 2:
            return "STRONG_BEARISH" if negative_trends == 3 else "MODERATE_BEARISH"
        else:
            return "NEUTRAL"
    
    def generate_multi_timeframe_signals(self, short_term: Dict[str, Any], medium_term: Dict[str, Any], long_term: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate signals based on multiple timeframes
        
        Args:
            short_term: Short-term analysis
            medium_term: Medium-term analysis
            long_term: Long-term analysis
            
        Returns:
            Multi-timeframe signals
        """
        signals = {}
        
        # Short-term signal
        if short_term["trend"] == "UP" and short_term["rsi"] < 70:
            signals["short_term"] = "BUY"
        elif short_term["trend"] == "DOWN" and short_term["rsi"] > 30:
            signals["short_term"] = "SELL"
        else:
            signals["short_term"] = "HOLD"
        
        # Medium-term signal
        if medium_term["trend"] == "UP" and medium_term["momentum"] == "POSITIVE":
            signals["medium_term"] = "BUY"
        elif medium_term["trend"] == "DOWN" and medium_term["momentum"] == "NEGATIVE":
            signals["medium_term"] = "SELL"
        else:
            signals["medium_term"] = "HOLD"
        
        # Long-term signal
        if long_term["trend"] == "UP" and long_term["volatility"] == "LOW":
            signals["long_term"] = "BUY"
        elif long_term["trend"] == "DOWN" and long_term["volatility"] == "HIGH":
            signals["long_term"] = "SELL"
        else:
            signals["long_term"] = "HOLD"
        
        return signals
    
    def calculate_trend_direction(self, prices: List[float]) -> str:
        """
        Calculate trend direction for a price series
        
        Args:
            prices: List of prices
            
        Returns:
            Trend direction (UP, DOWN, NEUTRAL)
        """
        if len(prices) < 2:
            return "NEUTRAL"
        
        # Simple trend calculation
        first_half = prices[:len(prices)//2]
        second_half = prices[len(prices)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.02:
            return "UP"
        elif second_avg < first_avg * 0.98:
            return "DOWN"
        else:
            return "NEUTRAL"
    
    def calculate_momentum(self, prices: List[float]) -> str:
        """
        Calculate momentum for a price series
        
        Args:
            prices: List of prices
            
        Returns:
            Momentum (POSITIVE, NEGATIVE, NEUTRAL)
        """
        if len(prices) < 2:
            return "NEUTRAL"
        
        # Calculate momentum as rate of change
        momentum = (prices[-1] - prices[0]) / prices[0]
        
        if momentum > 0.02:
            return "POSITIVE"
        elif momentum < -0.02:
            return "NEGATIVE"
        else:
            return "NEUTRAL"
    
    def calculate_volatility(self, prices: List[float]) -> str:
        """
        Calculate volatility level for a price series
        
        Args:
            prices: List of prices
            
        Returns:
            Volatility level (LOW, MEDIUM, HIGH)
        """
        if len(prices) < 2:
            return "LOW"
        
        # Calculate standard deviation
        mean_price = sum(prices) / len(prices)
        variance = sum((price - mean_price) ** 2 for price in prices) / len(prices)
        std_dev = variance ** 0.5
        
        # Normalize by mean price
        volatility = std_dev / mean_price if mean_price > 0 else 0
        
        if volatility > 0.05:
            return "HIGH"
        elif volatility > 0.02:
            return "MEDIUM"
        else:
            return "LOW"
    
    def determine_overall_trend(self, short_term: float, medium_term: float, long_term: float) -> str:
        """
        Determine overall trend based on multiple timeframes
        
        Args:
            short_term: Short-term change percentage
            medium_term: Medium-term change percentage
            long_term: Long-term change percentage
            
        Returns:
            Overall trend (BULLISH, BEARISH, NEUTRAL)
        """
        # Weight the timeframes (long-term has more weight)
        weighted_score = (short_term * 0.2) + (medium_term * 0.3) + (long_term * 0.5)
        
        if weighted_score > 2:
            return "BULLISH"
        elif weighted_score < -2:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calculate Relative Strength Index
        
        Args:
            prices: List of closing prices
            period: RSI period
            
        Returns:
            RSI value
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # Calculate average gains and losses
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def calculate_macd(
        self,
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, float]:
        """
        Calculate MACD indicator
        
        Args:
            prices: List of closing prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            MACD values
        """
        if len(prices) < slow_period:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        # Calculate EMAs
        fast_ema = self.calculate_ema(prices, fast_period)
        slow_ema = self.calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # For signal line, we need MACD values over time
        # Simplified: use current MACD as signal
        signal_line = macd_line * 0.9  # Simplified signal calculation
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return {
            "macd": round(macd_line, 4),
            "signal": round(signal_line, 4),
            "histogram": round(histogram, 4)
        }
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average
        
        Args:
            prices: List of closing prices
            period: EMA period
            
        Returns:
            EMA value
        """
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        # Calculate smoothing factor
        multiplier = 2 / (period + 1)
        
        # Start with SMA
        ema = sum(prices[:period]) / period
        
        # Calculate EMA for remaining prices
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def calculate_moving_averages(
        self,
        prices: List[float],
        periods: List[int] = [20, 50, 200]
    ) -> Dict[int, float]:
        """
        Calculate moving averages
        
        Args:
            prices: List of closing prices
            periods: List of MA periods
            
        Returns:
            Moving averages dictionary
        """
        moving_averages = {}
        
        for period in periods:
            if len(prices) >= period:
                ma = sum(prices[-period:]) / period
                moving_averages[period] = round(ma, 2)
            else:
                moving_averages[period] = 0.0
        
        return moving_averages
    
    def fundamental_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform fundamental analysis
        
        Args:
            stock_data: Stock data including market cap and price
            
        Returns:
            Fundamental analysis results
        """
        current_price = stock_data.get("current_price", 0)
        market_cap = stock_data.get("market_cap", 0)
        
        # Simplified fundamental analysis
        # In a real system, you would fetch financial statements
        pe_ratio = self.estimate_pe_ratio(current_price, market_cap)
        pb_ratio = self.estimate_pb_ratio(current_price, market_cap)
        
        return {
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "market_cap": market_cap,
            "current_price": current_price,
            "valuation": self.assess_valuation(pe_ratio, pb_ratio)
        }
    
    def trend_analysis(self, price_data: List[float]) -> str:
        """
        Analyze price trend
        
        Args:
            price_data: Historical price data
            
        Returns:
            Trend direction (BULLISH, BEARISH, SIDEWAYS)
        """
        if len(price_data) < 10:
            return "SIDEWAYS"
        
        # Calculate short and long term trends
        short_term = price_data[-5:]  # Last 5 days
        long_term = price_data[-20:] if len(price_data) >= 20 else price_data
        
        # Calculate trend slopes
        short_slope = self.calculate_slope(short_term)
        long_slope = self.calculate_slope(long_term)
        
        # Determine trend
        if short_slope > 0.01 and long_slope > 0.01:
            return "BULLISH"
        elif short_slope < -0.01 and long_slope < -0.01:
            return "BEARISH"
        else:
            return "SIDEWAYS"
    
    def generate_signals(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate trading signals
        
        Args:
            analysis_data: Technical and fundamental analysis data
            
        Returns:
            Trading signal (BUY, SELL, HOLD)
        """
        technical = analysis_data.get("technical", {})
        fundamental = analysis_data.get("fundamental", {})
        
        # Technical signals
        rsi = technical.get("rsi", 50)
        trend = technical.get("trend", "SIDEWAYS")
        macd = technical.get("macd", {})
        
        # Fundamental signals
        pe_ratio = fundamental.get("pe_ratio", 0)
        valuation = fundamental.get("valuation", "FAIR")
        
        # Generate signal based on multiple factors
        buy_signals = 0
        sell_signals = 0
        
        # RSI signals
        if rsi < 30:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 1
        
        # Trend signals
        if trend == "BULLISH":
            buy_signals += 1
        elif trend == "BEARISH":
            sell_signals += 1
        
        # MACD signals
        if macd.get("macd", 0) > macd.get("signal", 0):
            buy_signals += 1
        else:
            sell_signals += 1
        
        # Fundamental signals
        if valuation == "UNDERVALUED":
            buy_signals += 1
        elif valuation == "OVERVALUED":
            sell_signals += 1
        
        # Determine final signal
        if buy_signals > sell_signals and buy_signals >= 2:
            return "BUY"
        elif sell_signals > buy_signals and sell_signals >= 2:
            return "SELL"
        else:
            return "HOLD"
    
    def calculate_slope(self, prices: List[float]) -> float:
        """Calculate slope of price trend"""
        if len(prices) < 2:
            return 0.0
        
        x = list(range(len(prices)))
        y = prices
        
        # Simple linear regression slope
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope
    
    def estimate_pe_ratio(self, price: float, market_cap: float) -> float:
        """Estimate P/E ratio based on market cap"""
        if market_cap == 0:
            return 0.0
        
        # Simplified estimation
        estimated_earnings = market_cap * 0.1  # Assume 10% earnings
        return round(price / (estimated_earnings / 1000000), 2) if estimated_earnings > 0 else 0.0
    
    def estimate_pb_ratio(self, price: float, market_cap: float) -> float:
        """Estimate P/B ratio based on market cap"""
        if market_cap == 0:
            return 0.0
        
        # Simplified estimation
        estimated_book_value = market_cap * 0.3  # Assume 30% book value
        return round(price / (estimated_book_value / 1000000), 2) if estimated_book_value > 0 else 0.0
    
    def assess_valuation(self, pe_ratio: float, pb_ratio: float) -> str:
        """Assess if stock is overvalued, undervalued, or fair"""
        if pe_ratio < 15 and pb_ratio < 1.5:
            return "UNDERVALUED"
        elif pe_ratio > 25 or pb_ratio > 3.0:
            return "OVERVALUED"
        else:
            return "FAIR"
    
    def calculate_confidence_score(self, technical: Dict[str, Any], fundamental: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.5  # Base score
        
        # Technical confidence
        rsi = technical.get("rsi", 50)
        if 30 <= rsi <= 70:
            score += 0.1
        
        # Fundamental confidence
        pe_ratio = fundamental.get("pe_ratio", 0)
        if 10 <= pe_ratio <= 30:
            score += 0.1
        
        # Trend confidence
        trend = technical.get("trend", "SIDEWAYS")
        if trend in ["BULLISH", "BEARISH"]:
            score += 0.1
        
        return min(1.0, max(0.0, score))




