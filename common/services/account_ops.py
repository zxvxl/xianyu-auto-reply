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
