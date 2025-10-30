"""
Data Update Tasks
Periodic data collection and storage tasks
"""
from celery import current_task
from app.celery_app import celery_app
from app.database import SessionLocal
from app.agents.agent_manager import AgentManager
from app.services.stock_service import StockService
from app.models.tracked_stock import TrackedStock as TrackedStockModel
from app.models.stock import Stock as StockModel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.data_update_tasks.update_stock_data")
def update_stock_data(self):
    """
    Update stock data for all tracked stocks
    Runs every hour
    """
    try:
        logger.info("Starting stock data update task")
        
        db = SessionLocal()
        try:
            # Initialize services
            stock_service = StockService(db)
            agent_manager = AgentManager(db)
            
            # Get all tracked stocks
            tracked_stocks = db.query(TrackedStockModel).filter(
                TrackedStockModel.is_active == True
            ).all()
            
            logger.info(f"Updating data for {len(tracked_stocks)} tracked stocks")
            
            updated_count = 0
            failed_count = 0
            
            for i, tracked_stock in enumerate(tracked_stocks):
                try:
                    # Update task progress
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": tracked_stock.stock.symbol,
                            "progress": f"{i+1}/{len(tracked_stocks)}",
                            "updated": updated_count,
                            "failed": failed_count
                        }
                    )
                    
                    # Collect fresh data using agent manager
                    result = agent_manager.run_stock_analysis_pipeline(
                        user_id=tracked_stock.user_id,
                        stock_symbol=tracked_stock.stock.symbol
                    )
                    
                    if result and result.get("status") == "success":
                        updated_count += 1
                        logger.info(f"Updated data for {tracked_stock.stock.symbol}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to update {tracked_stock.stock.symbol}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error updating {tracked_stock.stock.symbol}: {str(e)}")
                    continue
            
            logger.info(f"Stock data update completed. Updated: {updated_count}, Failed: {failed_count}")
            
            return {
                "status": "completed",
                "total_stocks": len(tracked_stocks),
                "updated": updated_count,
                "failed": failed_count,
                "message": "Stock data update completed successfully"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Stock data update task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise

@celery_app.task(bind=True, name="app.tasks.data_update_tasks.update_news_data")
def update_news_data(self):
    """
    Update news data for tracked stocks
    Runs every 2 hours
    """
    try:
        logger.info("Starting news data update task")
        
        db = SessionLocal()
        try:
            # Initialize services
            agent_manager = AgentManager(db)
            
            # Get unique stock symbols from tracked stocks
            tracked_stocks = db.query(TrackedStockModel).filter(
                TrackedStockModel.is_active == True
            ).all()
            
            unique_symbols = list(set([ts.stock.symbol for ts in tracked_stocks]))
            logger.info(f"Updating news for {len(unique_symbols)} stocks")
            
            updated_count = 0
            failed_count = 0
            
            for i, symbol in enumerate(unique_symbols):
                try:
                    # Update task progress
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": symbol,
                            "progress": f"{i+1}/{len(unique_symbols)}",
                            "updated": updated_count,
                            "failed": failed_count
                        }
                    )
                    
                    # Get first user who tracks this stock for data collection
                    first_tracked = next((ts for ts in tracked_stocks if ts.stock.symbol == symbol), None)
                    if not first_tracked:
                        continue
                    
                    # Collect news data
                    result = agent_manager.run_stock_analysis_pipeline(
                        user_id=first_tracked.user_id,
                        stock_symbol=symbol
                    )
                    
                    if result and result.get("status") == "success":
                        updated_count += 1
                        logger.info(f"Updated news for {symbol}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to update news for {symbol}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error updating news for {symbol}: {str(e)}")
                    continue
            
            logger.info(f"News data update completed. Updated: {updated_count}, Failed: {failed_count}")
            
            return {
                "status": "completed",
                "total_stocks": len(unique_symbols),
                "updated": updated_count,
                "failed": failed_count,
                "message": "News data update completed successfully"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"News data update task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise

@celery_app.task(bind=True, name="app.tasks.data_update_tasks.cleanup_old_data")
def cleanup_old_data(self):
    """
    Clean up old data to maintain database performance
    Runs weekly
    """
    try:
        logger.info("Starting data cleanup task")
        
        db = SessionLocal()
        try:
            from app.models.news import News as NewsModel
            from app.models.stock_data import StockData as StockDataModel
            from app.models.alert import Alert as AlertModel
            
            # Clean up old news (older than 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            old_news = db.query(NewsModel).filter(
                NewsModel.created_at < cutoff_date
            ).count()
            
            if old_news > 0:
                db.query(NewsModel).filter(
                    NewsModel.created_at < cutoff_date
                ).delete()
                logger.info(f"Deleted {old_news} old news articles")
            
            # Clean up old stock data (older than 90 days)
            stock_cutoff = datetime.utcnow() - timedelta(days=90)
            old_stock_data = db.query(StockDataModel).filter(
                StockDataModel.timestamp < stock_cutoff
            ).count()
            
            if old_stock_data > 0:
                db.query(StockDataModel).filter(
                    StockDataModel.timestamp < stock_cutoff
                ).delete()
                logger.info(f"Deleted {old_stock_data} old stock data records")
            
            # Clean up expired alerts (older than 7 days)
            alert_cutoff = datetime.utcnow() - timedelta(days=7)
            old_alerts = db.query(AlertModel).filter(
                AlertModel.created_at < alert_cutoff,
                AlertModel.status == "EXPIRED"
            ).count()
            
            if old_alerts > 0:
                db.query(AlertModel).filter(
                    AlertModel.created_at < alert_cutoff,
                    AlertModel.status == "EXPIRED"
                ).delete()
                logger.info(f"Deleted {old_alerts} expired alerts")
            
            db.commit()
            
            logger.info("Data cleanup completed successfully")
            
            return {
                "status": "completed",
                "old_news_deleted": old_news,
                "old_stock_data_deleted": old_stock_data,
                "expired_alerts_deleted": old_alerts,
                "message": "Data cleanup completed successfully"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Data cleanup task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise










