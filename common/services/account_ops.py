"""
账号操作（异步版）

替代 db_manager 中的账号相关同步方法。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy import update

from common.db.session import async_session_maker
from common.models.xy_account import XYAccount


async def disable_account(cookie_id: str, reason: str = "") -> bool:
    """禁用账号

    Args:
        cookie_id: 账号标识(account_id)
        reason: 禁用原因

    Returns:
        是否成功
    """
    async with async_session_maker() as session:
        values = {"status": "disabled"}
        if reason:
            values["disable_reason"] = reason
        stmt = update(XYAccount).where(
            XYAccount.account_id == cookie_id
        ).values(**values)
        result = await session.execute(stmt)
        await session.commit()

        if result.rowcount > 0:
            logger.warning(f"【{cookie_id}】账号已被禁用，原因: {reason}")
            return True
        return False



async def update_risk_control_log(log_id: int, **kwargs) -> bool:
    """更新风控日志

    Args:
        log_id: 日志ID
        **kwargs: 可更新字段(processing_result, processing_status, error_message)

    Returns:
        是否成功
    """
    from sqlalchemy import update as sa_update
    from common.models.risk_control_log import XYRiskControlLog

    values = {}
    for key in ("processing_result", "processing_status", "error_message"):
        if key in kwargs:
            values[key] = kwargs[key]
    if not values:
        return True

    try:
        async with async_session_maker() as session:
            stmt = sa_update(XYRiskControlLog).where(
                XYRiskControlLog.id == log_id
            ).values(**values)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新风控日志失败: {e}")
        return False


async def get_item_info(cookie_id: str, item_id: str) -> dict | None:
    """获取商品信息

    Args:
        cookie_id: 账号标识
        item_id: 商品ID

    Returns:
        商品信息字典,不存在返回 None
    """
    from sqlalchemy import select
    from common.models.xy_account import XYAccount
    from common.models.xy_catalog_item import XYCatalogItem

    try:
        async with async_session_maker() as session:
            # 获取账号主键
            account_result = await session.execute(
                select(XYAccount.id).where(XYAccount.account_id == cookie_id)
            )
            account_pk = account_result.scalar_one_or_none()
            if not account_pk:
                return None

            stmt = select(XYCatalogItem).where(
                XYCatalogItem.account_pk == account_pk,
                XYCatalogItem.item_id == item_id,
            )
            result = await session.execute(stmt)
            item = result.scalars().first()
            if not item:
                return None

            metadata = item.metadata_json or {}
            return {
                "id": item.id,
                "item_id": item.item_id,
                "item_title": item.title,
                "title": item.title,
                "item_price": str(item.price) if item.price else "0",
                "price": str(item.price) if item.price else "0",
                "item_detail": metadata.get("detail", ""),
                "detail": metadata.get("detail", ""),
                "desc": metadata.get("description", ""),
                "ai_prompt": item.ai_prompt or "",
                "multi_quantity_delivery": metadata.get("multi_quantity_delivery", False),
                "multi_spec": metadata.get("is_multi_spec", False),
            }
    except Exception as e:
        logger.error(f"获取商品信息失败 [{cookie_id}/{item_id}]: {e}")
        return None



async def get_account_details(cookie_id: str) -> dict | None:
    """根据 account_id 获取账号详情

    Args:
        cookie_id: 账号标识(account_id)

    Returns:
        账号信息字典,不存在返回 None
    """
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = select(XYAccount).where(XYAccount.account_id == cookie_id)
            result = await session.execute(stmt)
            account = result.scalars().first()
            if not account:
                return None
            return {
                "id": account.id,
                "cookie_id": account.account_id,
                "cookie_value": account.cookie,
                "user_id": account.owner_id,
                "auto_confirm": account.auto_confirm,
                "remark": account.remark,
                "pause_duration": account.pause_duration,
                "username": account.username,
                "password": account.login_password,
                "show_browser": account.show_browser,
                "proxy_type": account.proxy_type,
                "proxy_host": account.proxy_host,
                "proxy_port": account.proxy_port,
                "proxy_user": account.proxy_user,
                "proxy_pass": account.proxy_pass,
            }
    except Exception as e:
        logger.error(f"获取账号详情失败 [{cookie_id}]: {e}")
        return None
