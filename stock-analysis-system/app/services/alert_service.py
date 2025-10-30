"""
Alert Service
Business logic for alert operations
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import logging

from app.schemas.alert import Alert, AlertCreate, AlertUpdate, AlertSummary
from app.models.alert import Alert as AlertModel, AlertType, AlertStatus
from app.models.stock import Stock as StockModel
from app.models.user import User as UserModel
from app.external.stock_api_client import StockAPIClient

class AlertService:
    """
    Service for alert-related operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.stock_api_client = StockAPIClient()
        self.logger = logging.getLogger("alert_service")
    
    async def get_user_alerts(self, user_id: int) -> List[Alert]:
        """
        Get all alerts for current user
        
        Args:
            user_id: User ID
            
        Returns:
            List of alerts
        """
        try:
            # Query alerts from database with stock information
            alerts = self.db.query(AlertModel).filter(AlertModel.user_id == user_id).all()
            
            result = []
            for alert in alerts:
                # Get stock information
                stock = alert.stock
                stock_data = None
                if stock:
                    from app.schemas.stock import Stock as StockSchema
                    stock_data = StockSchema(
                        id=stock.id,
                        symbol=stock.symbol,
                        name=stock.name,
                        sector=stock.sector,
                        industry=stock.industry,
                        market_cap=stock.market_cap,
                        current_price=stock.current_price,
                        currency=stock.currency,
                        exchange=stock.exchange,
                        is_active=stock.is_active == "1",
                        created_at=stock.created_at.isoformat(),
                        updated_at=stock.updated_at.isoformat()
                    )
                
                result.append(Alert(
                    id=alert.id,
                    user_id=alert.user_id,
                    stock_id=alert.stock_id,
                    alert_type=alert.alert_type,
                    threshold_value=alert.threshold_value,
                    current_value=alert.current_value,
                    trigger_count=alert.trigger_count,
                    trigger_history=alert.trigger_history,
                    required_triggers=alert.required_triggers,
                    message=alert.message,
                    status=alert.status,
                    triggered_at=alert.triggered_at.isoformat() if alert.triggered_at else None,
                    acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    created_at=alert.created_at.isoformat(),
                    stock=stock_data
                ))
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to get user alerts: {str(e)}")
            raise Exception(f"Failed to get user alerts: {str(e)}")
    
    async def get_active_alerts(self, user_id: int) -> List[Alert]:
        """
        Get active alerts for user
        
        Args:
            user_id: User ID
            
        Returns:
            List of active alerts
        """
        try:
            # Query active alerts from database
            alerts = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.user_id == user_id,
                    AlertModel.status == AlertStatus.TRIGGERED
                )
            ).all()
            
            result = []
            for alert in alerts:
                result.append(Alert(
                    id=alert.id,
                    user_id=alert.user_id,
                    stock_id=alert.stock_id,
                    alert_type=alert.alert_type,
                    threshold_value=alert.threshold_value,
                    current_value=alert.current_value,
                    trigger_count=alert.trigger_count,
                    trigger_history=alert.trigger_history,
                    required_triggers=alert.required_triggers,
                    message=alert.message,
                    status=alert.status,
                    triggered_at=alert.triggered_at.isoformat() if alert.triggered_at else None,
                    acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    created_at=alert.created_at.isoformat()
                ))
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to get active alerts: {str(e)}")
            raise Exception(f"Failed to get active alerts: {str(e)}")
    
    async def get_alert_summary(self, user_id: int) -> AlertSummary:
        """
        Get alert summary for user
        
        Args:
            user_id: User ID
            
        Returns:
            Alert summary
        """
        try:
            # Count different types of alerts
            total_alerts = self.db.query(AlertModel).filter(AlertModel.user_id == user_id).count()
            active_alerts = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.user_id == user_id,
                    AlertModel.status.in_([AlertStatus.PENDING, AlertStatus.TRIGGERED])
                )
            ).count()
            acknowledged_alerts = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.user_id == user_id,
                    AlertModel.status == AlertStatus.ACKNOWLEDGED
                )
            ).count()
            
            return AlertSummary(
                total_alerts=total_alerts,
                pending_alerts=total_alerts - active_alerts - acknowledged_alerts,
                triggered_alerts=active_alerts,
                acknowledged_alerts=acknowledged_alerts
            )
        except Exception as e:
            self.logger.error(f"Failed to get alert summary: {str(e)}")
            raise Exception(f"Failed to get alert summary: {str(e)}")
    
    async def acknowledge_alert(self, alert_id: int, user_id: int) -> None:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID to acknowledge
            user_id: User ID
        """
        try:
            # Find the alert
            alert = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.id == alert_id,
                    AlertModel.user_id == user_id
                )
            ).first()
            
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            # Update alert status
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
            raise Exception(f"Failed to acknowledge alert: {str(e)}")
    
    async def create_alert(self, user_id: int, stock_id: int, alert_type: AlertType, threshold_value: float) -> Alert:
        """
        Create a new alert
        
        Args:
            user_id: User ID
            stock_id: Stock ID
            alert_type: Type of alert
            threshold_value: Threshold value
            
        Returns:
            Created alert
        """
        try:
            # Create new alert
            alert = AlertModel(
                user_id=user_id,
                stock_id=stock_id,
                alert_type=alert_type,
                threshold_value=threshold_value,
                current_value=0.0,
                message=f"Alert created for {alert_type.value} at {threshold_value}%",
                status=AlertStatus.PENDING,
                created_at=datetime.utcnow()
            )
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            return Alert(
                id=alert.id,
                user_id=alert.user_id,
                stock_id=alert.stock_id,
                alert_type=alert.alert_type,
                threshold_value=alert.threshold_value,
                current_value=alert.current_value,
                trigger_count=alert.trigger_count,
                trigger_history=alert.trigger_history,
                required_triggers=alert.required_triggers,
                message=alert.message,
                status=alert.status,
                triggered_at=alert.triggered_at.isoformat() if alert.triggered_at else None,
                acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                created_at=alert.created_at.isoformat()
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to create alert: {str(e)}")
            raise Exception(f"Failed to create alert: {str(e)}")

    async def trigger_alert(self, alert_id: int, current_value: float, message: str) -> None:
        """
        Trigger an alert
        
        Args:
            alert_id: Alert ID
            current_value: Current value that triggered the alert
            message: Alert message
        """
        try:
            alert = self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            # Update alert status to TRIGGERED
            alert.status = AlertStatus.TRIGGERED
            alert.current_value = current_value
            alert.message = message
            alert.triggered_at = datetime.utcnow()
            
            self.db.commit()
            
            self.logger.info(f"Alert {alert_id} triggered for {alert.stock.symbol}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger alert {alert_id}: {str(e)}")
            raise Exception(f"Failed to trigger alert {alert_id}: {str(e)}")
    
    async def check_price_alerts(self, symbol: str) -> List[Alert]:
        """
        Check if price alerts should be triggered
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            List of triggered alerts
        """
        try:
            # Get current stock price
            stock_data = await self.stock_api_client.get_current_price(symbol)
            if "error" in stock_data:
                return []
            
            current_price = stock_data.get("price", 0)
            
            # Get stock from database
            stock = self.db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
            if not stock:
                return []
            
            # Get pending alerts for this stock
            alerts = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.stock_id == stock.id,
                    AlertModel.status == AlertStatus.PENDING,
                    AlertModel.alert_type == AlertType.PRICE_DROP
                )
            ).all()
            
            triggered_alerts = []
            for alert in alerts:
                # Calculate price change percentage
                price_change = ((current_price - stock.current_price) / stock.current_price) * 100
                
                # Check if alert should trigger
                if price_change <= -abs(alert.threshold_value):
                    alert.status = AlertStatus.TRIGGERED
                    alert.current_value = abs(price_change)
                    alert.message = f"{symbol} dropped {abs(price_change):.2f}% (threshold: {alert.threshold_value}%)"
                    alert.triggered_at = datetime.utcnow()
                    
                    triggered_alerts.append(Alert(
                        id=alert.id,
                        user_id=alert.user_id,
                        stock_id=alert.stock_id,
                        alert_type=alert.alert_type,
                        threshold_value=alert.threshold_value,
                        current_value=alert.current_value,
                        trigger_count=alert.trigger_count,
                        trigger_history=alert.trigger_history,
                        required_triggers=alert.required_triggers,
                        message=alert.message,
                        status=alert.status,
                        triggered_at=alert.triggered_at.isoformat(),
                        acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                        created_at=alert.created_at.isoformat()
                    ))
            
            self.db.commit()
            return triggered_alerts
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to check price alerts for {symbol}: {str(e)}")
            return []
    
    async def delete_alert(self, alert_id: int, user_id: int) -> None:
        """
        Delete an alert
        
        For ACKNOWLEDGED alerts: Reset to PENDING status (don't actually delete)
        For other alerts: Actually delete from database
        
        Args:
            alert_id: Alert ID to delete
            user_id: User ID (for security verification)
        """
        try:
            # Find the alert and verify ownership
            alert = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.id == alert_id,
                    AlertModel.user_id == user_id
                )
            ).first()
            
            if not alert:
                raise ValueError(f"Alert {alert_id} not found or not owned by user")
            
            # If alert is ACKNOWLEDGED, reset it to PENDING instead of deleting
            if alert.status == AlertStatus.ACKNOWLEDGED:
                alert.status = AlertStatus.PENDING
                alert.trigger_count = 0
                alert.trigger_history = None
                alert.triggered_at = None
                alert.acknowledged_at = None
                alert.message = f"Price drop alert for {alert.stock.symbol} at {alert.threshold_value}%"
                self.db.commit()
                self.logger.info(f"Alert {alert_id} reset to PENDING (was ACKNOWLEDGED)")
            else:
                # For PENDING or TRIGGERED alerts, actually delete
                self.db.delete(alert)
                self.db.commit()
                self.logger.info(f"Alert {alert_id} deleted for user {user_id}")
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to delete alert {alert_id}: {str(e)}")
            raise Exception(f"Failed to delete alert: {str(e)}")