"""Auto-generated from account_ops.py split"""
from __future__ import annotations
from loguru import logger
from sqlalchemy import select, update as sa_update, text
from sqlalchemy.ext.asyncio import AsyncSession
from common.db.session import async_session_maker
from common.models.xy_account import XYAccount


async def insert_or_update_order(
    order_id: str,
    item_id: str = None,
    buyer_id: str = None,
    cookie_id: str = None,
    chat_id: str = None,
    **kwargs,
) -> bool:
    """插入或更新订单(已存在则只补空字段;不存在则新建)

    新建时必须能解析出 owner_id(xy_orders.owner_id 为 NOT NULL),
    解析不到则放弃插入并返回 False(与历史行为保持一致)。
    """
    from datetime import datetime
    from sqlalchemy import select
    from common.models.xy_order import XYOrder
    try:
        async with async_session_maker() as session:
            stmt = select(XYOrder).where(XYOrder.order_no == order_id)
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if existing:
                # 只补空字段,不覆盖已有值
                if item_id and not existing.item_id:
                    existing.item_id = item_id
                if buyer_id and not existing.buyer_id:
                    existing.buyer_id = buyer_id
                if chat_id and not existing.chat_id:
                    existing.chat_id = chat_id
                if cookie_id and not existing.account_id:
                    existing.account_id = cookie_id
                await session.commit()
                return True

            # 新建:owner_id 为 NOT NULL,必须先解析
            owner_id = None
            if cookie_id:
                account_result = await session.execute(
                    select(XYAccount.owner_id).where(XYAccount.account_id == cookie_id)
                )
                owner_id = account_result.scalar_one_or_none()
            if not owner_id:
                logger.warning(f"无法解析 owner_id,跳过订单插入: {order_id}")
                return False

            order = XYOrder(
                order_no=order_id,
                owner_id=owner_id,
                item_id=item_id or "",
                buyer_id=buyer_id or "",
                chat_id=chat_id or "",
                account_id=cookie_id,
                status="processing",
                created_at=datetime.now(),
            )
            session.add(order)
            await session.commit()
            logger.info(f"插入新订单成功: {order_id}, item_id={item_id}, buyer_id={buyer_id}")
            return True
    except Exception as e:
        logger.error(f"插入/更新订单失败 [{order_id}]: {e}")
        return False


async def update_order_bargain_status(order_id: str, is_bargain: bool = True) -> bool:
    """更新订单小刀状态"""
    from sqlalchemy import update as sa_update
    from common.models.xy_order import XYOrder
    try:
        async with async_session_maker() as session:
            stmt = sa_update(XYOrder).where(XYOrder.order_no == order_id).values(is_bargain=is_bargain)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新小刀状态失败 [{order_id}]: {e}")
        return False


async def update_order_yifan_status(order_id: str, **kwargs) -> bool:
    """更新订单亦凡状态"""
    from sqlalchemy import update as sa_update
    from common.models.xy_order import XYOrder
    values = {}
    if "yifan_order_no" in kwargs:
        values["yifan_order_no"] = kwargs["yifan_order_no"]
    if "chat_id" in kwargs:
        values["chat_id"] = kwargs["chat_id"]
    if not values:
        return True
    try:
        async with async_session_maker() as session:
            stmt = sa_update(XYOrder).where(XYOrder.order_no == order_id).values(**values)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新订单亦凡状态失败 [{order_id}]: {e}")
        return False


async def update_order_chat_id(order_id: str, chat_id: str) -> bool:
    """更新订单 chat_id"""
    return await update_order_yifan_status(order_id, chat_id=chat_id)
