"""
AI Analysis Service
Uses OpenAI for intelligent stock analysis
"""
import openai
from typing import Dict, Any, List
import json
import logging
from app.config import settings

class AIAnalysisService:
    """
    Service for AI-powered stock analysis using OpenAI
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_analysis_service")
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def analyze_stock_with_ai(self, stock_data: Dict[str, Any], news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use OpenAI to analyze stock data and news
        
        Args:
            stock_data: Stock price and technical data
            news_data: News articles about the stock
            
        Returns:
            AI analysis results
        """
        try:
            # Prepare data for AI analysis
            analysis_prompt = self._create_analysis_prompt(stock_data, news_data)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional financial analyst with expertise in stock market analysis."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            ai_analysis = response.choices[0].message.content
            
            # Parse AI response
            return self._parse_ai_response(ai_analysis)
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {str(e)}")
            return {"error": str(e), "analysis": "AI analysis unavailable"}
    
    def _create_analysis_prompt(self, stock_data: Dict[str, Any], news_data: List[Dict[str, Any]]) -> str:
        """
        Create analysis prompt for OpenAI
        
        Args:
            stock_data: Stock data
            news_data: News data
            
        Returns:
            Formatted prompt
        """
        symbol = stock_data.get("symbol", "Unknown")
        current_price = stock_data.get("current_price", 0)
        price_change = stock_data.get("price_change_percent", 0)
        volume = stock_data.get("volume", 0)
        
        # Format news headlines
        news_headlines = []
        for article in news_data[:5]:  # Top 5 articles
            news_headlines.append(f"- {article.get('title', '')} ({article.get('sentiment', 'neutral')})")
        
        prompt = f"""
        Analyze the following stock data and provide a comprehensive analysis:
        
        Stock: {symbol}
        Current Price: ${current_price}
        Price Change: {price_change}%
        Volume: {volume:,}
        
        Recent News:
        {chr(10).join(news_headlines)}
        
        Please provide:
        1. Technical Analysis Summary
        2. Fundamental Analysis Summary  
        3. News Sentiment Impact
        4. Risk Assessment
        5. Investment Recommendation (BUY/SELL/HOLD)
        6. Confidence Level (1-10)
        7. Key Factors to Watch
        
        Format your response as JSON with these fields:
        {{
            "technical_analysis": "summary",
            "fundamental_analysis": "summary", 
            "news_sentiment": "positive/negative/neutral",
            "risk_level": "low/medium/high",
            "recommendation": "BUY/SELL/HOLD",
            "confidence": 8,
            "key_factors": ["factor1", "factor2", "factor3"]
        }}
        """
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse AI response and extract structured data
        
        Args:
            ai_response: Raw AI response
            
        Returns:
            Parsed analysis data
        """
        try:
            # Try to extract JSON from response
            if "{" in ai_response and "}" in ai_response:
                start = ai_response.find("{")
                end = ai_response.rfind("}") + 1
                json_str = ai_response[start:end]
                return json.loads(json_str)
            else:
                # Fallback to text parsing
                return {
                    "technical_analysis": "AI analysis completed",
                    "fundamental_analysis": "AI analysis completed",
                    "news_sentiment": "neutral",
                    "risk_level": "medium",
                    "recommendation": "HOLD",
                    "confidence": 5,
                    "key_factors": ["AI analysis completed"],
                    "raw_response": ai_response
                }
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {str(e)}")
            return {
                "error": "Failed to parse AI response",
                "raw_response": ai_response
            }
    
    async def generate_investment_report(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate a comprehensive investment report
        
        Args:
            analysis_data: Analysis results
            
        Returns:
            Formatted report
        """
        try:
            report_prompt = f"""
            Create a professional investment report based on this analysis:
            
            {json.dumps(analysis_data, indent=2)}
            
            Format as a comprehensive report with:
            - Executive Summary
            - Technical Analysis
            - Fundamental Analysis
            - Risk Assessment
            - Investment Recommendation
            - Conclusion
            
            Keep it professional and actionable for investors.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior financial analyst writing investment reports."},
                    {"role": "user", "content": report_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            return f"Report generation failed: {str(e)}"
    
    async def generate_executive_summary(
        self,
        symbol: str,
        analysis: Dict[str, Any],
        risk: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> str:
        """
        Generate an executive summary using OpenAI
        """
        try:
            prompt = f"""
            Generate a concise executive summary for {symbol} stock based on the following analysis:

            Technical Analysis: {json.dumps(analysis.get('technical_analysis', {}), indent=2)}
            Risk Analysis: {json.dumps(risk, indent=2)}
            Sentiment Analysis: {json.dumps(sentiment, indent=2)}

            Please provide a professional executive summary that includes:
            1. Key findings and insights
            2. Trading signal and confidence level
            3. Risk assessment
            4. Market sentiment impact
            5. Investment recommendation

            Keep it concise (2-3 paragraphs) and actionable for investors.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior financial analyst writing executive summaries for investment reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Executive summary generation failed: {str(e)}")
            return f"Executive summary generation failed: {str(e)}"
    
    async def analyze_news_sentiment(self, news_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment of news articles using OpenAI
        """
        if not news_articles:
            return {"overall_sentiment": "NEUTRAL", "sentiment_score": 0.5, "news_count": 0, "confidence": 0.0}

        try:
            # Prepare news text for analysis
            news_texts = []
            for article in news_articles[:5]:  # Limit to first 5 articles
                title = article.get('title', '')
                content = article.get('content', '')
                news_texts.append(f"Title: {title}\nContent: {content}")
            
            combined_news = "\n---\n".join(news_texts)
            
            prompt = f"""
            Analyze the overall sentiment of the following news articles about a stock.
            Provide an overall sentiment (POSITIVE, NEGATIVE, NEUTRAL), a sentiment score from 0 to 1 (0 being very negative, 1 being very positive),
            and a confidence score for your analysis.

            News Articles:
            {combined_news}

            Return the result as a JSON object with keys: "overall_sentiment", "sentiment_score", "confidence".
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial news sentiment analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result["news_count"] = len(news_articles)
            return result
            
        except Exception as e:
            self.logger.error(f"News sentiment analysis failed: {str(e)}")
            return {"overall_sentiment": "NEUTRAL", "sentiment_score": 0.5, "news_count": len(news_articles), "confidence": 0.0}
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get Fear & Greed Index using OpenAI
        """
        try:
            prompt = """
            What is the current Fear & Greed Index for the stock market?
            Provide a numerical index (0-100, 0=Extreme Fear, 100=Extreme Greed),
            and a corresponding sentiment (Extreme Fear, Fear, Neutral, Greed, Extreme Greed).
            Also, provide a brief explanation of the current market conditions.
            
            Return the result as a JSON object with keys: "index", "sentiment", "explanation".
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a market sentiment analyst with access to current market data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"Fear & Greed Index analysis failed: {str(e)}")
            return {"index": 50, "sentiment": "Neutral", "explanation": "Could not retrieve current market sentiment."}
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """
        Get overall market sentiment using OpenAI
        """
        try:
            prompt = """
            Analyze the current overall market sentiment based on recent market conditions, economic indicators, and global events.
            Provide a sentiment score (0-100, 0=Very Bearish, 100=Very Bullish) and a brief explanation.
            
            Return the result as a JSON object with keys: "sentiment_score", "sentiment_level", "explanation".
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a market analyst with expertise in macroeconomic conditions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"Market sentiment analysis failed: {str(e)}")
            return {"sentiment_score": 50, "sentiment_level": "Neutral", "explanation": "Could not analyze current market sentiment."}
    
    def analyze_stock_technical(self, symbol: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze stock technical indicators
        
        Args:
            symbol: Stock symbol
            price_data: Price data with changes
            
        Returns:
            Technical analysis results
        """
        try:
            # Calculate technical indicators
            daily_change = price_data.get('daily_change', 0)
            weekly_change = price_data.get('weekly_change', 0)
            monthly_change = price_data.get('monthly_change', 0)
            
            # Determine trend
            if daily_change > 0 and weekly_change > 0 and monthly_change > 0:
                trend = "strong_uptrend"
                strength = "strong"
            elif daily_change > 0 and weekly_change > 0:
                trend = "uptrend"
                strength = "moderate"
            elif daily_change < 0 and weekly_change < 0 and monthly_change < 0:
                trend = "strong_downtrend"
                strength = "strong"
            elif daily_change < 0 and weekly_change < 0:
                trend = "downtrend"
                strength = "moderate"
            else:
                trend = "sideways"
                strength = "weak"
            
            # Generate recommendation
            if trend in ["strong_uptrend", "uptrend"]:
                recommendation = "BUY"
            elif trend in ["strong_downtrend", "downtrend"]:
                recommendation = "SELL"
            else:
                recommendation = "HOLD"
            
            return {
                "trend": trend,
                "strength": strength,
                "recommendation": recommendation,
                "daily_change": daily_change,
                "weekly_change": weekly_change,
                "monthly_change": monthly_change,
                "analysis": f"Stock {symbol} shows {trend} with {strength} momentum"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze technical indicators: {str(e)}")
            return {
                "trend": "unknown",
                "strength": "unknown",
                "recommendation": "HOLD",
                "error": str(e)
            }
    
    def analyze_stock_risk(self, symbol: str, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze stock risk factors
        
        Args:
            symbol: Stock symbol
            risk_data: Risk-related data
            
        Returns:
            Risk analysis results
        """
        try:
            volatility = risk_data.get('volatility', 0)
            beta = risk_data.get('beta', 1.0)
            daily_change = abs(risk_data.get('daily_change', 0))
            weekly_change = abs(risk_data.get('weekly_change', 0))
            
            # Calculate risk level
            risk_score = 0
            
            # Volatility risk
            if volatility > 0.3:
                risk_score += 3
            elif volatility > 0.2:
                risk_score += 2
            elif volatility > 0.1:
                risk_score += 1
            
            # Beta risk
            if beta > 1.5:
                risk_score += 2
            elif beta > 1.2:
                risk_score += 1
            elif beta < 0.8:
                risk_score -= 1
            
            # Price movement risk
            if daily_change > 5:
                risk_score += 2
            elif daily_change > 3:
                risk_score += 1
            
            if weekly_change > 10:
                risk_score += 2
            elif weekly_change > 5:
                risk_score += 1
            
            # Determine risk level
            if risk_score >= 5:
                risk_level = "high"
            elif risk_score >= 3:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # Identify risk factors
            risk_factors = []
            if volatility > 0.2:
                risk_factors.append("high_volatility")
            if beta > 1.2:
                risk_factors.append("high_beta")
            if daily_change > 3:
                risk_factors.append("high_daily_volatility")
            
            # Generate recommendation
            if risk_level == "high":
                recommendation = "High risk - consider position sizing"
            elif risk_level == "medium":
                recommendation = "Moderate risk - monitor closely"
            else:
                recommendation = "Low risk - suitable for conservative investors"
            
            return {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "volatility": volatility,
                "beta": beta,
                "recommendation": recommendation,
                "analysis": f"Stock {symbol} has {risk_level} risk level"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze risk: {str(e)}")
            return {
                "risk_level": "unknown",
                "risk_score": 0,
                "risk_factors": [],
                "recommendation": "Unable to assess risk",
                "error": str(e)
            }
    
    def analyze_market_sentiment(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze market sentiment from news data
        
        Args:
            news_data: List of news articles with sentiment
            
        Returns:
            Market sentiment analysis
        """
        try:
            if not news_data:
                return {
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "key_factors": [],
                    "confidence": 0.0
                }
            
            # Count sentiment types
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            key_factors = []
            
            for news in news_data:
                sentiment = news.get('sentiment', 'neutral')
                if sentiment == 'positive':
                    positive_count += 1
                elif sentiment == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1
                
                # Extract key factors from title
                title = news.get('title', '')
                if 'earnings' in title.lower():
                    key_factors.append('earnings_news')
                if 'revenue' in title.lower():
                    key_factors.append('revenue_news')
                if 'growth' in title.lower():
                    key_factors.append('growth_news')
                if 'decline' in title.lower():
                    key_factors.append('decline_news')
            
            total_news = len(news_data)
            
            # Calculate sentiment score
            sentiment_score = (positive_count - negative_count) / total_news if total_news > 0 else 0
            
            # Determine overall sentiment
            if sentiment_score > 0.3:
                overall_sentiment = "positive"
            elif sentiment_score < -0.3:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
            
            # Calculate confidence
            confidence = max(positive_count, negative_count) / total_news if total_news > 0 else 0
            
            return {
                "overall_sentiment": overall_sentiment,
                "sentiment_score": sentiment_score,
                "key_factors": list(set(key_factors)),
                "confidence": confidence,
                "positive_news": positive_count,
                "negative_news": negative_count,
                "neutral_news": neutral_count,
                "analysis": f"Market sentiment is {overall_sentiment} with {confidence:.2f} confidence"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze market sentiment: {str(e)}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "key_factors": [],
                "confidence": 0.0,
                "error": str(e)
            }
