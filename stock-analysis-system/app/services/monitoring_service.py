"""
System Monitoring Service
Comprehensive monitoring for stock analysis system
"""
import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.database import get_db_session, get_connection_pool_status
from app.core.logging import get_logger
from app.core.exceptions import DatabaseException
from app.models.user import User
from app.models.stock import Stock
from app.models.alert import Alert
from app.models.report import Report
from app.models.news import News
from app.models.stock_data import StockData

logger = get_logger("monitoring")

class SystemMonitor:
    """
    System performance monitoring
    """
    
    def __init__(self):
        self.logger = get_logger("system_monitor")
        self.metrics_history = []
        self.max_history = 1000  # Keep last 1000 metrics
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system performance metrics
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": cpu_freq.current if cpu_freq else None,
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "pid": process.pid,
                    "memory_percent": process.memory_percent(),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                    "create_time": process.create_time()
                }
            }
            
            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {str(e)}")
            raise DatabaseException(f"Failed to get system metrics", details={"error": str(e)})
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get metrics history for the specified hours
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            metric for metric in self.metrics_history
            if datetime.fromisoformat(metric["timestamp"]) > cutoff_time
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary statistics
        """
        if not self.metrics_history:
            return {"status": "no_data"}
        
        recent_metrics = self.metrics_history[-100:]  # Last 100 metrics
        
        cpu_values = [m["cpu"]["percent"] for m in recent_metrics]
        memory_values = [m["memory"]["percent"] for m in recent_metrics]
        disk_values = [m["disk"]["percent"] for m in recent_metrics]
        
        return {
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0
            },
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": sum(memory_values) / len(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0
            },
            "disk": {
                "current": disk_values[-1] if disk_values else 0,
                "average": sum(disk_values) / len(disk_values) if disk_values else 0,
                "max": max(disk_values) if disk_values else 0,
                "min": min(disk_values) if disk_values else 0
            },
            "sample_count": len(recent_metrics),
            "time_range": {
                "start": recent_metrics[0]["timestamp"] if recent_metrics else None,
                "end": recent_metrics[-1]["timestamp"] if recent_metrics else None
            }
        }


class DatabaseMonitor:
    """
    Database performance monitoring
    """
    
    def __init__(self):
        self.logger = get_logger("database_monitor")
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """
        Get database performance metrics
        """
        try:
            with get_db_session() as db:
                # Connection pool status
                pool_status = get_connection_pool_status()
                
                # Database size
                db_size = self._get_database_size(db)
                
                # Table statistics
                table_stats = self._get_table_statistics(db)
                
                # Query performance
                query_performance = self._get_query_performance(db)
                
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "connection_pool": pool_status,
                    "database_size": db_size,
                    "table_statistics": table_stats,
                    "query_performance": query_performance
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database metrics: {str(e)}")
            raise DatabaseException(f"Failed to get database metrics", details={"error": str(e)})
    
    def _get_database_size(self, db: Session) -> Dict[str, Any]:
        """Get database size information"""
        try:
            # Get database size (MySQL specific)
            result = db.execute(text("""
                SELECT 
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """)).fetchone()
            
            return {
                "size_mb": result[0] if result else 0,
                "tables": len(self._get_table_list(db))
            }
        except Exception as e:
            self.logger.warning(f"Could not get database size: {str(e)}")
            return {"size_mb": 0, "tables": 0}
    
    def _get_table_list(self, db: Session) -> List[str]:
        """Get list of tables in database"""
        try:
            result = db.execute(text("SHOW TABLES")).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            self.logger.warning(f"Could not get table list: {str(e)}")
            return []
    
    def _get_table_statistics(self, db: Session) -> Dict[str, Any]:
        """Get table statistics"""
        try:
            stats = {}
            
            # User table stats
            user_count = db.query(User).count()
            stats["users"] = {"count": user_count}
            
            # Stock table stats
            stock_count = db.query(Stock).count()
            stats["stocks"] = {"count": stock_count}
            
            # Alert table stats
            alert_count = db.query(Alert).count()
            pending_alerts = db.query(Alert).filter(Alert.status == "PENDING").count()
            stats["alerts"] = {"total": alert_count, "pending": pending_alerts}
            
            # Report table stats
            report_count = db.query(Report).count()
            stats["reports"] = {"count": report_count}
            
            # News table stats
            news_count = db.query(News).count()
            stats["news"] = {"count": news_count}
            
            # Stock data stats
            stock_data_count = db.query(StockData).count()
            stats["stock_data"] = {"count": stock_data_count}
            
            return stats
            
        except Exception as e:
            self.logger.warning(f"Could not get table statistics: {str(e)}")
            return {}
    
    def _get_query_performance(self, db: Session) -> Dict[str, Any]:
        """Get query performance metrics"""
        try:
            # Get slow query log status (MySQL specific)
            result = db.execute(text("SHOW VARIABLES LIKE 'slow_query_log'")).fetchone()
            slow_query_log = result[1] if result else "OFF"
            
            # Get query cache status
            result = db.execute(text("SHOW VARIABLES LIKE 'query_cache_size'")).fetchone()
            query_cache_size = result[1] if result else "0"
            
            return {
                "slow_query_log": slow_query_log,
                "query_cache_size": query_cache_size,
                "connection_time": "< 1ms"  # Simplified
            }
        except Exception as e:
            self.logger.warning(f"Could not get query performance: {str(e)}")
            return {"error": str(e)}


class TaskMonitor:
    """
    Celery task monitoring
    """
    
    def __init__(self):
        self.logger = get_logger("task_monitor")
    
    def get_task_metrics(self) -> Dict[str, Any]:
        """
        Get Celery task performance metrics
        """
        try:
            from app.celery_app import celery_app
            
            # Get worker statistics
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            
            # Calculate metrics
            total_workers = len(stats) if stats else 0
            total_tasks = sum(
                sum(worker_stats.get("total", {}).values()) 
                for worker_stats in (stats.values() if stats else [])
            )
            
            active_task_count = sum(
                len(tasks) for tasks in (active_tasks.values() if active_tasks else [])
            )
            
            scheduled_task_count = sum(
                len(tasks) for tasks in (scheduled_tasks.values() if scheduled_tasks else [])
            )
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "workers": {
                    "total": total_workers,
                    "active": total_workers,
                    "stats": stats
                },
                "tasks": {
                    "total_executed": total_tasks,
                    "active": active_task_count,
                    "scheduled": scheduled_task_count
                },
                "queues": {
                    "monitoring": self._get_queue_metrics("monitoring"),
                    "data_update": self._get_queue_metrics("data_update"),
                    "reports": self._get_queue_metrics("reports"),
                    "alerts": self._get_queue_metrics("alerts")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task metrics: {str(e)}")
            return {"error": str(e)}
    
    def _get_queue_metrics(self, queue_name: str) -> Dict[str, Any]:
        """Get metrics for a specific queue"""
        try:
            from app.celery_app import celery_app
            inspect = celery_app.control.inspect()
            
            # Get queue length (simplified)
            return {
                "name": queue_name,
                "length": 0,  # Would need Redis inspection for actual length
                "status": "active"
            }
        except Exception as e:
            return {"name": queue_name, "error": str(e)}


class BusinessMonitor:
    """
    Business metrics monitoring
    """
    
    def __init__(self):
        self.logger = get_logger("business_monitor")
    
    def get_business_metrics(self) -> Dict[str, Any]:
        """
        Get business-related metrics
        """
        try:
            with get_db_session() as db:
                # User metrics
                total_users = db.query(User).count()
                active_users = db.query(User).filter(User.is_active == True).count()
                
                # Stock metrics
                total_stocks = db.query(Stock).count()
                active_stocks = db.query(Stock).filter(Stock.is_active == True).count()
                
                # Alert metrics
                total_alerts = db.query(Alert).count()
                pending_alerts = db.query(Alert).filter(Alert.status == "PENDING").count()
                triggered_alerts = db.query(Alert).filter(Alert.status == "TRIGGERED").count()
                
                # Report metrics
                total_reports = db.query(Report).count()
                recent_reports = db.query(Report).filter(
                    Report.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
                
                # News metrics
                total_news = db.query(News).count()
                recent_news = db.query(News).filter(
                    News.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
                
                # Stock data metrics
                total_stock_data = db.query(StockData).count()
                recent_stock_data = db.query(StockData).filter(
                    StockData.timestamp >= datetime.utcnow() - timedelta(days=7)
                ).count()
                
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "users": {
                        "total": total_users,
                        "active": active_users,
                        "inactive": total_users - active_users
                    },
                    "stocks": {
                        "total": total_stocks,
                        "active": active_stocks,
                        "inactive": total_stocks - active_stocks
                    },
                    "alerts": {
                        "total": total_alerts,
                        "pending": pending_alerts,
                        "triggered": triggered_alerts,
                        "acknowledged": total_alerts - pending_alerts - triggered_alerts
                    },
                    "reports": {
                        "total": total_reports,
                        "recent_7_days": recent_reports
                    },
                    "news": {
                        "total": total_news,
                        "recent_7_days": recent_news
                    },
                    "stock_data": {
                        "total": total_stock_data,
                        "recent_7_days": recent_stock_data
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get business metrics: {str(e)}")
            raise DatabaseException(f"Failed to get business metrics", details={"error": str(e)})


class MonitoringService:
    """
    Main monitoring service that coordinates all monitoring components
    """
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.database_monitor = DatabaseMonitor()
        self.task_monitor = TaskMonitor()
        self.business_monitor = BusinessMonitor()
        self.logger = get_logger("monitoring_service")
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive system metrics
        """
        try:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": self.system_monitor.get_system_metrics(),
                "database": self.database_monitor.get_database_metrics(),
                "tasks": self.task_monitor.get_task_metrics(),
                "business": self.business_monitor.get_business_metrics()
            }
        except Exception as e:
            self.logger.error(f"Failed to get comprehensive metrics: {str(e)}")
            return {"error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall system health status
        """
        try:
            system_metrics = self.system_monitor.get_system_metrics()
            db_metrics = self.database_monitor.get_database_metrics()
            task_metrics = self.task_monitor.get_task_metrics()
            
            # Determine health status
            health_issues = []
            
            # Check CPU usage
            if system_metrics["cpu"]["percent"] > 80:
                health_issues.append("High CPU usage")
            
            # Check memory usage
            if system_metrics["memory"]["percent"] > 85:
                health_issues.append("High memory usage")
            
            # Check disk usage
            if system_metrics["disk"]["percent"] > 90:
                health_issues.append("High disk usage")
            
            # Check database connection pool
            pool_status = db_metrics.get("connection_pool", {})
            if pool_status.get("checked_out", 0) > pool_status.get("pool_size", 0) * 0.8:
                health_issues.append("Database connection pool near capacity")
            
            # Check task workers
            if task_metrics.get("workers", {}).get("total", 0) == 0:
                health_issues.append("No Celery workers running")
            
            overall_status = "healthy" if not health_issues else "warning" if len(health_issues) < 3 else "critical"
            
            return {
                "status": overall_status,
                "issues": health_issues,
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_percent": system_metrics["cpu"]["percent"],
                    "memory_percent": system_metrics["memory"]["percent"],
                    "disk_percent": system_metrics["disk"]["percent"]
                },
                "database": {
                    "pool_size": pool_status.get("pool_size", 0),
                    "checked_out": pool_status.get("checked_out", 0)
                },
                "tasks": {
                    "workers": task_metrics.get("workers", {}).get("total", 0),
                    "active_tasks": task_metrics.get("tasks", {}).get("active", 0)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a stock symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None if not found
        """
        try:
            from app.external.stock_api_client import StockAPIClient
            
            stock_api = StockAPIClient()
            price_data = await stock_api.get_current_price(symbol)
            
            if price_data and "error" not in price_data:
                return price_data.get("price")  # StockAPIClient returns "price" not "current_price"
            else:
                self.logger.warning(f"Failed to get current price for {symbol}: {price_data.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return None

    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive stock data including price changes
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock data dictionary with price changes
        """
        try:
            from app.agents.data_collection_agent import DataCollectionAgent
            from app.database import get_db_session
            
            with get_db_session() as db:
                data_agent = DataCollectionAgent(db)
                stock_data = await data_agent.collect_stock_data(symbol)
                
                if stock_data and "error" not in stock_data:
                    return stock_data
                else:
                    self.logger.warning(f"Failed to get stock data for {symbol}: {stock_data.get('error', 'Unknown error')}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting stock data for {symbol}: {str(e)}")
            return None