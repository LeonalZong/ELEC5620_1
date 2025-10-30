"""
Portfolio Sentiment Agent
Prepares bounded news dataset for a user's entire portfolio with per-stock caps
to control token usage and latency. Uses DataCollectionAgent to backfill when
recent news is missing.
"""
from typing import Any, Dict, List
from datetime import datetime, timedelta

from app.agents.base_agent import BaseAgent
from app.agents.data_collection_agent import DataCollectionAgent
from app.database import SessionLocal
from app.models.portfolio import Portfolio as PortfolioModel
from app.models.stock import Stock as StockModel
from app.models.news import News as NewsModel


class PortfolioSentimentAgent(BaseAgent):
    def __init__(self, agent_id: str = "portfolio_sentiment", db=None):
        super().__init__(agent_id, "Portfolio Sentiment Agent")
        self.db = db or SessionLocal()

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build portfolio-wide news dataset with caps per holding.

        Args:
            task_data: {"user_id": int, "per_stock_limit": int=3, "days": int=7}
        """
        user_id: int = int(task_data.get("user_id"))
        per_stock_limit: int = int(task_data.get("per_stock_limit", 3))
        days: int = int(task_data.get("days", 7))

        db = self.db
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Fetch holdings
        holdings = db.query(PortfolioModel).filter(PortfolioModel.user_id == user_id).all()
        news_data: List[Dict[str, Any]] = []

        for h in holdings:
            stock: StockModel = db.query(StockModel).filter(StockModel.id == h.stock_id).first()
            if not stock:
                continue

            # Fetch limited recent news
            items = db.query(NewsModel).filter(
                NewsModel.stock_id == stock.id,
                NewsModel.published_at >= cutoff
            ).order_by(NewsModel.published_at.desc()).limit(per_stock_limit).all()

            # Auto collect if none
            if not items:
                try:
                    collector = DataCollectionAgent(db=db)
                    await collector.execute_task({"symbol": stock.symbol})
                    items = db.query(NewsModel).filter(
                        NewsModel.stock_id == stock.id,
                        NewsModel.published_at >= cutoff
                    ).order_by(NewsModel.published_at.desc()).limit(per_stock_limit).all()
                except Exception:
                    items = []

        for n in items:
                news_data.append({
                    "title": n.title,
                    "content": n.content or "",
                    "sentiment": "positive" if n.sentiment_score and n.sentiment_score > 0.3 else ("negative" if n.sentiment_score and n.sentiment_score < -0.3 else "neutral"),
                    "published_at": n.published_at.isoformat(),
                    "url": n.url,
                    "source": n.source or "",
                    "symbol": stock.symbol
                })
        # Build brief and top_news (one per symbol, most recent)
        from collections import defaultdict
        by_symbol: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for a in news_data:
            by_symbol[a["symbol"]].append(a)
        for sym in by_symbol:
            by_symbol[sym].sort(key=lambda x: x.get("published_at", ""), reverse=True)
        # brief like: NVDA x3, AAPL x2, MSFT x2 ...
        parts = [f"{sym} x{len(arts)}" for sym, arts in sorted(by_symbol.items(), key=lambda kv: len(kv[1]), reverse=True)[:5]]
        news_brief = "; ".join(parts)
        top_news: List[Dict[str, Any]] = []
        for sym, arts in by_symbol.items():
            if arts:
                top = arts[0]
                top_news.append({
                    "symbol": sym,
                    "title": top.get("title"),
                    "url": top.get("url"),
                    "source": top.get("source"),
                    "published_at": top.get("published_at")
                })

        return {"status": "success", "news_data": news_data, "top_news": top_news, "news_brief": news_brief, "per_stock_limit": per_stock_limit, "days": days}


