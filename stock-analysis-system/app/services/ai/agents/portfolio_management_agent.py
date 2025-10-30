"""
Portfolio Management Agent (P0 - read-only)
Provides tools for AI Assistant to view a user's (or advisor's client) portfolio
and list tracked stocks. Write actions will be added in a later phase with
two-step confirmation and auditing.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import asyncio
import uuid

from app.database import SessionLocal
from app.services.portfolio_service import PortfolioService
from app.models.tracked_stock import TrackedStock as TrackedStockModel
from app.models.stock import Stock as StockModel
from app.models.portfolio import Portfolio as PortfolioModel


class ViewPortfolioInput(BaseModel):
    """Input for viewing a user's portfolio. The user_id is bound by the tool."""
    summary: bool = Field(True, description="Whether to include portfolio summary metrics")


class ListTrackedStocksInput(BaseModel):
    """Input for listing tracked stocks for the bound user."""
    include_baseline: bool = Field(True, description="Include baseline price if available")


# ---------- Confirmation models & store ----------
class AddHoldingInput(BaseModel):
    symbol: str = Field(..., description="Stock symbol, e.g., NVDA")
    quantity: float = Field(..., description="Number of shares")
    price: float = Field(..., description="Purchase price per share")
    notes: Optional[str] = Field(None, description="Optional notes")
    confirm: bool = Field(False, description="Set True to execute after reviewing draft")
    token: Optional[str] = Field(None, description="Confirmation token returned by draft stage")


class UpdateHoldingInput(BaseModel):
    holding_id: int = Field(..., description="Holding (portfolio) id")
    quantity: Optional[float] = Field(None, description="New quantity")
    price: Optional[float] = Field(None, description="New purchase price")
    notes: Optional[str] = Field(None, description="New notes")
    confirm: bool = Field(False, description="Set True to execute after reviewing draft")
    token: Optional[str] = Field(None, description="Confirmation token")


class DeleteHoldingInput(BaseModel):
    holding_id: int = Field(..., description="Holding (portfolio) id to delete")
    confirm: bool = Field(False, description="Set True to execute after reviewing draft")
    token: Optional[str] = Field(None, description="Confirmation token")


class TrackStockInput(BaseModel):
    symbol: str = Field(..., description="Stock symbol to track")
    baseline_price: Optional[float] = Field(None, description="Baseline price for alert/tracking context")
    confirm: bool = Field(False, description="Set True to execute after reviewing draft")
    token: Optional[str] = Field(None, description="Confirmation token")


class UntrackStockInput(BaseModel):
    symbol: str = Field(..., description="Stock symbol to untrack")
    confirm: bool = Field(False, description="Set True to execute after reviewing draft")
    token: Optional[str] = Field(None, description="Confirmation token")


CONFIRMATION_STORE: Dict[str, Dict[str, Any]] = {}


def view_portfolio(user_id: int, summary: bool = True) -> Dict[str, Any]:
    """Return the user's portfolio holdings and optional summary."""
    db = SessionLocal()
    try:
        service = PortfolioService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            holdings = loop.run_until_complete(service.get_user_portfolio(user_id))
            response: Dict[str, Any] = {
                "status": "success",
                "holdings": [
                    {
                        "holding_id": h.id,
                        "symbol": h.stock.symbol,
                        "name": h.stock.name,
                        "quantity": h.quantity,
                        "purchase_price": float(h.purchase_price or 0),
                        "current_price": float(h.current_price or 0),
                        "profit_loss_pct": float(h.profit_loss_pct or 0),
                        "current_value": float(h.current_value or 0)
                    }
                    for h in holdings
                ]
            }
            if summary:
                summary_data = loop.run_until_complete(service.get_portfolio_summary(user_id))
                response["summary"] = {
                    "total_value": float(summary_data.total_value or 0),
                    "total_profit_loss": float(summary_data.total_profit_loss or 0),
                    "total_profit_loss_pct": float(summary_data.total_profit_loss_pct or 0),
                    "today_gain": float(summary_data.today_gain or 0),
                    "today_gain_pct": float(summary_data.today_gain_pct or 0),
                    "active_alerts": int(summary_data.active_alerts or 0)
                }
            return response
        finally:
            loop.close()
    except Exception as e:
        return {"status": "error", "message": f"Failed to view portfolio: {str(e)}"}
    finally:
        db.close()


