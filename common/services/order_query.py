"""
订单快捷查询（异步版）

替代 db_manager.get_order_by_id 同步调用。
调用方直接 await 即可,不再需要走 compat.py 的线程桥接。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import select

from common.db.session import async_session_maker
from common.models.xy_order import XYOrder


async def get_order_by_id(order_no: str) -> Optional[Dict[str, Any]]:
    """根据订单号查询订单信息

    Args:
        order_no: 订单号

    Returns:
        订单信息字典,不存在返回 None
    """
    async with async_session_maker() as session:
        stmt = select(XYOrder).where(XYOrder.order_no == order_no)
        result = await session.execute(stmt)
        order = result.scalars().first()
        if not order:
            return None
        return {
            "id": order.id,
            "order_id": order.order_no,
            "account_id": order.account_id,
            "item_id": order.item_id,
            "buyer_id": order.buyer_id,
            "chat_id": order.chat_id,
            "status": order.status,
            "amount": str(order.amount) if order.amount else "0",
            "quantity": order.quantity,
            "is_bargain": order.is_bargain,
        }
