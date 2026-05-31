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



# ============================================================
# 以下为剩余零散方法的 async 替代(瘦身第七步)
# ============================================================

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


async def get_item_multi_spec_status(cookie_id: str, item_id: str) -> bool:
    """获取商品是否为多规格"""
    info = await get_item_info(cookie_id, item_id)
    return info.get("multi_spec", False) if info else False


async def get_cards_by_item_id(item_id: str, spec_name: str = None, spec_value: str = None) -> list[dict]:
    """通过商品ID获取卡券列表"""
    from common.services.card_matcher import CardMatcher
    try:
        async with async_session_maker() as session:
            matcher = CardMatcher(session)
            return await matcher.get_cards_by_item_id(item_id, spec_name, spec_value)
    except Exception as e:
        logger.error(f"获取卡券失败 [{item_id}]: {e}")
        return []


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


async def update_card_image_url(card_id: int, image_url: str) -> bool:
    """更新卡券图片URL"""
    from sqlalchemy import update as sa_update
    from common.models.card import Card
    try:
        async with async_session_maker() as session:
            stmt = sa_update(Card).where(Card.id == card_id).values(image_url=image_url)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新卡券图片失败 [card_id={card_id}]: {e}")
        return False


async def update_card_image_urls(card_id: int, index: int, cdn_url: str) -> bool:
    """更新卡券多图片列表中指定索引的URL"""
    import json as _json
    from sqlalchemy import select
    from common.models.card import Card
    try:
        async with async_session_maker() as session:
            stmt = select(Card.image_urls).where(Card.id == card_id)
            result = await session.execute(stmt)
            current = result.scalar_one_or_none()
            urls_list = _json.loads(current) if current else []
            while len(urls_list) <= index:
                urls_list.append("")
            urls_list[index] = cdn_url
            from sqlalchemy import update as sa_update
            await session.execute(
                sa_update(Card).where(Card.id == card_id).values(image_urls=_json.dumps(urls_list))
            )
            await session.commit()
            return True
    except Exception as e:
        logger.error(f"更新卡券多图片失败 [card_id={card_id}, index={index}]: {e}")
        return False


async def update_keyword_image_url(cookie_id: str, keyword: str, image_url: str) -> bool:
    """更新关键词图片URL"""
    from sqlalchemy import select, update as sa_update
    from common.models.xy_keyword_rule import XYKeywordRule
    try:
        async with async_session_maker() as session:
            account_result = await session.execute(
                select(XYAccount.id).where(XYAccount.account_id == cookie_id)
            )
            account_pk = account_result.scalar_one_or_none()
            if not account_pk:
                return False
            stmt = sa_update(XYKeywordRule).where(
                XYKeywordRule.account_pk == account_pk, XYKeywordRule.keyword == keyword
            ).values(image_url=image_url)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新关键词图片失败 [{cookie_id}/{keyword}]: {e}")
        return False


async def update_default_reply_image_url(cookie_id: str, image_url: str, item_id: str = None) -> bool:
    """更新默认回复图片URL"""
    from sqlalchemy import update as sa_update
    from common.models.default_reply import DefaultReply
    try:
        async with async_session_maker() as session:
            if item_id:
                stmt = sa_update(DefaultReply).where(
                    DefaultReply.account_id == cookie_id, DefaultReply.item_id == item_id
                ).values(reply_image=image_url)
            else:
                stmt = sa_update(DefaultReply).where(
                    DefaultReply.account_id == cookie_id, DefaultReply.item_id.is_(None)
                ).values(reply_image=image_url)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新默认回复图片失败 [{cookie_id}]: {e}")
        return False
