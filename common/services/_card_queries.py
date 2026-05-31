"""Auto-generated from account_ops.py split"""
from __future__ import annotations
from loguru import logger
from sqlalchemy import select, update as sa_update, text
from sqlalchemy.ext.asyncio import AsyncSession
from common.db.session import async_session_maker
from common.models.xy_account import XYAccount


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


async def get_item_multi_quantity_delivery_status(cookie_id: str, item_id: str) -> bool:
    """获取多数量发货状态"""
    info = await get_item_info(cookie_id, item_id)
    return info.get("multi_quantity_delivery", False) if info else False


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

    使用 SELECT FOR UPDATE 行锁 + 显式事务,防止并发重复派发同一卡密。
    行为与历史实现对齐:过滤所有空行,清空后写入空字符串。
    """
    from sqlalchemy import select, update as sa_update
    from common.models.card import Card
    try:
        async with async_session_maker() as session:
            async with session.begin():
                stmt = select(Card).where(Card.id == card_id).with_for_update()
                result = await session.execute(stmt)
                card = result.scalars().first()
                if not card or not card.data_content:
                    logger.warning(f"卡券 {card_id} 不存在或没有批量数据")
                    return None

                # 过滤所有空行(与历史行为一致)
                lines = [line.strip() for line in card.data_content.split("\n") if line.strip()]
                if not lines:
                    logger.warning(f"卡券 {card_id} 批量数据已用完")
                    return None

                consumed = lines[0]
                remaining = lines[1:]
                new_content = "\n".join(remaining) if remaining else ""
                await session.execute(
                    sa_update(Card).where(Card.id == card_id).values(data_content=new_content)
                )
                logger.info(f"卡券 {card_id} 消费数据成功,剩余 {len(remaining)} 条")
                return consumed
    except Exception as e:
        logger.error(f"消费批量数据失败 [card_id={card_id}]: {e}")
        return None


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
