"""
Report Generation Tasks
Automated report generation and distribution
"""
from celery import current_task
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.report_service import ReportService
from app.models.user import User as UserModel
from app.models.tracked_stock import TrackedStock as TrackedStockModel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.report_tasks.generate_daily_reports")
def generate_daily_reports(self):
    """
    Generate daily analysis reports for all active users
    Runs daily at 6 AM
    """
    try:
        logger.info("Starting daily report generation task")
        
        db = SessionLocal()
        try:
            # Initialize services
            report_service = ReportService(db)
            
            # Get all active users with tracked stocks
            active_users = db.query(UserModel).filter(
                UserModel.is_active == True
            ).all()
            
            logger.info(f"Generating reports for {len(active_users)} active users")
            
            reports_generated = 0
            failed_reports = 0
            
            for i, user in enumerate(active_users):
                try:
                    # Update task progress
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current_user": user.username,
                            "progress": f"{i+1}/{len(active_users)}",
                            "generated": reports_generated,
                            "failed": failed_reports
                        }
                    )
                    
                    # Get user's tracked stocks
                    tracked_stocks = db.query(TrackedStockModel).filter(
                        TrackedStockModel.user_id == user.id,
                        TrackedStockModel.is_active == True
                    ).all()
                    
                    if not tracked_stocks:
                        logger.info(f"No tracked stocks for user {user.username}, skipping")
                        continue
                    
                    # Generate report for each tracked stock
                    for tracked_stock in tracked_stocks:
                        try:
                            # Check if report already exists for today
                            today = datetime.utcnow().date()
                            existing_report = report_service.get_reports_by_user_and_stock(
                                user_id=user.id,
                                stock_id=tracked_stock.stock_id,
                                start_date=today,
                                end_date=today
                            )
                            
                            if existing_report:
                                logger.info(f"Report already exists for {user.username} - {tracked_stock.stock.symbol}")
                                continue
                            
                            # Generate new report
                            report = report_service.generate_report(
                                user_id=user.id,
                                stock_id=tracked_stock.stock_id,
                                report_type="DAILY"
                            )
                            
                            if report:
                                reports_generated += 1
                                logger.info(f"Generated report for {user.username} - {tracked_stock.stock.symbol}")
                            else:
                                failed_reports += 1
                                logger.warning(f"Failed to generate report for {user.username} - {tracked_stock.stock.symbol}")
                                
                        except Exception as e:
                            failed_reports += 1
                            logger.error(f"Error generating report for {user.username} - {tracked_stock.stock.symbol}: {str(e)}")
                            continue
                    
                except Exception as e:
                    failed_reports += 1
                    logger.error(f"Error processing user {user.username}: {str(e)}")
                    continue
            
            logger.info(f"Daily report generation completed. Generated: {reports_generated}, Failed: {failed_reports}")
            
            return {
                "status": "completed",
                "total_users": len(active_users),
                "reports_generated": reports_generated,
                "failed_reports": failed_reports,
                "message": "Daily report generation completed successfully"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Daily report generation task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise

@celery_app.task(bind=True, name="app.tasks.report_tasks.generate_weekly_summary")
def generate_weekly_summary(self):
    """
    Generate weekly summary reports for advisors and admins
    Runs weekly on Monday at 8 AM
    """
    try:
        logger.info("Starting weekly summary generation task")
        
        db = SessionLocal()
        try:
            # Initialize services
            report_service = ReportService(db)
            
            # Get advisors and admins
            privileged_users = db.query(UserModel).filter(
                UserModel.is_active == True,
                UserModel.role.in_(["ADVISOR", "ADMIN"])
            ).all()
            
            logger.info(f"Generating weekly summaries for {len(privileged_users)} privileged users")
            
            summaries_generated = 0
            failed_summaries = 0
            
            for i, user in enumerate(privileged_users):
                try:
                    # Update task progress
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current_user": user.username,
                            "progress": f"{i+1}/{len(privileged_users)}",
                            "generated": summaries_generated,
                            "failed": failed_summaries
                        }
                    )
                    
                    # Generate weekly summary
                    summary = report_service.generate_report_summary(
                        user_id=user.id,
                        start_date=datetime.utcnow() - timedelta(days=7),
                        end_date=datetime.utcnow()
                    )
                    
                    if summary:
                        summaries_generated += 1
                        logger.info(f"Generated weekly summary for {user.username}")
                    else:
                        failed_summaries += 1
                        logger.warning(f"Failed to generate weekly summary for {user.username}")
                    
                except Exception as e:
                    failed_summaries += 1
                    logger.error(f"Error generating weekly summary for {user.username}: {str(e)}")
                    continue
            
            logger.info(f"Weekly summary generation completed. Generated: {summaries_generated}, Failed: {failed_summaries}")
            
            return {
                "status": "completed",
                "total_users": len(privileged_users),
                "summaries_generated": summaries_generated,
                "failed_summaries": failed_summaries,
                "message": "Weekly summary generation completed successfully"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Weekly summary generation task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise

@celery_app.task(bind=True, name="app.tasks.report_tasks.generate_market_report")
def generate_market_report(self):
    """
    Generate overall market analysis report
    Runs daily at 7 AM
    """
    try:
        logger.info("Starting market report generation task")
        
        db = SessionLocal()
        try:
            # Initialize services
            report_service = ReportService(db)
            
            # Get all tracked stocks for market analysis
            tracked_stocks = db.query(TrackedStockModel).filter(
                TrackedStockModel.is_active == True
            ).all()
            
            if not tracked_stocks:
                logger.info("No tracked stocks found, skipping market report")
                return {
                    "status": "completed",
                    "message": "No tracked stocks found, market report skipped"
                }
            
            # Get unique stock symbols
            unique_symbols = list(set([ts.stock.symbol for ts in tracked_stocks]))
            
            # Generate market report
            market_report = report_service.generate_market_analysis_report(
                stock_symbols=unique_symbols,
                report_type="MARKET_OVERVIEW"
            )
            
            if market_report:
                logger.info("Market report generated successfully")
                
                return {
                    "status": "completed",
                    "stocks_analyzed": len(unique_symbols),
                    "report_id": market_report.id,
                    "message": "Market report generated successfully"
                }
            else:
                logger.warning("Failed to generate market report")
                
                return {
                    "status": "failed",
                    "message": "Failed to generate market report"
                }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Market report generation task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise










