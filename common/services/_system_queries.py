"""Auto-generated from account_ops.py split"""
from __future__ import annotations
from loguru import logger
from sqlalchemy import select, update as sa_update, text
from sqlalchemy.ext.asyncio import AsyncSession
from common.db.session import async_session_maker
from common.models.xy_account import XYAccount


async def get_system_setting(key: str, default: str | None = None) -> str | None:
    """获取系统设置值"""
    from sqlalchemy import select
    from common.models.system_setting import SystemSetting
    try:
        async with async_session_maker() as session:
            stmt = select(SystemSetting.value).where(SystemSetting.key == key)
            result = await session.execute(stmt)
            val = result.scalar_one_or_none()
            return val if val is not None else default
    except Exception as e:
        logger.error(f"获取系统设置失败 [{key}]: {e}")
        return default


async def get_keywords_with_type(cookie_id: str) -> list[dict]:
    """获取账号关键词列表(含类型)"""
    from sqlalchemy import select
    from common.models.xy_keyword_rule import XYKeywordRule
    try:
        async with async_session_maker() as session:
            account_result = await session.execute(
                select(XYAccount.id).where(XYAccount.account_id == cookie_id)
            )
            account_pk = account_result.scalar_one_or_none()
            if not account_pk:
                return []
            stmt = select(XYKeywordRule).where(
                XYKeywordRule.account_pk == account_pk,
                XYKeywordRule.is_active == True,
            )
            result = await session.execute(stmt)
            return [{"id": k.id, "keyword": k.keyword, "reply": k.reply_content,
                     "type": k.reply_type or "text", "item_id": k.item_id,
                     "image_url": k.image_url} for k in result.scalars().all()]
    except Exception as e:
        logger.error(f"获取关键词失败 [{cookie_id}]: {e}")
        return []


async def get_message_filter_keywords(cookie_id: str, filter_type: str = "skip_reply") -> list[str]:
    """获取消息过滤关键词列表"""
    from sqlalchemy import text
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                text("SELECT keyword FROM xy_message_filters WHERE account_id = :aid AND filter_type = :ft AND enabled = 1"),
                {"aid": cookie_id, "ft": filter_type},
            )
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"获取过滤关键词失败 [{cookie_id}]: {e}")
        return []


async def get_user_setting_by_cookie_id(cookie_id: str, key: str) -> str | None:
    """通过 cookie_id 获取用户设置"""
    from sqlalchemy import select
    from common.models.user_setting import UserSetting
    try:
        async with async_session_maker() as session:
            owner_result = await session.execute(
                select(XYAccount.owner_id).where(XYAccount.account_id == cookie_id)
            )
            owner_id = owner_result.scalar_one_or_none()
            if not owner_id:
                return None
            result = await session.execute(
                select(UserSetting.value).where(UserSetting.user_id == owner_id, UserSetting.key == key)
            )
            return result.scalar_one_or_none()
    except Exception:
        return None


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


async def add_risk_control_log(cookie_id: str, event_type: str, event_description: str,
                               processing_status: str = "processing", **kwargs) -> int | None:
    """添加风控日志"""
    from sqlalchemy import select
    from common.models.risk_control_log import XYRiskControlLog
    try:
        async with async_session_maker() as session:
            account_result = await session.execute(
                select(XYAccount.id, XYAccount.owner_id).where(XYAccount.account_id == cookie_id)
            )
            row = account_result.first()
            log = XYRiskControlLog(
                owner_id=row[1] if row else None,
                account_pk=row[0] if row else None,
                account_identifier=cookie_id,
                event_type=event_type,
                event_description=event_description,
                processing_status=processing_status,
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log.id
    except Exception as e:
        logger.error(f"添加风控日志失败 [{cookie_id}]: {e}")
        return None


async def add_account_login_log(
    cookie_id: str,
    login_status: str,
    *,
    username: str | None = None,
    trigger_reason: str | None = None,
    failure_reason: str | None = None,
    error_message: str | None = None,
    updated_cookie_names: str | None = None,
    duration_ms: int | None = None,
) -> int | None:
    """添加账号登录日志(使用 ORM 模型,error_message 完整存储)"""
    from sqlalchemy import select
    from common.models.account_login_log import XYAccountLoginLog
    try:
        async with async_session_maker() as session:
            account_result = await session.execute(
                select(XYAccount.id, XYAccount.owner_id).where(XYAccount.account_id == cookie_id)
            )
            row = account_result.first()
            log = XYAccountLoginLog(
                owner_id=row[1] if row else None,
                account_pk=row[0] if row else None,
                account_identifier=cookie_id,
                username=username,
                trigger_reason=trigger_reason,
                login_status=login_status,
                failure_reason=failure_reason,
                error_message=error_message,
                updated_cookie_names=updated_cookie_names,
                duration_ms=duration_ms,
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log.id
    except Exception as e:
        logger.warning(f"添加账号登录日志失败 [{cookie_id}]: {e}")
        return None



# ============================================================
# 以下为剩余零散方法的 async 替代(瘦身第七步)
# ============================================================
