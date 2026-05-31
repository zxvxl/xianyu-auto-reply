"""Auto-generated from account_ops.py split"""
from __future__ import annotations
from loguru import logger
from sqlalchemy import select, update as sa_update, text
from sqlalchemy.ext.asyncio import AsyncSession
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


async def get_account_notifications(cookie_id: str) -> list[dict]:
    """获取账号的通知配置列表

    Args:
        cookie_id: 账号标识

    Returns:
        通知配置列表(含渠道信息)
    """
    from sqlalchemy import select
    from common.models.notification_channel import NotificationChannel
    from common.models.message_notification import MessageNotification

    try:
        async with async_session_maker() as session:
            stmt = (
                select(MessageNotification, NotificationChannel)
                .join(NotificationChannel, MessageNotification.channel_id == NotificationChannel.id)
                .where(
                    MessageNotification.account_identifier == cookie_id,
                    NotificationChannel.enabled == True,
                )
                .order_by(MessageNotification.id)
            )
            result = await session.execute(stmt)
            rows = result.all()

            notifications = []
            for notification, channel in rows:
                notifications.append({
                    "id": notification.id,
                    "channel_id": channel.id,
                    "enabled": notification.enabled,
                    "channel_name": channel.name,
                    "channel_type": channel.channel_type,
                    "channel_config": channel.config_payload,
                })
            return notifications
    except Exception as e:
        logger.error(f"获取账号通知配置失败 [{cookie_id}]: {e}")
        return []


async def get_confirm_before_send(cookie_id: str) -> bool:
    """获取发货成功再发卡券开关设置

    Args:
        cookie_id: 账号标识

    Returns:
        是否启用
    """
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = select(XYAccount.confirm_before_send).where(XYAccount.account_id == cookie_id)
            result = await session.execute(stmt)
            val = result.scalar_one_or_none()
            return bool(val) if val is not None else False
    except Exception as e:
        logger.error(f"获取 confirm_before_send 失败 [{cookie_id}]: {e}")
        return False


async def get_cookie_message_expire_time(cookie_id: str) -> int:
    """获取相同消息等待时间配置"""
    from sqlalchemy import select
    try:
        async with async_session_maker() as session:
            stmt = select(XYAccount.message_expire_time).where(XYAccount.account_id == cookie_id)
            result = await session.execute(stmt)
            val = result.scalar_one_or_none()
            return val if val is not None else 3600
    except Exception as e:
        logger.warning(f"获取 message_expire_time 失败 [{cookie_id}]: {e}")
        return 3600


async def get_account_pk_by_cookie_id(cookie_id: str) -> int | None:
    """获取账号主键ID"""
    from sqlalchemy import select
    try:
        async with async_session_maker() as session:
            stmt = select(XYAccount.id).where(XYAccount.account_id == cookie_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"获取账号主键失败 [{cookie_id}]: {e}")
        return None


async def get_auto_confirm(cookie_id: str) -> bool:
    """获取自动确认发货设置"""
    from sqlalchemy import select
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(XYAccount.auto_confirm).where(XYAccount.account_id == cookie_id)
            )
            val = result.scalar_one_or_none()
            return bool(val) if val is not None else False
    except Exception:
        return False


async def get_cookie_pause_duration(cookie_id: str) -> int:
    """获取暂停时间(分钟)"""
    from sqlalchemy import select
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(XYAccount.pause_duration).where(XYAccount.account_id == cookie_id)
            )
            val = result.scalar_one_or_none()
            return val if val is not None else 10
    except Exception:
        return 10


async def get_cookie_proxy_config(cookie_id: str) -> dict:
    """获取代理配置"""
    from sqlalchemy import select
    default = {"proxy_type": "none", "proxy_host": "", "proxy_port": 0, "proxy_user": "", "proxy_pass": ""}
    try:
        async with async_session_maker() as session:
            stmt = select(
                XYAccount.proxy_type, XYAccount.proxy_host, XYAccount.proxy_port,
                XYAccount.proxy_user, XYAccount.proxy_pass,
            ).where(XYAccount.account_id == cookie_id)
            result = await session.execute(stmt)
            row = result.first()
            if not row:
                return default
            return {"proxy_type": row[0] or "none", "proxy_host": row[1] or "",
                    "proxy_port": row[2] or 0, "proxy_user": row[3] or "", "proxy_pass": row[4] or ""}
    except Exception:
        return default


async def update_cookie_account_info(cookie_id: str, **kwargs) -> bool:
    """更新账号 Cookie 信息"""
    from sqlalchemy import update as sa_update
    values = {}
    if "cookie_value" in kwargs:
        values["cookie"] = kwargs["cookie_value"]
    elif "value" in kwargs:
        values["cookie"] = kwargs["value"]
    if not values:
        return False
    try:
        async with async_session_maker() as session:
            stmt = sa_update(XYAccount).where(XYAccount.account_id == cookie_id).values(**values)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新账号信息失败 [{cookie_id}]: {e}")
        return False
