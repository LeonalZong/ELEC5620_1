"""
Report Generation Agent
Generates comprehensive analysis reports
"""
from typing import Dict, Any, List
from datetime import datetime

from app.agents.base_agent import BaseAgent

class ReportGenerateAgent(BaseAgent):
    """
    Agent responsible for generating analysis reports
    """
    
    def __init__(self, agent_id: str = "report_generate"):
        """
        Initialize Report Generation Agent
        
        Args:
            agent_id: Agent identifier
        """
        super().__init__(agent_id, "Report Generation Agent")
        from app.services.ai_analysis_service import AIAnalysisService
        self.ai_service = AIAnalysisService()
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute report generation task
        
        Args:
            task_data: Task parameters including all analysis results
            
        Returns:
            Generated report
        """
        symbol = task_data.get("symbol", "")
        data_collection = task_data.get("data_collection", {})
        analysis = task_data.get("analysis", {})
        risk_analysis = task_data.get("risk_analysis", {})
        emotional_analysis = task_data.get("emotional_analysis", {})
        
        # Generate report sections
        executive_summary = await self.generate_executive_summary(symbol, analysis, risk_analysis, emotional_analysis)
        technical_summary = self.generate_technical_summary(analysis)
        risk_summary = self.generate_risk_summary(risk_analysis)
        sentiment_summary = self.generate_sentiment_summary(emotional_analysis)
        recommendations = self.generate_recommendations(analysis, risk_analysis, emotional_analysis)
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(analysis, risk_analysis, emotional_analysis)
        
        return {
            "symbol": symbol,
            "title": f"Analysis Report for {symbol}",
            "executive_summary": executive_summary,
            "technical_analysis": technical_summary,
            "risk_analysis": risk_summary,
            "sentiment_analysis": sentiment_summary,
            "recommendations": recommendations,
            "overall_score": overall_score,
            "report_type": "COMPREHENSIVE",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def generate_executive_summary(self, symbol: str, analysis: Dict[str, Any], risk: Dict[str, Any], sentiment: Dict[str, Any]) -> str:
        """Generate executive summary using AI"""
        try:
            # Use AI service to generate summary
            summary = await self.ai_service.generate_executive_summary(
                symbol, analysis, risk, sentiment
            )
            return summary
        except Exception as e:
            self.logger.error(f"Failed to generate executive summary: {str(e)}")
            # Fallback to simple summary
            trading_signal = analysis.get("trading_signal", "HOLD")
            confidence = analysis.get("confidence_score", 0.5)
            risk_level = risk.get("risk_level", "MEDIUM")
            fear_greed = sentiment.get("fear_greed_index", {}).get("category", "NEUTRAL")
            
            return f"""
            Executive Summary for {symbol}:
            
            Trading Signal: {trading_signal}
            Confidence Level: {confidence:.1%}
            Risk Level: {risk_level}
            Market Sentiment: {fear_greed}
            
            This analysis provides a comprehensive view of {symbol}'s current market position,
            technical indicators, risk profile, and market sentiment to guide investment decisions.
            """
    
    def generate_technical_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate technical analysis summary"""
        technical = analysis.get("technical_analysis", {})
        
        return {
            "rsi": technical.get("rsi", 50),
            "trend": technical.get("trend", "SIDEWAYS"),
            "moving_averages": technical.get("moving_averages", {}),
            "macd": technical.get("macd", {}),
            "signal": technical.get("trading_signal", "HOLD")
        }
    
    def generate_risk_summary(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk analysis summary"""
        return {
            "volatility": risk_analysis.get("volatility", 0),
            "beta": risk_analysis.get("beta", 1.0),
            "var": risk_analysis.get("var", 0),
            "risk_score": risk_analysis.get("risk_score", 50),
            "risk_level": risk_analysis.get("risk_level", "MEDIUM")
        }
    
    def generate_sentiment_summary(self, emotional_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sentiment analysis summary"""
        return {
            "news_sentiment": emotional_analysis.get("news_sentiment", {}),
            "market_sentiment": emotional_analysis.get("market_sentiment", {}),
            "fear_greed_index": emotional_analysis.get("fear_greed_index", {}),
            "emotional_signal": emotional_analysis.get("emotional_signal", "HOLD")
        }
    
    def generate_recommendations(self, analysis: Dict[str, Any], risk: Dict[str, Any], sentiment: Dict[str, Any]) -> List[str]:
        """Generate investment recommendations"""
        recommendations = []
        
        # Technical recommendations
        trading_signal = analysis.get("trading_signal", "HOLD")
        if trading_signal == "BUY":
            recommendations.append("Consider buying based on technical indicators")
        elif trading_signal == "SELL":
            recommendations.append("Consider selling based on technical indicators")
        
        # Risk recommendations
        risk_level = risk.get("risk_level", "MEDIUM")
        if risk_level == "HIGH":
            recommendations.append("High risk investment - consider position sizing")
        elif risk_level == "LOW":
            recommendations.append("Low risk investment - suitable for conservative portfolios")
        
        # Sentiment recommendations
        fear_greed = sentiment.get("fear_greed_index", {}).get("category", "NEUTRAL")
        if fear_greed == "EXTREME_FEAR":
            recommendations.append("Market shows extreme fear - potential buying opportunity")
        elif fear_greed == "EXTREME_GREED":
            recommendations.append("Market shows extreme greed - consider taking profits")
        
        return recommendations
    
    def calculate_overall_score(self, analysis: Dict[str, Any], risk: Dict[str, Any], sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall investment score"""
        # Technical score (40%)
        technical_score = 50  # Base score
        trading_signal = analysis.get("trading_signal", "HOLD")
        if trading_signal == "BUY":
            technical_score += 20
        elif trading_signal == "SELL":
            technical_score -= 20
        
        # Risk score (30%)
        risk_score = 100 - risk.get("risk_score", 50)  # Invert risk score
        
        # Sentiment score (30%)
        fear_greed = sentiment.get("fear_greed_index", {}).get("index", 50)
        sentiment_score = fear_greed
        
        # Weighted average
        overall = (technical_score * 0.4) + (risk_score * 0.3) + (sentiment_score * 0.3)
        
        # Determine rating
        if overall >= 80:
            rating = "EXCELLENT"
        elif overall >= 60:
            rating = "GOOD"
        elif overall >= 40:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        return {
            "score": round(overall, 1),
            "rating": rating,
            "technical_component": round(technical_score, 1),
            "risk_component": round(risk_score, 1),
            "sentiment_component": round(sentiment_score, 1)
        }