def list_tracked_stocks(user_id: int, include_baseline: bool = True) -> Dict[str, Any]:
    """List tracked stocks for the bound user with optional baseline price."""
    db = SessionLocal()
    try:
        tracked = db.query(TrackedStockModel).filter(TrackedStockModel.user_id == user_id).all()
        items: List[Dict[str, Any]] = []
        for t in tracked:
            stock: Optional[StockModel] = db.query(StockModel).filter(StockModel.id == t.stock_id).first()
            items.append({
                "symbol": stock.symbol if stock else None,
                "name": stock.name if stock else None,
                "baseline_price": float(t.baseline_price) if include_baseline and getattr(t, "baseline_price", None) is not None else None,
                "is_active": t.is_active == "Y"
            })
        return {"status": "success", "tracked": items}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list tracked stocks: {str(e)}"}
    finally:
        db.close()


# ---------- Write operations with two-step confirmation ----------
def _make_token() -> str:
    return uuid.uuid4().hex[:16]


def add_holding(user_id: int, symbol: str, quantity: float, price: float, notes: Optional[str] = None, confirm: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
    """Add or increase a holding with a confirm flow.
    If the user already holds the stock, we will INCREASE the position and
    recompute the purchase_price using weighted-average cost.
    """
    db = SessionLocal()
    try:
        stock = db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
        if not stock:
            return {"status": "error", "message": f"Stock {symbol} not found"}

        existing: Optional[PortfolioModel] = db.query(PortfolioModel).filter(PortfolioModel.user_id == user_id, PortfolioModel.stock_id == stock.id).first()

        if existing:
            old_qty = float(existing.quantity or 0)
            old_cost = float(existing.purchase_price or 0)
            new_qty = old_qty + float(quantity)
            new_cost = ((old_qty * old_cost) + (float(quantity) * float(price))) / new_qty if new_qty > 0 else 0.0
            draft = {
                "action": "increase_holding",
                "user_id": user_id,
                "stock_id": stock.id,
                "symbol": stock.symbol,
                "increase_by": float(quantity),
                "buy_price": float(price),
                "old_quantity": old_qty,
                "old_cost": old_cost,
                "new_quantity": new_qty,
                "new_weighted_cost": new_cost,
                "notes": notes
            }
            diff_text = f"Increase {stock.symbol}: {old_qty}→{new_qty}, cost {old_cost}→{round(new_cost, 4)} (buy {quantity} @ {price})"
        else:
            draft = {
                "action": "add_holding",
                "user_id": user_id,
                "stock_id": stock.id,
                "symbol": stock.symbol,
                "quantity": float(quantity),
                "price": float(price),
                "notes": notes
            }
            diff_text = f"Add new holding {stock.symbol} {quantity} @ {price}"
        if not confirm:
            t = _make_token()
            CONFIRMATION_STORE[t] = draft
            return {"status": "draft", "token": t, "diff_summary": diff_text, "details": draft}

        if not token or token not in CONFIRMATION_STORE:
            return {"status": "error", "message": "Invalid or missing confirmation token"}

        plan = CONFIRMATION_STORE.pop(token)
        service = PortfolioService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if plan.get("action") == "increase_holding":
                from app.schemas.portfolio import PortfolioUpdate
                updated = loop.run_until_complete(
                    service.update_holding(
                        user_id,
                        db.query(PortfolioModel).filter(PortfolioModel.user_id == user_id, PortfolioModel.stock_id == plan["stock_id"]).first().id,
                        PortfolioUpdate(quantity=plan["new_quantity"], purchase_price=plan["new_weighted_cost"], notes=plan.get("notes"))
                    )
                )
                return {"status": "executed", "result": {"holding_id": updated.id, "symbol": updated.stock.symbol, "quantity": updated.quantity, "purchase_price": float(updated.purchase_price)}}
            else:
                from app.schemas.portfolio import PortfolioCreate
                created = loop.run_until_complete(service.add_holding(user_id, PortfolioCreate(stock_id=plan["stock_id"], quantity=plan["quantity"], purchase_price=plan["price"], notes=plan.get("notes"))))
                return {"status": "executed", "result": {"holding_id": created.id, "symbol": created.stock.symbol, "quantity": created.quantity, "purchase_price": float(created.purchase_price)}}
        finally:
            loop.close()
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Failed to add holding: {str(e)}"}
    finally:
        db.close()


def update_holding(user_id: int, holding_id: int, quantity: Optional[float] = None, price: Optional[float] = None, notes: Optional[str] = None, confirm: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        holding = db.query(PortfolioModel).filter(PortfolioModel.id == holding_id, PortfolioModel.user_id == user_id).first()
        if not holding:
            return {"status": "error", "message": f"Holding {holding_id} not found"}
        draft = {
            "action": "update_holding",
            "user_id": user_id,
            "holding_id": holding_id,
            "quantity": quantity,
            "price": price,
            "notes": notes
        }
        if not confirm:
            t = _make_token()
            CONFIRMATION_STORE[t] = draft
            return {"status": "draft", "token": t, "diff_summary": f"Update {holding.stock.symbol}: quantity->{quantity}, price->{price}", "details": draft}
        if not token or token not in CONFIRMATION_STORE:
            return {"status": "error", "message": "Invalid or missing confirmation token"}
        plan = CONFIRMATION_STORE.pop(token)
        service = PortfolioService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from app.schemas.portfolio import PortfolioUpdate
            updated = loop.run_until_complete(service.update_holding(user_id, plan["holding_id"], PortfolioUpdate(quantity=plan["quantity"], purchase_price=plan["price"], notes=plan["notes"])) )
            return {"status": "executed", "result": {"holding_id": updated.id, "symbol": updated.stock.symbol, "quantity": updated.quantity, "purchase_price": float(updated.purchase_price)}}
        finally:
            loop.close()
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Failed to update holding: {str(e)}"}
    finally:
        db.close()


def delete_holding(user_id: int, holding_id: int, confirm: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        holding = db.query(PortfolioModel).filter(PortfolioModel.id == holding_id, PortfolioModel.user_id == user_id).first()
        if not holding:
            return {"status": "error", "message": f"Holding {holding_id} not found"}
        draft = {"action": "delete_holding", "user_id": user_id, "holding_id": holding_id, "symbol": holding.stock.symbol}
        if not confirm:
            t = _make_token()
            CONFIRMATION_STORE[t] = draft
            return {"status": "draft", "token": t, "diff_summary": f"Delete holding {holding.stock.symbol} (id={holding_id})", "details": draft}
        if not token or token not in CONFIRMATION_STORE:
            return {"status": "error", "message": "Invalid or missing confirmation token"}
        plan = CONFIRMATION_STORE.pop(token)
        service = PortfolioService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(service.delete_holding(user_id, plan["holding_id"]))
            return {"status": "executed", "result": {"deleted_holding_id": plan["holding_id"], "symbol": plan["symbol"]}}
        finally:
            loop.close()
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Failed to delete holding: {str(e)}"}
    finally:
        db.close()


def track_stock(user_id: int, symbol: str, baseline_price: Optional[float] = None, confirm: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        stock = db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
        if not stock:
            return {"status": "error", "message": f"Stock {symbol} not found"}
        draft = {"action": "track_stock", "user_id": user_id, "stock_id": stock.id, "symbol": stock.symbol, "baseline_price": baseline_price}
        if not confirm:
            t = _make_token()
            CONFIRMATION_STORE[t] = draft
            return {"status": "draft", "token": t, "diff_summary": f"Track {stock.symbol} baseline={baseline_price}", "details": draft}
        if not token or token not in CONFIRMATION_STORE:
            return {"status": "error", "message": "Invalid or missing confirmation token"}
        plan = CONFIRMATION_STORE.pop(token)
        ts = TrackedStockModel(user_id=user_id, stock_id=plan["stock_id"], baseline_price=plan.get("baseline_price"), is_active="Y")
        db.add(ts)
        db.commit()
        return {"status": "executed", "result": {"symbol": plan["symbol"], "baseline_price": plan.get("baseline_price")}}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Failed to track stock: {str(e)}"}
    finally:
        db.close()


def untrack_stock(user_id: int, symbol: str, confirm: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        stock = db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
        if not stock:
            return {"status": "error", "message": f"Stock {symbol} not found"}
        existing = db.query(TrackedStockModel).filter(TrackedStockModel.user_id == user_id, TrackedStockModel.stock_id == stock.id).first()
        if not existing:
            return {"status": "error", "message": f"{symbol} is not tracked"}
        draft = {"action": "untrack_stock", "user_id": user_id, "stock_id": stock.id, "symbol": stock.symbol}
        if not confirm:
            t = _make_token()
            CONFIRMATION_STORE[t] = draft
            return {"status": "draft", "token": t, "diff_summary": f"Untrack {stock.symbol}", "details": draft}
        if not token or token not in CONFIRMATION_STORE:
            return {"status": "error", "message": "Invalid or missing confirmation token"}
        plan = CONFIRMATION_STORE.pop(token)
        db.delete(existing)
        db.commit()
        return {"status": "executed", "result": {"untracked": plan["symbol"]}}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Failed to untrack stock: {str(e)}"}
    finally:
        db.close()


# ---------- Decrease position (reduce) ----------
class ReduceHoldingInput(BaseModel):
    symbol: str = Field(..., description="Stock symbol to reduce")
    quantity: float = Field(..., description="Quantity to reduce")
    delete_when_zero: bool = Field(False, description="If true and new quantity is 0, delete the holding instead of keeping 0 qty")
    confirm: bool = Field(False, description="Set True to execute after reviewing draft")
    token: Optional[str] = Field(None, description="Confirmation token")


def reduce_holding(user_id: int, symbol: str, quantity: float, delete_when_zero: bool = False, confirm: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
    """Reduce an existing holding quantity. Keeps average cost unchanged for remaining shares.
    If reduction brings quantity to 0, we keep the row with 0 quantity (or this can be extended to delete).
    """
    db = SessionLocal()
    try:
        stock = db.query(StockModel).filter(StockModel.symbol == symbol.upper()).first()
        if not stock:
            return {"status": "error", "message": f"Stock {symbol} not found"}
        holding = db.query(PortfolioModel).filter(PortfolioModel.user_id == user_id, PortfolioModel.stock_id == stock.id).first()
        if not holding:
            return {"status": "error", "message": f"No existing holding for {symbol}"}
        old_qty = float(holding.quantity or 0)
        reduce_qty = float(quantity)
        if reduce_qty <= 0:
            return {"status": "error", "message": "Reduction quantity must be > 0"}
        new_qty = max(old_qty - reduce_qty, 0.0)
        draft = {
            "action": "reduce_holding",
            "user_id": user_id,
            "holding_id": holding.id,
            "symbol": stock.symbol,
            "old_quantity": old_qty,
            "reduce_by": reduce_qty,
            "new_quantity": new_qty,
            "purchase_price_unchanged": float(holding.purchase_price or 0),
            "delete_when_zero": bool(delete_when_zero)
        }
        if not confirm:
            t = _make_token()
            CONFIRMATION_STORE[t] = draft
            return {"status": "draft", "token": t, "diff_summary": f"Reduce {stock.symbol}: {old_qty}→{new_qty} (-{reduce_qty})", "details": draft}
        if not token or token not in CONFIRMATION_STORE:
            return {"status": "error", "message": "Invalid or missing confirmation token"}
        plan = CONFIRMATION_STORE.pop(token)
        from app.schemas.portfolio import PortfolioUpdate
        service = PortfolioService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if plan.get("new_quantity", 0) == 0 and plan.get("delete_when_zero"):
                loop.run_until_complete(service.delete_holding(user_id, plan["holding_id"]))
                return {"status": "executed", "result": {"deleted_holding_id": plan["holding_id"], "symbol": plan["symbol"]}}
            updated = loop.run_until_complete(service.update_holding(user_id, plan["holding_id"], PortfolioUpdate(quantity=plan["new_quantity"], purchase_price=None, notes=None)))
            return {"status": "executed", "result": {"holding_id": updated.id, "symbol": updated.stock.symbol, "quantity": updated.quantity, "purchase_price": float(updated.purchase_price)}}
        finally:
            loop.close()
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Failed to reduce holding: {str(e)}"}
    finally:
        db.close()


