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


async def get_item_multi_quantity_delivery_status(cookie_id: str, item_id: str) -> bool:
    """获取多数量发货状态"""
    info = await get_item_info(cookie_id, item_id)
    return info.get("multi_quantity_delivery", False) if info else False


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


async def increment_delivery_count(card_id: int) -> bool:
    """增加卡券的发货次数"""
    from sqlalchemy import update as sa_update
    from common.models.card import Card
    try:
        async with async_session_maker() as session:
            stmt = sa_update(Card).where(Card.id == card_id).values(
                delivery_count=Card.delivery_count + 1
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"增加发货次数失败 [card_id={card_id}]: {e}")
        return False


async def consume_batch_data(card_id: int) -> str | None:
    """消费批量数据卡券的一条数据(行锁防并发)

    使用 SELECT FOR UPDATE 确保并发安全。
    """
    from sqlalchemy import select
    from common.models.card import Card
    try:
        async with async_session_maker() as session:
            async with session.begin():
                stmt = select(Card).where(Card.id == card_id).with_for_update()
                result = await session.execute(stmt)
                card = result.scalars().first()
                if not card or not card.data_content:
                    return None

                lines = card.data_content.strip().split("\n")
                if not lines:
                    return None

                consumed = lines[0].strip()
                remaining = "\n".join(lines[1:]).strip()
                card.data_content = remaining if remaining else None
                await session.flush()
            return consumed if consumed else None
    except Exception as e:
        logger.error(f"消费批量数据失败 [card_id={card_id}]: {e}")
        return None


async def insert_or_update_order(
    order_id: str,
    item_id: str = None,
    buyer_id: str = None,
    cookie_id: str = None,
    chat_id: str = None,
    **kwargs,
) -> bool:
    """插入或更新订单(只更新空字段)"""
    from sqlalchemy import select
    from common.models.xy_order import XYOrder
    try:
        async with async_session_maker() as session:
            stmt = select(XYOrder).where(XYOrder.order_no == order_id)
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if existing:
                update_values = {}
                if item_id and not existing.item_id:
                    update_values["item_id"] = item_id
                if buyer_id and not existing.buyer_id:
                    update_values["buyer_id"] = buyer_id
                if chat_id and not existing.chat_id:
                    update_values["chat_id"] = chat_id
                if cookie_id and not existing.account_id:
                    update_values["account_id"] = cookie_id
                if update_values:
                    for k, v in update_values.items():
                        setattr(existing, k, v)
                    await session.commit()
            else:
                order = XYOrder(
                    order_no=order_id,
                    item_id=item_id,
                    buyer_id=buyer_id,
                    account_id=cookie_id,
                    chat_id=chat_id,
                    status="pending",
                )
                session.add(order)
                await session.commit()
            return True
    except Exception as e:
        logger.error(f"插入/更新订单失败 [{order_id}]: {e}")
        return False


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


async def update_confirm_receipt_image_url(cookie_id: str, image_url: str) -> bool:
    """更新确认收货消息的图片URL"""
    from sqlalchemy import update as sa_update
    from common.models.confirm_receipt_message import ConfirmReceiptMessage
    try:
        async with async_session_maker() as session:
            stmt = sa_update(ConfirmReceiptMessage).where(
                ConfirmReceiptMessage.account_id == cookie_id
            ).values(message_image=image_url)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新确认收货图片失败 [{cookie_id}]: {e}")
        return False


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
    """添加账号登录日志"""
    from sqlalchemy import text
    try:
        async with async_session_maker() as session:
            # 获取 account pk + owner_id
            from sqlalchemy import select
            stmt = select(XYAccount.id, XYAccount.owner_id).where(XYAccount.account_id == cookie_id)
            result = await session.execute(stmt)
            row = result.first()
            account_pk = row[0] if row else None
            owner_id = row[1] if row else None

            insert_result = await session.execute(
                text("""
                    INSERT INTO xy_account_login_logs
                    (owner_id, account_id, account_identifier, username, trigger_reason,
                     login_status, failure_reason, error_message, updated_cookie_names, duration_ms, created_at)
                    VALUES (:owner_id, :account_id, :identifier, :username, :trigger_reason,
                            :login_status, :failure_reason, :error_message, :updated_cookie_names, :duration_ms, NOW())
                """),
                {
                    "owner_id": owner_id,
                    "account_id": account_pk,
                    "identifier": cookie_id,
                    "username": username,
                    "trigger_reason": trigger_reason,
                    "login_status": login_status,
                    "failure_reason": failure_reason,
                    "error_message": (error_message or "")[:500],
                    "updated_cookie_names": updated_cookie_names,
                    "duration_ms": duration_ms,
                },
            )
            await session.commit()
            return insert_result.lastrowid
    except Exception as e:
        logger.error(f"添加登录日志失败 [{cookie_id}]: {e}")
        return None
