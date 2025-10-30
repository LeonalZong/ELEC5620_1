"""
Report Service
Business logic for report operations
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import logging
import json

from app.agents.agent_manager import AgentManager
from app.schemas.report import Report, ReportRequest, ReportSummary, Stock
from app.models.report import Report as ReportModel
from app.models.stock import Stock as StockModel
from app.models.user import User as UserModel
from app.services.ai_analysis_service import AIAnalysisService

class ReportService:
    """
    Service for report operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_manager = AgentManager(db)
        self.ai_service = AIAnalysisService()
        self.logger = logging.getLogger("report_service")
    
    async def generate_report(self, user_id: int, stock_id: int, report_type: str = "COMPREHENSIVE") -> Report:
        """
        Generate a new analysis report
        
        Args:
            user_id: User ID
            stock_id: Stock ID
            report_type: Type of report
            
        Returns:
            Generated report
        """
        try:
            # Get stock information
            stock = self.db.query(StockModel).filter(StockModel.id == stock_id).first()
            if not stock:
                raise ValueError(f"Stock {stock_id} not found")
            
            # Use Agent Manager to generate report
            result = await self.agent_manager.run_stock_analysis_pipeline(
                user_id=user_id,
                stock_symbol=stock.symbol
            )
            
            # Extract data from analysis result
            report_data = result.get("report", {})
            analysis_data = result.get("analysis", {})
            risk_data = result.get("risk_analysis", {})
            emotion_data = result.get("emotional_analysis", {})
            
            # Debug logging
            self.logger.info(f"Analysis data keys: {list(analysis_data.keys())}")
            self.logger.info(f"Risk data keys: {list(risk_data.keys())}")
            self.logger.info(f"Emotion data keys: {list(emotion_data.keys())}")
            self.logger.info(f"Result keys: {list(result.keys())}")
            
            # Generate data overview (for quick reference)
            self.logger.info("=== GENERATING DATA OVERVIEW ===")
            data_overview = self._generate_data_overview(stock, analysis_data, risk_data, emotion_data, result)
            self.logger.info(f"Data overview generated: {len(data_overview)} characters")
            
            # Generate full analysis report using AI (detailed text-based analysis)
            self.logger.info("=== GENERATING AI FULL ANALYSIS ===")
            full_analysis = await self._generate_ai_full_analysis(stock, analysis_data, risk_data, emotion_data, result)
            self.logger.info(f"Full analysis generated: {len(full_analysis)} characters")
            self.logger.info(f"Full analysis preview (first 500 chars): {full_analysis[:500]}")
            
            # Combine data overview and full analysis
            combined_content = f"{data_overview}\n\n---\n\n{full_analysis}"
            self.logger.info(f"Combined content: {len(combined_content)} characters")
            
            recommendations = self._generate_recommendations(analysis_data, risk_data, emotion_data)
            
            # Create report record in database
            report = ReportModel(
                user_id=user_id,
                stock_id=stock_id,
                title=report_data.get("title", f"Analysis Report for {stock.symbol}"),
                summary=report_data.get("executive_summary", "Report summary"),
                content=combined_content,
                recommendations=recommendations,
                risk_level=risk_data.get("risk_level", "MEDIUM"),
                sentiment_score=emotion_data.get("fear_greed_index", {}).get("index", 50),
                technical_signal=analysis_data.get("trading_signal", "HOLD"),
                confidence_score=analysis_data.get("confidence_score", 0.5),
                details_json=result,
                report_type=report_type,
                created_at=datetime.utcnow()
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            return Report(
                id=report.id,
                user_id=report.user_id,
                stock_id=report.stock_id,
                stock=Stock(
                    id=stock.id,
                    symbol=stock.symbol,
                    name=stock.name,
                    current_price=stock.current_price,
                    sector=stock.sector
                ),
                title=report.title,
                summary=report.summary,
                content=report.content,
                recommendations=report.recommendations,
                risk_level=report.risk_level,
                sentiment_score=report.sentiment_score,
                technical_signal=report.technical_signal,
                confidence_score=report.confidence_score,
                details_json=report.details_json,
                report_type=report.report_type,
                created_at=report.created_at.isoformat()
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to generate report: {str(e)}")
            raise Exception(f"Failed to generate report: {str(e)}")
    
    async def _generate_ai_full_analysis(self, stock: StockModel, analysis_data: dict, risk_data: dict, emotion_data: dict, result: dict) -> str:
        """Generate comprehensive full analysis using AI"""
        self.logger.info("=== STARTING AI FULL ANALYSIS GENERATION ===")
        try:
            # Prepare data for AI
            stock_data = result.get("data_collection", {}).get("stock_data", {})
            technical = analysis_data.get("technical_analysis", {})
            multi_tf = analysis_data.get("multi_timeframe_analysis", {})
            
            self.logger.info(f"Stock: {stock.symbol}, Price: {stock.current_price}")
            
            # Create detailed prompt for AI
            current_price_str = f"${stock.current_price:.2f}" if stock.current_price else "$0.00"
            
            prompt = f"""
You are a senior financial analyst. Generate a comprehensive, professional investment analysis report for {stock.symbol} ({stock.name}).

## AVAILABLE DATA:

**Stock Information:**
- Current Price: {current_price_str}
- Sector: {stock.sector or 'N/A'}
- Market Cap: ${stock_data.get('market_cap', 'N/A')}
- Volume: {stock_data.get('volume', 'N/A')}

**Price Changes:**
- 1-Day: {stock_data.get('price_change_percent', 'N/A')}%
- 7-Day: {stock_data.get('short_term_change_percent', 'N/A')}%
- 14-Day: {stock_data.get('medium_term_change_percent', 'N/A')}%
- 28-Day: {stock_data.get('long_term_change_percent', 'N/A')}%

**Technical Indicators:**
- RSI: {technical.get('rsi', 'N/A')}
- MACD: {technical.get('macd', {})}
- Moving Averages: {technical.get('moving_averages', {})}
- Trading Signal: {analysis_data.get('trading_signal', 'HOLD')}
- Confidence: {analysis_data.get('confidence_score', 0.5):.1%}

**Risk Metrics:**
- Risk Level: {risk_data.get('risk_level', 'MEDIUM')}
- Volatility: {risk_data.get('volatility', 'N/A')}
- Beta: {risk_data.get('beta', 'N/A')}
- VaR: {risk_data.get('var', 'N/A')}%

**Market Sentiment:**
- Fear & Greed Index: {emotion_data.get('fear_greed_index', {}).get('index', 'N/A')}
- News Sentiment: {emotion_data.get('news_sentiment', {})}
- Market Sentiment: {emotion_data.get('market_sentiment', {})}

## INSTRUCTIONS:

Generate a detailed analysis report with the following 5 sections. Each section should be 2-3 substantial paragraphs of professional analysis:

# 📊 Technical Analysis

Write a comprehensive technical analysis covering:
- Detailed interpretation of RSI, MACD, and Moving Averages
- Multi-timeframe trend analysis (short, medium, long-term)
- Price action patterns and momentum indicators
- What these indicators suggest for future price movement
- Specific entry/exit points if applicable

# ⚠️ Risk Analysis

Provide an in-depth risk assessment including:
- Detailed volatility analysis and what it means for investors
- Beta interpretation and market correlation
- Value at Risk (VaR) implications
- Overall risk profile for different investor types
- Specific risk mitigation strategies

# 💭 Market Sentiment Analysis

Analyze the market sentiment comprehensively:
- Fear & Greed Index interpretation and market psychology
- News sentiment impact on stock performance
- Market-wide sentiment trends affecting this stock
- Contrarian vs. momentum indicators
- How sentiment might drive near-term price action

# 📈 Fundamental Data Analysis

Analyze the fundamental metrics:
- Market capitalization and company size implications
- Trading volume and liquidity analysis
- Valuation metrics (P/E ratio, etc.) if available
- Sector positioning and competitive landscape
- Growth potential and fundamental strength

# 📝 Investment Conclusion

Provide a comprehensive investment recommendation:
- Clear BUY/SELL/HOLD recommendation with reasoning
- Time horizon for the recommendation (short/medium/long term)
- Specific price targets or ranges if applicable
- Risk-adjusted return expectations
- Portfolio allocation suggestions for different investor types
- Key catalysts to watch

## FORMAT REQUIREMENTS:
- Write in professional, clear English
- Use complete sentences and paragraphs
- Each section should be 2-3 substantial paragraphs
- Avoid bullet points in the main analysis (use flowing paragraphs)
- Be specific and actionable
- Support all conclusions with data-driven reasoning
"""

            # Call OpenAI API
            self.logger.info("Calling OpenAI API...")
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": "You are a senior financial analyst with 20+ years of experience in equity research and investment analysis. Write detailed, professional analysis reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            full_analysis = response.choices[0].message.content
            self.logger.info(f"✅ AI RESPONSE RECEIVED: {len(full_analysis)} characters")
            self.logger.info(f"AI Response Preview: {full_analysis[:300]}...")
            
            return full_analysis
            
        except Exception as e:
            self.logger.error(f"❌ FAILED to generate AI full analysis: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Fallback to template-based content
            self.logger.warning("⚠️ FALLING BACK to template-based content")
            fallback_content = self._generate_full_report_content(stock, analysis_data, risk_data, emotion_data, result)
            self.logger.info(f"Fallback content generated: {len(fallback_content)} characters")
            return fallback_content
    
    def _generate_data_overview(self, stock: StockModel, analysis_data: dict, risk_data: dict, emotion_data: dict, result: dict) -> str:
        """Generate data overview table for quick reference"""
        overview_parts = []
        
        overview_parts.append("# 📋 DATA OVERVIEW\n")
        
        # Get data
        stock_data = result.get("data_collection", {}).get("stock_data", {})
        technical = analysis_data.get("technical_analysis", {})
        
        # Format helper
        def format_change(change):
            if isinstance(change, (int, float)):
                return f"{change:+.2f}%"
            return str(change)
        
        # Table: Stock Information
        overview_parts.append("## Stock Information")
        overview_parts.append("```")
        overview_parts.append(f"{'Metric':<25} | {'Value':>20}")
        overview_parts.append("-" * 48)
        overview_parts.append(f"{'Symbol':<25} | {stock.symbol:>20}")
        overview_parts.append(f"{'Company Name':<25} | {stock.name[:20] if stock.name else 'N/A':>20}")
        overview_parts.append(f"{'Current Price':<25} | {'$' + f'{stock.current_price:.2f}' if stock.current_price else 'N/A':>20}")
        overview_parts.append(f"{'Sector':<25} | {(stock.sector[:20] if stock.sector else 'N/A'):>20}")
        overview_parts.append("```")
        overview_parts.append("")
        
        # Table: Price Changes
        overview_parts.append("## Price Changes")
        overview_parts.append("```")
        overview_parts.append(f"{'Period':<25} | {'Change':>20}")
        overview_parts.append("-" * 48)
        overview_parts.append(f"{'1-Day':<25} | {format_change(stock_data.get('price_change_percent', 'N/A')):>20}")
        overview_parts.append(f"{'7-Day (Short Term)':<25} | {format_change(stock_data.get('short_term_change_percent', 'N/A')):>20}")
        overview_parts.append(f"{'14-Day (Medium Term)':<25} | {format_change(stock_data.get('medium_term_change_percent', 'N/A')):>20}")
        overview_parts.append(f"{'28-Day (Long Term)':<25} | {format_change(stock_data.get('long_term_change_percent', 'N/A')):>20}")
        overview_parts.append("```")
        overview_parts.append("")
        
        # Table: Technical Indicators
        overview_parts.append("## Technical Indicators")
        overview_parts.append("```")
        overview_parts.append(f"{'Indicator':<25} | {'Value':>20}")
        overview_parts.append("-" * 48)
        
        # RSI
        rsi_value = technical.get('rsi', 'N/A')
        if isinstance(rsi_value, (int, float)):
            rsi_str = f"{rsi_value:.2f}"
            rsi_status = " (Oversold)" if rsi_value < 30 else " (Overbought)" if rsi_value > 70 else " (Neutral)"
            overview_parts.append(f"{'RSI':<25} | {(rsi_str + rsi_status):>20}")
        else:
            overview_parts.append(f"{'RSI':<25} | {str(rsi_value):>20}")
        
        # MACD
        macd_value = technical.get('macd', {})
        if isinstance(macd_value, dict):
            macd_line = macd_value.get('macd', 'N/A')
            if isinstance(macd_line, (int, float)):
                overview_parts.append(f"{'MACD Line':<25} | {f'{macd_line:.4f}':>20}")
            else:
                overview_parts.append(f"{'MACD Line':<25} | {str(macd_line):>20}")
        
        # Moving Averages
        ma_data = technical.get('moving_averages', {})
        if isinstance(ma_data, dict) and ma_data:
            for period in sorted([20, 50, 200]):
                if period in ma_data:
                    value = ma_data[period]
                    if isinstance(value, (int, float)) and value > 0:
                        overview_parts.append(f"{f'MA{period}':<25} | {'$' + f'{value:.2f}':>20}")
        
        # Trading Signal
        trading_signal = analysis_data.get('trading_signal', 'HOLD')
        confidence = analysis_data.get('confidence_score', 0.5)
        overview_parts.append(f"{'Trading Signal':<25} | {trading_signal:>20}")
        overview_parts.append(f"{'Confidence':<25} | {f'{confidence:.1%}':>20}")
        overview_parts.append("```")
        overview_parts.append("")
        
        # Table: Risk Metrics
        overview_parts.append("## Risk Metrics")
        overview_parts.append("```")
        overview_parts.append(f"{'Metric':<25} | {'Value':>20}")
        overview_parts.append("-" * 48)
        overview_parts.append(f"{'Risk Level':<25} | {risk_data.get('risk_level', 'N/A'):>20}")
        
        volatility = risk_data.get('volatility', 'N/A')
        if isinstance(volatility, (int, float)):
            overview_parts.append(f"{'Volatility':<25} | {f'{volatility:.2f}':>20}")
        else:
            overview_parts.append(f"{'Volatility':<25} | {str(volatility):>20}")
        
        beta = risk_data.get('beta', 'N/A')
        if isinstance(beta, (int, float)):
            overview_parts.append(f"{'Beta':<25} | {f'{beta:.2f}':>20}")
        else:
            overview_parts.append(f"{'Beta':<25} | {str(beta):>20}")
        
        var = risk_data.get('var', 'N/A')
        if isinstance(var, (int, float)):
            overview_parts.append(f"{'Value at Risk (VaR)':<25} | {f'{var:.2f}%':>20}")
        else:
            overview_parts.append(f"{'Value at Risk':<25} | {str(var):>20}")
        overview_parts.append("```")
        overview_parts.append("")
        
        # Table: Market Sentiment
        overview_parts.append("## Market Sentiment")
        overview_parts.append("```")
        overview_parts.append(f"{'Metric':<25} | {'Value':>20}")
        overview_parts.append("-" * 48)
        
        fear_greed = emotion_data.get("fear_greed_index", {})
        fg_index = fear_greed.get('index', 'N/A')
        if isinstance(fg_index, (int, float)):
            fg_label = fear_greed.get('label', 'N/A')
            overview_parts.append(f"{'Fear & Greed Index':<25} | {f'{fg_index} ({fg_label})':>20}")
        else:
            overview_parts.append(f"{'Fear & Greed Index':<25} | {str(fg_index):>20}")
        
        news_sentiment = emotion_data.get('news_sentiment', {})
        if isinstance(news_sentiment, dict):
            overall = news_sentiment.get('overall_sentiment', 'N/A')
            count = news_sentiment.get('news_count', 0)
            overview_parts.append(f"{'News Sentiment':<25} | {f'{overall} ({count} articles)':>20}")
        
        market_sentiment = emotion_data.get('market_sentiment', {})
        if isinstance(market_sentiment, dict):
            price_sentiment = market_sentiment.get('price_sentiment', 'N/A')
            overview_parts.append(f"{'Market Sentiment':<25} | {price_sentiment:>20}")
        overview_parts.append("```")
        overview_parts.append("")
        
        # Table: Market Data
        overview_parts.append("## Market Data")
        overview_parts.append("```")
        overview_parts.append(f"{'Metric':<25} | {'Value':>20}")
        overview_parts.append("-" * 48)
        
        # Volume
        volume = stock_data.get('volume', 'N/A')
        if isinstance(volume, (int, float)) and volume > 0:
            if volume >= 1e9:
                volume_str = f"{volume/1e9:.2f}B"
            elif volume >= 1e6:
                volume_str = f"{volume/1e6:.2f}M"
            else:
                volume_str = f"{volume:,.0f}"
            overview_parts.append(f"{'Trading Volume':<25} | {volume_str:>20}")
        else:
            overview_parts.append(f"{'Volume':<25} | {str(volume):>20}")
        
        # Market Cap
        market_cap = stock_data.get('market_cap', 'N/A')
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            if market_cap >= 1e12:
                cap_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                cap_str = f"${market_cap/1e9:.2f}B"
            else:
                cap_str = f"${market_cap/1e6:.2f}M"
            overview_parts.append(f"{'Market Cap':<25} | {cap_str:>20}")
        else:
            overview_parts.append(f"{'Market Cap':<25} | {str(market_cap):>20}")
        
        pe_ratio = stock_data.get('pe_ratio', 'N/A')
        overview_parts.append(f"{'PE Ratio':<25} | {str(pe_ratio):>20}")
        overview_parts.append("```")
        
        return "\n".join(overview_parts)
    
    def _generate_full_report_content(self, stock: StockModel, analysis_data: dict, risk_data: dict, emotion_data: dict, result: dict) -> str:
        """Generate comprehensive full report with detailed analysis"""
        content_parts = []
        
        # Get stock data
        stock_data = result.get("data_collection", {}).get("stock_data", {})
        technical = analysis_data.get("technical_analysis", {})
        multi_tf = analysis_data.get("multi_timeframe_analysis", {})
        
        # ========== SECTION 1: TECHNICAL ANALYSIS ==========
        content_parts.append("# 📊 Technical Analysis\n")
        
        content_parts.append("## Price Action & Trends")
        content_parts.append(f"Current Price: ${stock.current_price:.2f}" if stock.current_price else "Current Price: N/A")
        content_parts.append("")
        
        # Multi-timeframe trend analysis
        if multi_tf:
            content_parts.append("### Multi-Timeframe Trend Analysis")
            
            # Short-term (7 days)
            short_term = multi_tf.get('short_term', {})
            content_parts.append(f"**Short-Term (7 Days):**")
            content_parts.append(f"- Change: {short_term.get('change_percent', 'N/A'):+.2f}%" if isinstance(short_term.get('change_percent'), (int, float)) else f"- Change: {short_term.get('change_percent', 'N/A')}")
            content_parts.append(f"- Trend: {short_term.get('trend', 'N/A')}")
            content_parts.append("")
            
            # Medium-term (14 days)
            medium_term = multi_tf.get('medium_term', {})
            content_parts.append(f"**Medium-Term (14 Days):**")
            content_parts.append(f"- Change: {medium_term.get('change_percent', 'N/A'):+.2f}%" if isinstance(medium_term.get('change_percent'), (int, float)) else f"- Change: {medium_term.get('change_percent', 'N/A')}")
            content_parts.append(f"- Trend: {medium_term.get('trend', 'N/A')}")
            content_parts.append("")
            
            # Long-term (28 days)
            long_term = multi_tf.get('long_term', {})
            content_parts.append(f"**Long-Term (28 Days):**")
            content_parts.append(f"- Change: {long_term.get('change_percent', 'N/A'):+.2f}%" if isinstance(long_term.get('change_percent'), (int, float)) else f"- Change: {long_term.get('change_percent', 'N/A')}")
            content_parts.append(f"- Trend: {long_term.get('trend', 'N/A')}")
            content_parts.append("")
            
            # Overall trend strength
            content_parts.append(f"**Overall Trend:** {multi_tf.get('overall_trend', 'N/A')}")
            content_parts.append(f"**Trend Strength:** {multi_tf.get('trend_strength', 'N/A')}")
            content_parts.append("")
        
        # Technical Indicators
        content_parts.append("## Technical Indicators")
        
        # RSI Analysis
        rsi_value = technical.get('rsi', 'N/A')
        if isinstance(rsi_value, (int, float)):
            rsi_status = "Oversold" if rsi_value < 30 else "Overbought" if rsi_value > 70 else "Neutral"
            rsi_signal = "🟢 Buy Signal" if rsi_value < 30 else "🔴 Sell Signal" if rsi_value > 70 else "🟡 Hold Signal"
            content_parts.append(f"**RSI (Relative Strength Index):** {rsi_value:.2f}")
            content_parts.append(f"- Status: {rsi_status}")
            content_parts.append(f"- Signal: {rsi_signal}")
            content_parts.append("- Interpretation: RSI below 30 indicates oversold conditions (potential buying opportunity), above 70 indicates overbought conditions (potential selling pressure).")
        else:
            content_parts.append(f"**RSI:** {rsi_value}")
        content_parts.append("")
        
        # MACD Analysis
        macd_value = technical.get('macd', 'N/A')
        if isinstance(macd_value, dict):
            macd_line = macd_value.get('macd', 'N/A')
            signal_line = macd_value.get('signal', 'N/A')
            histogram = macd_value.get('histogram', 'N/A')
            content_parts.append(f"**MACD (Moving Average Convergence Divergence):**")
            content_parts.append(f"- MACD Line: {macd_line}")
            content_parts.append(f"- Signal Line: {signal_line}")
            content_parts.append(f"- Histogram: {histogram}")
            if isinstance(macd_line, (int, float)) and isinstance(signal_line, (int, float)):
                macd_signal = "🟢 Bullish" if macd_line > signal_line else "🔴 Bearish"
                content_parts.append(f"- Signal: {macd_signal}")
            content_parts.append("- Interpretation: MACD line above signal line indicates bullish momentum, below indicates bearish momentum.")
        else:
            content_parts.append(f"**MACD:** {macd_value}")
        content_parts.append("")
        
        # Moving Averages
        ma_data = technical.get('moving_averages', {})
        if isinstance(ma_data, dict) and ma_data:
            content_parts.append(f"**Moving Averages:**")
            for period, value in sorted(ma_data.items()):
                if isinstance(value, (int, float)) and value > 0:
                    if stock.current_price and stock.current_price > value:
                        position = "Above (Bullish)"
                    elif stock.current_price and stock.current_price < value:
                        position = "Below (Bearish)"
                    else:
                        position = "At MA"
                    content_parts.append(f"- MA{period}: ${value:.2f} - Price {position}")
                else:
                    content_parts.append(f"- MA{period}: {value}")
            content_parts.append("- Interpretation: Price above MA indicates uptrend, below indicates downtrend. Longer-period MAs show long-term trends.")
        else:
            content_parts.append(f"**Moving Averages:** {ma_data}")
        content_parts.append("")
        
        # Trading Signal
        trading_signal = analysis_data.get('trading_signal', 'HOLD')
        confidence = analysis_data.get('confidence_score', 0.5)
        signal_emoji = "🟢" if trading_signal == "BUY" else "🔴" if trading_signal == "SELL" else "🟡"
        content_parts.append(f"**Trading Signal:** {signal_emoji} {trading_signal}")
        content_parts.append(f"**Confidence Level:** {confidence:.1%}")
        content_parts.append("")
        
        # ========== SECTION 2: RISK ANALYSIS ==========
        content_parts.append("# ⚠️ Risk Analysis\n")
        
        risk_level = risk_data.get('risk_level', 'MEDIUM')
        risk_emoji = "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
        content_parts.append(f"**Overall Risk Level:** {risk_emoji} {risk_level}")
        content_parts.append("")
        
        # Volatility Analysis
        volatility = risk_data.get('volatility', 'N/A')
        if isinstance(volatility, (int, float)):
            vol_interpretation = "Low" if volatility < 1.0 else "Moderate" if volatility < 2.0 else "High"
            content_parts.append(f"**Volatility:** {volatility:.2f}")
            content_parts.append(f"- Interpretation: {vol_interpretation} volatility - {'Stable price movements' if volatility < 1.0 else 'Moderate price fluctuations' if volatility < 2.0 else 'Significant price swings'}")
        else:
            content_parts.append(f"**Volatility:** {volatility}")
        content_parts.append("")
        
        # Beta Analysis
        beta = risk_data.get('beta', 'N/A')
        if isinstance(beta, (int, float)):
            beta_interpretation = "Less volatile than market" if beta < 1.0 else "Market volatility" if beta == 1.0 else "More volatile than market"
            content_parts.append(f"**Beta:** {beta:.2f}")
            content_parts.append(f"- Interpretation: {beta_interpretation}")
            content_parts.append(f"- Market Correlation: {'Defensive stock' if beta < 0.8 else 'Moderate risk' if beta < 1.2 else 'Aggressive stock'}")
        else:
            content_parts.append(f"**Beta:** {beta}")
        content_parts.append("")
        
        # Value at Risk (VaR)
        var = risk_data.get('var', 'N/A')
        if isinstance(var, (int, float)):
            content_parts.append(f"**Value at Risk (VaR):** {var:.2f}%")
            content_parts.append(f"- Interpretation: Estimated maximum loss over the next trading day with 95% confidence")
            content_parts.append(f"- Risk Assessment: {'Low risk' if var < 2.0 else 'Moderate risk' if var < 4.0 else 'High risk'}")
        else:
            content_parts.append(f"**Value at Risk:** {var}")
        content_parts.append("")
        
        # ========== SECTION 3: SENTIMENT ANALYSIS ==========
        content_parts.append("# 💭 Market Sentiment Analysis\n")
        
        # Fear & Greed Index
        fear_greed = emotion_data.get("fear_greed_index", {})
        fg_index = fear_greed.get('index', 'N/A')
        fg_label = fear_greed.get('label', 'N/A')
        if isinstance(fg_index, (int, float)):
            fg_emoji = "😱" if fg_index < 25 else "😰" if fg_index < 45 else "😐" if fg_index < 55 else "😃" if fg_index < 75 else "🤩"
            content_parts.append(f"**Fear & Greed Index:** {fg_emoji} {fg_index} - {fg_label}")
            content_parts.append(f"- Interpretation: {'Extreme Fear - Potential buying opportunity' if fg_index < 25 else 'Fear - Market pessimism' if fg_index < 45 else 'Neutral - Balanced sentiment' if fg_index < 55 else 'Greed - Market optimism' if fg_index < 75 else 'Extreme Greed - Potential correction ahead'}")
        else:
            content_parts.append(f"**Fear & Greed Index:** {fg_index}")
        content_parts.append("")
        
        # News Sentiment
        news_sentiment = emotion_data.get('news_sentiment', 'N/A')
        if isinstance(news_sentiment, dict):
            overall = news_sentiment.get('overall_sentiment', 'N/A')
            score = news_sentiment.get('sentiment_score', 'N/A')
            count = news_sentiment.get('news_count', 0)
            sentiment_emoji = "🟢" if overall == "POSITIVE" else "🔴" if overall == "NEGATIVE" else "🟡"
            content_parts.append(f"**News Sentiment:** {sentiment_emoji} {overall}")
            content_parts.append(f"- Sentiment Score: {score}")
            content_parts.append(f"- Articles Analyzed: {count}")
            if count == 0:
                content_parts.append("- Note: Limited news data available")
        else:
            content_parts.append(f"**News Sentiment:** {news_sentiment}")
        content_parts.append("")
        
        # Market Sentiment
        market_sentiment = emotion_data.get('market_sentiment', 'N/A')
        if isinstance(market_sentiment, dict):
            price_sentiment = market_sentiment.get('price_sentiment', 'N/A')
            volume_sentiment = market_sentiment.get('volume_sentiment', 'N/A')
            price_change = market_sentiment.get('price_change', 'N/A')
            
            price_emoji = "🟢" if price_sentiment == "BULLISH" else "🔴" if price_sentiment == "BEARISH" else "🟡"
            content_parts.append(f"**Market Sentiment:** {price_emoji} {price_sentiment}")
            content_parts.append(f"- Volume Sentiment: {volume_sentiment}")
            content_parts.append(f"- Price Change: {price_change}%")
            content_parts.append(f"- Interpretation: {price_sentiment} price action with {volume_sentiment} trading interest")
        else:
            content_parts.append(f"**Market Sentiment:** {market_sentiment}")
        content_parts.append("")
        
        # ========== SECTION 4: FUNDAMENTAL DATA ==========
        content_parts.append("# 📈 Fundamental Data\n")
        
        # Market Data
        volume = stock_data.get('volume', 'N/A')
        market_cap = stock_data.get('market_cap', 'N/A')
        
        if isinstance(volume, (int, float)) and volume > 0:
            if volume >= 1e9:
                volume_str = f"{volume/1e9:.2f}B"
            elif volume >= 1e6:
                volume_str = f"{volume/1e6:.2f}M"
            elif volume >= 1e3:
                volume_str = f"{volume/1e3:.2f}K"
            else:
                volume_str = f"{volume:,.0f}"
            content_parts.append(f"**Trading Volume:** {volume_str}")
            content_parts.append(f"- Liquidity: {'High liquidity' if volume > 10e6 else 'Moderate liquidity' if volume > 1e6 else 'Low liquidity'}")
        else:
            content_parts.append(f"**Volume:** {volume}")
        content_parts.append("")
        
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            if market_cap >= 1e12:
                cap_str = f"${market_cap/1e12:.2f}T"
                cap_category = "Mega Cap"
            elif market_cap >= 200e9:
                cap_str = f"${market_cap/1e9:.2f}B"
                cap_category = "Large Cap"
            elif market_cap >= 10e9:
                cap_str = f"${market_cap/1e9:.2f}B"
                cap_category = "Mid Cap"
            elif market_cap >= 2e9:
                cap_str = f"${market_cap/1e9:.2f}B"
                cap_category = "Small Cap"
            else:
                cap_str = f"${market_cap/1e6:.2f}M"
                cap_category = "Micro Cap"
            content_parts.append(f"**Market Capitalization:** {cap_str}")
            content_parts.append(f"- Category: {cap_category}")
        else:
            content_parts.append(f"**Market Cap:** {market_cap}")
        content_parts.append("")
        
        content_parts.append(f"**PE Ratio:** {stock_data.get('pe_ratio', 'N/A')}")
        if stock_data.get('pe_ratio') and isinstance(stock_data.get('pe_ratio'), (int, float)):
            pe = stock_data.get('pe_ratio')
            content_parts.append(f"- Valuation: {'Undervalued' if pe < 15 else 'Fair value' if pe < 25 else 'Overvalued'}")
        content_parts.append("")
        
        # ========== SECTION 5: CONCLUSION ==========
        content_parts.append("# 📝 Investment Conclusion\n")
        
        content_parts.append(f"**Trading Recommendation:** {signal_emoji} {trading_signal}")
        content_parts.append(f"**Risk Level:** {risk_emoji} {risk_level}")
        content_parts.append(f"**Confidence:** {confidence:.1%}")
        content_parts.append("")
        
        content_parts.append("**Key Takeaways:**")
        # Generate key takeaways based on analysis
        takeaways = []
        if isinstance(rsi_value, (int, float)):
            if rsi_value < 30:
                takeaways.append("- RSI indicates oversold conditions - potential buying opportunity")
            elif rsi_value > 70:
                takeaways.append("- RSI indicates overbought conditions - caution advised")
        
        if risk_level == "LOW":
            takeaways.append("- Low risk profile suitable for conservative investors")
        elif risk_level == "HIGH":
            takeaways.append("- High risk profile - suitable only for risk-tolerant investors")
        
        if isinstance(fg_index, (int, float)):
            if fg_index > 75:
                takeaways.append("- Extreme greed in market - potential correction ahead")
            elif fg_index < 25:
                takeaways.append("- Extreme fear in market - potential buying opportunity")
        
        if takeaways:
            content_parts.extend(takeaways)
        else:
            content_parts.append("- Maintain diversified portfolio")
            content_parts.append("- Monitor market conditions regularly")
        
        return "\n".join(content_parts)
    
    def _generate_recommendations(self, analysis_data: dict, risk_data: dict, emotion_data: dict) -> str:
        """Generate investment recommendations"""
        recommendations = []
        
        # Technical Signal Recommendation
        signal = analysis_data.get("trading_signal", "HOLD")
        confidence = analysis_data.get("confidence_score", 0.5)
        
        if signal == "BUY" and confidence > 0.7:
            recommendations.append("Strong Buy: Technical indicators suggest upward momentum with high confidence.")
        elif signal == "BUY":
            recommendations.append("Buy: Technical indicators are positive but monitor closely.")
        elif signal == "SELL" and confidence > 0.7:
            recommendations.append("Strong Sell: Technical indicators suggest downward pressure with high confidence.")
        elif signal == "SELL":
            recommendations.append("Sell: Technical indicators are negative, consider reducing position.")
        else:
            recommendations.append("Hold: Technical indicators are neutral, maintain current position.")
        
        # Risk-based Recommendations
        risk_level = risk_data.get("risk_level", "MEDIUM")
        if risk_level == "HIGH":
            recommendations.append("High Risk: Consider position sizing and stop-loss strategies.")
        elif risk_level == "LOW":
            recommendations.append("Low Risk: Suitable for conservative investors.")
        
        # Sentiment-based Recommendations
        fear_greed = emotion_data.get("fear_greed_index", {}).get("index", 50)
        if fear_greed > 70:
            recommendations.append("Market Greed: Consider taking profits, market may be overbought.")
        elif fear_greed < 30:
            recommendations.append("Market Fear: Potential buying opportunity, market may be oversold.")
        
        return "\n".join(recommendations)
    
    async def get_user_reports(self, user_id: int, limit: int = 10) -> List[Report]:
        """
        Get all reports for current user
        
        Args:
            user_id: User ID
            limit: Maximum number of reports to return
            
        Returns:
            List of reports
        """
        try:
            # Query reports from database with stock information
            from sqlalchemy.orm import joinedload
            reports = self.db.query(ReportModel).options(
                joinedload(ReportModel.stock)
            ).filter(
                ReportModel.user_id == user_id
            ).order_by(ReportModel.created_at.desc()).limit(limit).all()
            
            result = []
            for report in reports:
                # Get stock information
                stock_info = None
                if report.stock:
                    stock_info = Stock(
                        id=report.stock.id,
                        symbol=report.stock.symbol,
                        name=report.stock.name,
                        current_price=report.stock.current_price,
                        sector=report.stock.sector
                    )
                
                result.append(Report(
                    id=report.id,
                    user_id=report.user_id,
                    stock_id=report.stock_id,
                    stock=stock_info,
                    title=report.title,
                    summary=report.summary,
                    content=report.content,
                    recommendations=report.recommendations,
                    risk_level=report.risk_level,
                    sentiment_score=report.sentiment_score,
                    technical_signal=report.technical_signal,
                    confidence_score=report.confidence_score,
                    details_json=report.details_json,
                    report_type=report.report_type,
                    created_at=report.created_at.isoformat()
                ))
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to get user reports: {str(e)}")
            raise Exception(f"Failed to get user reports: {str(e)}")
    
    async def get_report_summary(self, user_id: int) -> ReportSummary:
        """
        Get report summary for user
        
        Args:
            user_id: User ID
            
        Returns:
            Report summary
        """
        try:
            # Count different types of reports
            total_reports = self.db.query(ReportModel).filter(ReportModel.user_id == user_id).count()
            
            # Recent reports (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_reports = self.db.query(ReportModel).filter(
                and_(
                    ReportModel.user_id == user_id,
                    ReportModel.created_at >= recent_cutoff
                )
            ).count()
            
            # High confidence reports (confidence > 0.7)
            high_confidence_reports = self.db.query(ReportModel).filter(
                and_(
                    ReportModel.user_id == user_id,
                    ReportModel.confidence_score > 0.7
                )
            ).count()
            
            # Count signals
            buy_signals = self.db.query(ReportModel).filter(
                and_(
                    ReportModel.user_id == user_id,
                    ReportModel.technical_signal == "BUY"
                )
            ).count()
            
            sell_signals = self.db.query(ReportModel).filter(
                and_(
                    ReportModel.user_id == user_id,
                    ReportModel.technical_signal == "SELL"
                )
            ).count()
            
            hold_signals = self.db.query(ReportModel).filter(
                and_(
                    ReportModel.user_id == user_id,
                    ReportModel.technical_signal == "HOLD"
                )
            ).count()
            
            # Calculate risk and sentiment distribution
            risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
            sentiment_distribution = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
            
            # Get all reports for distribution calculation
            all_reports = self.db.query(ReportModel).filter(ReportModel.user_id == user_id).all()
            
            for report in all_reports:
                # Risk distribution
                if report.risk_level in risk_distribution:
                    risk_distribution[report.risk_level] += 1
                
                # Sentiment distribution (based on sentiment_score)
                if report.sentiment_score > 60:
                    sentiment_distribution["POSITIVE"] += 1
                elif report.sentiment_score < 40:
                    sentiment_distribution["NEGATIVE"] += 1
                else:
                    sentiment_distribution["NEUTRAL"] += 1
            
            return ReportSummary(
                total_reports=total_reports,
                recent_reports=recent_reports,
                high_confidence_reports=high_confidence_reports,
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                hold_signals=hold_signals,
                risk_distribution=risk_distribution,
                sentiment_distribution=sentiment_distribution
            )
        except Exception as e:
            self.logger.error(f"Failed to get report summary: {str(e)}")
            raise Exception(f"Failed to get report summary: {str(e)}")
    
    async def get_report_by_id(self, report_id: int, user_id: int) -> Optional[Report]:
        """
        Get a specific report by ID
        
        Args:
            report_id: Report ID
            user_id: User ID
            
        Returns:
            Report if found, None otherwise
        """
        try:
            report = self.db.query(ReportModel).filter(
                and_(
                    ReportModel.id == report_id,
                    ReportModel.user_id == user_id
                )
            ).first()
            
            if not report:
                return None
            
            return Report(
                id=report.id,
                user_id=report.user_id,
                stock_id=report.stock_id,
                title=report.title,
                summary=report.summary,
                risk_level=report.risk_level,
                sentiment_score=report.sentiment_score,
                technical_signal=report.technical_signal,
                confidence_score=report.confidence_score,
                details_json=report.details_json,
                report_type=report.report_type,
                created_at=report.created_at.isoformat()
            )
        except Exception as e:
            self.logger.error(f"Failed to get report {report_id}: {str(e)}")
            raise Exception(f"Failed to get report: {str(e)}")
    
    async def delete_report(self, report_id: int, user_id: int) -> None:
        """
        Delete a report
        
        Args:
            report_id: Report ID to delete
            user_id: User ID
        """
        try:
            report = self.db.query(ReportModel).filter(
                and_(
                    ReportModel.id == report_id,
                    ReportModel.user_id == user_id
                )
            ).first()
            
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            self.db.delete(report)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to delete report {report_id}: {str(e)}")
            raise Exception(f"Failed to delete report: {str(e)}")