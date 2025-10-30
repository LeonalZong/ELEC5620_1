"""
Advisor API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import os

from app.database import get_db
from app.services.auth_service import get_current_active_user, require_advisor
from app.models.user import User as UserModel, UserRole
from app.models.alert import Alert as AlertModel
from app.models.portfolio import Portfolio as PortfolioModel
from app.services.portfolio_service import PortfolioService
from app.models.report import Report as ReportModel
from app.models.stock import Stock as StockModel
from app.models.stock_data import StockData as StockDataModel

router = APIRouter()


@router.get("/dashboard")
async def get_advisor_dashboard(
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Minimal advisor dashboard stats.
    If advisor-client relationship is not available, use all INVESTOR users as demo scope.
    """
    try:
        # DEMO scope: all investors
        clients_q = db.query(UserModel).filter(UserModel.role == UserRole.INVESTOR)
        total_clients = clients_q.count()

        # Active portfolios: count portfolio rows owned by investors
        active_portfolios = db.query(PortfolioModel).join(UserModel, PortfolioModel.user_id == UserModel.id) \
            .filter(UserModel.role == UserRole.INVESTOR).count()

        # Total alerts under investors
        total_alerts = db.query(AlertModel).count()

        return {
            "total_clients": total_clients,
            "active_portfolios": active_portfolios,
            "total_alerts": total_alerts,
            "pending_reviews": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@router.get("/clients")
async def get_advisor_clients(
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
):
    """
    Return advisor's clients.
    DEMO: list all INVESTOR users with basic fields (id, username, email, last_login, is_active).
    """
    try:
        # Optional env-based scoping: ADVISOR_CLIENT_IDS="1,2,3"
        ids_env = os.getenv("ADVISOR_CLIENT_IDS")
        if ids_env:
            id_list: List[int] = [int(x) for x in ids_env.split(',') if x.strip().isdigit()]
            q = db.query(UserModel).filter(UserModel.role == UserRole.INVESTOR, UserModel.id.in_(id_list))
        else:
            q = db.query(UserModel).filter(UserModel.role == UserRole.INVESTOR)
        investors = q.all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "is_active": True if getattr(u, "is_active", "Y") in ("Y", True) else False,
            }
            for u in investors
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get clients: {str(e)}")


@router.get("/clients/{client_id}/summary")
async def get_client_summary(
    client_id: int,
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
):
    """
    Return portfolio summary for a specific client.
    """
    try:
        # Ensure client exists and is investor (demo check)
        client = db.query(UserModel).filter(UserModel.id == client_id).first()
        if not client or client.role != UserRole.INVESTOR:
            raise HTTPException(status_code=404, detail="Client not found")

        svc = PortfolioService(db)
        summary = await svc.get_portfolio_summary(client_id)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get client summary: {str(e)}")


@router.get("/portfolios")
async def get_client_portfolios(
    client_id: int,
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
):
    """
    Return portfolio holdings for a client.
    """
    try:
        client = db.query(UserModel).filter(UserModel.id == client_id).first()
        if not client or client.role != UserRole.INVESTOR:
            raise HTTPException(status_code=404, detail="Client not found")
        svc = PortfolioService(db)
        holdings = await svc.get_user_portfolio(client_id)
        return holdings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get client portfolios: {str(e)}")


@router.get("/reports")
async def get_client_reports(
    client_id: int,
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
):
    """
    Minimal report list for a client.
    """
    try:
        reports = db.query(ReportModel).filter(ReportModel.user_id == client_id).order_by(ReportModel.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "summary": r.summary,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get client reports: {str(e)}")


@router.get("/analytics")
async def get_client_analytics(
    client_id: int,
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Provide simple analytics for a client: sector distribution and alert counts.
    """
    try:
        # Sector distribution from holdings
        holdings = db.query(PortfolioModel).filter(PortfolioModel.user_id == client_id).all()
        sector_dist: Dict[str, float] = {}
        total_value = 0.0
        for p in holdings:
            stock = db.query(StockModel).filter(StockModel.id == p.stock_id).first()
            price = stock.current_price or p.purchase_price
            value = (price or 0) * (p.quantity or 0)
            total_value += value
            sector = (stock.sector or "Unknown") if stock else "Unknown"
            sector_dist[sector] = sector_dist.get(sector, 0.0) + value
        if total_value > 0:
            for k in list(sector_dist.keys()):
                sector_dist[k] = round(sector_dist[k] / total_value * 100, 2)

        # Alert counts
        alert_counts = {
            "total": db.query(AlertModel).filter(AlertModel.user_id == client_id).count(),
        }
        return {
            "total_value": round(total_value, 2),
            "sector_distribution_pct": sector_dist,
            "alerts": alert_counts,
            "holdings": len(holdings),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/reports/{report_id}")
async def get_report_detail(
    report_id: int,
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
):
    """
    Return full report content.
    """
    try:
        r = db.query(ReportModel).filter(ReportModel.id == report_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Report not found")
        return {
            "id": r.id,
            "title": r.title,
            "summary": r.summary,
            "content": r.content,
            "details_json": r.details_json,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/analytics/returns")
async def get_client_returns_curve(
    client_id: int,
    days: int = 30,
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compute simple equity curve for a client using StockData closes over last N days.
    """
    try:
        days = max(1, min(days, 120))
        holdings = db.query(PortfolioModel).filter(PortfolioModel.user_id == client_id).all()
        if not holdings:
            return {"days": days, "equity": []}

        # Collect stock ids and quantities
        from collections import defaultdict
        stock_qty = defaultdict(float)
        for p in holdings:
            stock_qty[p.stock_id] += float(p.quantity or 0)

        # Get data per stock
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        # date->value
        equity_map = defaultdict(float)
        dates_set = set()
        for stock_id, qty in stock_qty.items():
            data = db.query(StockDataModel).filter(
                StockDataModel.stock_id == stock_id,
                StockDataModel.timestamp >= cutoff
            ).order_by(StockDataModel.timestamp.asc()).all()
            for d in data:
                date_str = d.timestamp.strftime("%Y-%m-%d")
                dates_set.add(date_str)
                equity_map[date_str] += qty * float(d.close_price or 0)

        equity = [
            {"date": dt, "value": round(equity_map.get(dt, 0.0), 2)}
            for dt in sorted(list(dates_set))
        ]

        # Compute pct change from first day
        if equity:
            base = equity[0]["value"] or 1.0
            for row in equity:
                row["change_pct"] = round(((row["value"] - base) / base) * 100, 2) if base else 0

        return {"days": days, "equity": equity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute returns: {str(e)}")


@router.post("/reports/generate")
async def generate_report(
    client_id: int,
    title: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    current_user: UserModel = Depends(require_advisor),
    db: Session = Depends(get_db)
):
    """
    Minimal report generation: create a report row for client with basic summary.
    """
    try:
        svc = PortfolioService(db)
        summary = await svc.get_portfolio_summary(client_id)
        report = ReportModel(
            user_id=client_id,
            title=title or "Advisor Report",
            summary=f"Total value: ${summary.total_value:.2f}, Return {summary.total_profit_loss_pct:.2f}%",
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return {"id": report.id, "title": report.title, "created_at": report.created_at}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


