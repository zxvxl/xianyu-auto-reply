"""
订单服务

功能：
1. 订单列表查询（支持按账号、状态筛选）
2. 订单详情查询
3. 订单状态更新
4. 待发货订单查询
5. 关联商品表获取商品标题

此服务位于common目录下，供backend-web和websocket服务共同使用
"""
from __future__ import annotations

import asyncio
from typing import Optional, Dict

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from common.models.xy_order import XYOrder
from common.models.xy_catalog_item import XYCatalogItem


class OrderService:
    """订单服务 - 读写xy_orders表"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_item_titles(self, owner_id: int | None, item_ids: list[str]) -> Dict[str, str]:
        """批量获取商品标题
        
        Args:
            owner_id: 用户ID，None表示不限制用户（管理员）
            item_ids: 商品ID列表
            
        Returns:
            {item_id: title} 字典
        """
        if not item_ids:
            return {}
        
        try:
            unique_item_ids = list(set(item_ids))
            stmt = select(XYCatalogItem.item_id, XYCatalogItem.title).where(
                XYCatalogItem.item_id.in_(unique_item_ids)
            )
            if owner_id is not None:
                stmt = stmt.where(XYCatalogItem.owner_id == owner_id)
            result = await self.session.execute(stmt)
            return {row.item_id: row.title or "" for row in result.all()}
        except Exception as e:
            logger.warning(f"获取商品标题失败: {e}")
            return {}

    async def list_orders(
        self,
        owner_id: int | None,
        *,
        account_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        delivery_method: str | None = None,
        is_bargain: bool | None = None,
        is_rated: bool | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[XYOrder], int, Dict[str, str]]:
        """获取订单列表（分页），支持多条件筛选
        
        Args:
            owner_id: 用户ID，None表示查询所有用户（管理员）
            account_id: 账号ID筛选
            status: 订单状态筛选
            search: 搜索关键词（匹配订单号、商品ID、买家ID）
            delivery_method: 发货方式筛选（manual/auto/scheduled）
            is_bargain: 是否小刀筛选
            is_rated: 是否已评价筛选
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            page: 页码
            page_size: 每页数量
            
        Returns:
            (订单列表, 总数, 商品标题字典)
        """
        from sqlalchemy import and_, or_
        from datetime import datetime, timedelta
        
        base_stmt = select(XYOrder)
        conditions = []
        
        if owner_id is not None:
            conditions.append(XYOrder.owner_id == owner_id)
        if account_id:
            conditions.append(XYOrder.account_id == account_id)
        if status:
            conditions.append(XYOrder.status == status)
        
        # 搜索关键词（模糊匹配订单号、商品ID、买家ID）
        if search:
            conditions.append(
                or_(
                    XYOrder.order_no.ilike(f"%{search}%"),
                    XYOrder.item_id.ilike(f"%{search}%"),
                    XYOrder.buyer_id.ilike(f"%{search}%"),
                )
            )
        
        # 发货方式筛选
        if delivery_method is not None:
            if delivery_method == "none":
                # 未发货：delivery_method 为空或 None
                conditions.append(
                    or_(
                        XYOrder.delivery_method.is_(None),
                        XYOrder.delivery_method == ""
                    )
                )
            else:
                conditions.append(XYOrder.delivery_method == delivery_method)
        
        # 是否小刀筛选
        if is_bargain is not None:
            conditions.append(XYOrder.is_bargain == is_bargain)
        
        # 是否已评价筛选
        if is_rated is not None:
            conditions.append(XYOrder.is_rated == is_rated)
        
        # 时间范围筛选
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                conditions.append(XYOrder.placed_at >= start_dt)
            except ValueError:
                logger.warning(f"无效的开始日期格式: {start_date}")
        
        if end_date:
            try:
                # 结束日期需要加一天，以包含当天的所有数据
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                conditions.append(XYOrder.placed_at < end_dt)
            except ValueError:
                logger.warning(f"无效的结束日期格式: {end_date}")
        
        if conditions:
            base_stmt = base_stmt.where(and_(*conditions))
        
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        
        offset = (page - 1) * page_size
        # MySQL 不支持 NULLS LAST，用 CASE WHEN 实现 NULL 排最后
        from sqlalchemy import case
        stmt = base_stmt.order_by(
            case((XYOrder.placed_at.is_(None), 1), else_=0),
            XYOrder.placed_at.desc()
        ).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        orders = list(result.scalars().all())
        
        item_ids = [order.item_id for order in orders if order.item_id]
        item_titles = await self._get_item_titles(owner_id, item_ids)
        
        return orders, total, item_titles

    async def get_order_by_id(self, order_no: str) -> Optional[XYOrder]:
        """根据订单号获取订单"""
        stmt = select(XYOrder).where(XYOrder.order_no == order_no)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_item_title(self, owner_id: int, item_id: str) -> str:
        """获取单个商品标题"""
        if not item_id:
            return ""
        
        try:
            stmt = select(XYCatalogItem.title).where(
                XYCatalogItem.owner_id == owner_id,
                XYCatalogItem.item_id == item_id
            ).limit(1)
            result = await self.session.execute(stmt)
            row = result.scalar()
            return row or ""
        except Exception as e:
            logger.warning(f"获取商品标题失败: {e}")
            return ""

    async def get_order_by_no(self, order_no: str) -> Optional[XYOrder]:
        """根据订单号获取订单（别名方法）"""
        return await self.get_order_by_id(order_no)

    async def update_order_status(self, order_no: str, status: str) -> bool:
        """更新订单状态"""
        try:
            stmt = (
                update(XYOrder)
                .where(XYOrder.order_no == order_no)
                .values(status=status)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
            await self.session.rollback()
            return False

    async def update_order_chat_id(self, order_no: str, chat_id: str) -> bool:
        """更新订单的聊天会话ID（chat_id）
        
        场景：订单手动发货时发现 chat_id 为空，
        调用闲鱼 LWP 接口创建会话后，补写回订单表。
        
        Args:
            order_no: 订单号
            chat_id: 聊天会话ID（不带 @goofish 后缀）
            
        Returns:
            是否更新成功
        """
        if not chat_id:
            logger.warning(f"更新订单 chat_id 失败: chat_id 为空 (order_no={order_no})")
            return False
        try:
            stmt = (
                update(XYOrder)
                .where(XYOrder.order_no == order_no)
                .values(chat_id=chat_id)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"更新订单 chat_id 失败: order_no={order_no}, chat_id={chat_id}, 错误={e}")
            await self.session.rollback()
            return False

    async def get_pending_order_by_buyer(
        self,
        account_pk: int,
        buyer_id: str,
        item_id: Optional[str] = None,
    ) -> Optional[XYOrder]:
        """根据买家ID获取待发货订单
        
        Args:
            account_pk: 账号主键
            buyer_id: 买家ID
            item_id: 商品ID（可选）
            
        Returns:
            待发货订单或None
        """
        try:
            from common.models.xy_account import XYAccount
            
            account_stmt = select(XYAccount).where(XYAccount.id == account_pk)
            account_result = await self.session.execute(account_stmt)
            account = account_result.scalars().first()
            
            if not account:
                return None
            
            stmt = select(XYOrder).where(
                XYOrder.owner_id == account.owner_id,
                XYOrder.account_id == account.account_id,
                XYOrder.buyer_id == buyer_id,
                XYOrder.status.in_(["pending", "paid", "待发货"]),
            )
            
            if item_id:
                stmt = stmt.where(XYOrder.item_id == item_id)
            
            stmt = stmt.order_by(XYOrder.created_at.desc()).limit(1)
            result = await self.session.execute(stmt)
            return result.scalars().first()
            
        except Exception as e:
            logger.error(f"获取待发货订单失败: {e}")
            return None

    async def update_order_delivery_info(
        self,
        order_no: str,
        status: str,
        delivery_method: str,
        delivery_content: str | None = None,
        buyer_fish_nick: str | None = None,
    ) -> bool:
        """更新订单发货信息
        
        Args:
            order_no: 订单号
            status: 新状态
            delivery_method: 发货方式 (manual-手动发货, auto-自动发货, scheduled-定时发货)
            delivery_content: 发货内容（卡券内容）
            buyer_fish_nick: 买家闲鱼昵称（明文）
            
        Returns:
            是否更新成功
        """
        try:
            if delivery_content and len(delivery_content) > 2000:
                delivery_content = delivery_content[:1997] + "..."
            
            values = {
                "status": status,
                "delivery_method": delivery_method,
                "delivery_content": delivery_content,
                "delivery_fail_reason": None,  # 发货成功，清空失败原因
            }
            if buyer_fish_nick:
                values["buyer_fish_nick"] = buyer_fish_nick

            stmt = (
                update(XYOrder)
                .where(XYOrder.order_no == order_no)
                .values(**values)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"更新订单发货信息失败: {e}")
            await self.session.rollback()
            return False

    async def record_delivery_for_closed_order(
        self,
        order_no: str,
        delivery_method: str,
        delivery_content: str | None = None,
        buyer_fish_nick: str | None = None,
    ) -> bool:
        """专为「禁止发货 + 主动关闭订单 + 关闭后只发卡券」场景设计的记录方法

        与 update_order_delivery_info 的区别：
          - 不修改 status：因为订单已经被卖家主动关闭（status 已由关闭流程更新），
            这里再标记为 'shipped' 会导致与闲鱼平台真实状态冲突
          - 不清空 delivery_fail_reason：保留 pre_delivery_check_and_close 写入的
            "禁止发货原因"，便于后续追溯为什么走了 card_only 流程

        仅更新 delivery_method 和 delivery_content，让卖家能在订单详情看到补发的卡券内容。

        Args:
            order_no: 订单号
            delivery_method: 发货方式（沿用 'auto' / 'manual' / 'scheduled' 等）
            delivery_content: 补发的卡券内容（>2000 字会截断）
            buyer_fish_nick: 买家闲鱼昵称（明文）

        Returns:
            是否更新成功
        """
        try:
            if delivery_content and len(delivery_content) > 2000:
                delivery_content = delivery_content[:1997] + "..."

            values = {
                "delivery_method": delivery_method,
                "delivery_content": delivery_content,
            }
            if buyer_fish_nick:
                values["buyer_fish_nick"] = buyer_fish_nick

            stmt = (
                update(XYOrder)
                .where(XYOrder.order_no == order_no)
                .values(**values)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"记录已关闭订单的卡券补发信息失败: {e}")
            await self.session.rollback()
            return False

    async def update_order_delivery_fail_reason(
        self,
        order_no: str,
        fail_reason: str
    ) -> bool:
        """更新订单发货失败原因
        
        Args:
            order_no: 订单号
            fail_reason: 发货失败原因
            
        Returns:
            是否更新成功
        """
        try:
            if fail_reason and len(fail_reason) > 2000:
                fail_reason = fail_reason[:1997] + "..."
            
            stmt = (
                update(XYOrder)
                .where(XYOrder.order_no == order_no)
                .values(delivery_fail_reason=fail_reason)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"更新订单发货失败原因失败: {e}")
            await self.session.rollback()
            return False

    async def create_order_from_message(
        self,
        order_no: str,
        account_id: str,
        status: str,
        item_id: str = None,
        buyer_id: str = None,
        chat_id: str = None,
        price: str = None,
    ) -> bool:
        """从消息创建订单记录
        
        Args:
            order_no: 订单号
            account_id: 账号ID
            status: 订单状态
            item_id: 商品ID（可选）
            buyer_id: 买家ID（可选）
            chat_id: 聊天会话ID（可选）
            price: 价格（可选）
            
        Returns:
            是否创建成功
        """
        try:
            from common.models.xy_account import XYAccount
            from common.models.xy_catalog_item import XYCatalogItem
            
            # 获取账号信息
            account_stmt = select(XYAccount).where(XYAccount.account_id == account_id)
            account_result = await self.session.execute(account_stmt)
            account = account_result.scalars().first()
            
            if not account:
                logger.warning(f"创建订单失败：账号 {account_id} 不存在")
                return False
            
            # 如果提供了商品ID，验证商品是否属于当前账号
            if item_id:
                item_stmt = select(XYCatalogItem).where(
                    XYCatalogItem.item_id == item_id,
                    XYCatalogItem.account_pk == account.id
                )
                item_result = await self.session.execute(item_stmt)
                item = item_result.scalars().first()
                
                if not item:
                    logger.warning(
                        f"创建订单失败：商品 {item_id} 不属于账号 {account_id} "
                        f"(account_pk={account.id})，跳过处理"
                    )
                    return False
            
            # 检查订单是否已存在
            existing_stmt = select(XYOrder).where(XYOrder.order_no == order_no)
            existing_result = await self.session.execute(existing_stmt)
            existing_order = existing_result.scalars().first()
            
            if existing_order:
                # 订单已存在，准备更新字段
                update_values = {}
                
                # 如果要更新item_id，需要验证商品归属
                if item_id and not existing_order.item_id:
                    item_stmt = select(XYCatalogItem).where(
                        XYCatalogItem.item_id == item_id,
                        XYCatalogItem.account_pk == account.id
                    )
                    item_result = await self.session.execute(item_stmt)
                    item = item_result.scalars().first()
                    
                    if not item:
                        logger.warning(
                            f"更新订单失败：商品 {item_id} 不属于账号 {account_id} "
                            f"(account_pk={account.id})，跳过更新"
                        )
                        return False
                    
                    update_values['item_id'] = item_id
                
                if buyer_id and not existing_order.buyer_id:
                    update_values['buyer_id'] = buyer_id
                if chat_id and not existing_order.chat_id:
                    update_values['chat_id'] = chat_id
                
                if update_values:
                    update_stmt = update(XYOrder).where(XYOrder.order_no == order_no).values(**update_values)
                    await self.session.execute(update_stmt)
                    await self.session.commit()
                    logger.info(f"订单 {order_no} 已存在，更新字段: {update_values}")
                else:
                    logger.info(f"订单 {order_no} 已存在，无需更新")
                return True
            
            # 创建新订单（使用当前北京时间作为下单时间）
            from datetime import datetime, timezone, timedelta
            beijing_tz = timezone(timedelta(hours=8))
            now_beijing = datetime.now(beijing_tz).replace(tzinfo=None)
            
            new_order = XYOrder(
                owner_id=account.owner_id,
                account_id=account_id,
                order_no=order_no,
                item_id=item_id or "",
                buyer_id=buyer_id or "",
                chat_id=chat_id or "",
                amount=price or None,
                status=status,
                placed_at=now_beijing,
            )
            self.session.add(new_order)
            await self.session.commit()
            logger.info(f"订单 {order_no} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            await self.session.rollback()
            return False

    async def delete_order(self, order_id: int, owner_id: int) -> bool:
        """删除订单
        
        Args:
            order_id: 订单ID（主键）
            owner_id: 用户ID（用于权限验证）
            
        Returns:
            是否删除成功
        """
        try:
            stmt = select(XYOrder).where(
                XYOrder.id == order_id,
                XYOrder.owner_id == owner_id
            )
            result = await self.session.execute(stmt)
            order = result.scalars().first()
            
            if not order:
                return False
            
            delete_stmt = delete(XYOrder).where(XYOrder.id == order_id)
            await self.session.execute(delete_stmt)
            await self.session.commit()
            logger.info(f"订单 {order_id} 删除成功")
            return True
            
        except Exception as e:
            logger.error(f"删除订单失败: {e}")
            await self.session.rollback()
            return False

    async def batch_delete_orders(self, order_ids: list[int], owner_id: int) -> dict:
        """批量删除订单
        
        Args:
            order_ids: 订单ID列表（主键）
            owner_id: 用户ID（用于权限验证，None表示管理员）
            
        Returns:
            { deleted: int, failed: int }
        """
        deleted = 0
        failed = 0
        try:
            conditions = [XYOrder.id.in_(order_ids)]
            if owner_id is not None:
                conditions.append(XYOrder.owner_id == owner_id)
            
            delete_stmt = delete(XYOrder).where(*conditions)
            result = await self.session.execute(delete_stmt)
            await self.session.commit()
            deleted = result.rowcount
            failed = len(order_ids) - deleted
            logger.info(f"批量删除订单: 删除{deleted}条, 失败{failed}条")
        except Exception as e:
            logger.error(f"批量删除订单失败: {e}")
            await self.session.rollback()
            failed = len(order_ids)
        
        return {'deleted': deleted, 'failed': failed}

    # ---- 获取闲鱼卖家订单列表 ----

    # 闲鱼订单状态 → 系统状态映射
    _XIANYU_STATUS_MAP = {
        '待付款': 'pending_payment',
        '待发货': 'pending_ship',
        '已发货': 'shipped',
        '交易成功': 'completed',
        '交易关闭': 'cancelled',
        '退款中': 'refunding',
    }
    _XIANYU_ORDER_PAGE_SIZE = 30

    async def fetch_xianyu_orders(self, account) -> dict:
        """获取闲鱼卖家已售订单并同步到数据库
        
        Args:
            account: XYAccount 对象，需要 cookie / account_id / owner_id
            
        Returns:
            { total_fetched, new_inserted, updated, failed, errors }
        """
        import asyncio
        
        cookies_str = account.cookie
        total_fetched = 0
        new_inserted = 0
        updated = 0
        failed = 0
        errors = []
        try:
            first_page_data = await self._fetch_sold_orders_page(
                cookies_str, 1, account_id=account.account_id
            )
        except Exception as e:
            errors.append(f"第1页请求失败: {str(e)}")
            logger.error(f"获取闲鱼订单第1页失败: {e}")
            return {
                'total_fetched': total_fetched,
                'new_inserted': new_inserted,
                'updated': updated,
                'failed': failed,
                'errors': errors,
            }

        if not first_page_data:
            errors.append("第1页返回空数据")
            return {
                'total_fetched': total_fetched,
                'new_inserted': new_inserted,
                'updated': updated,
                'failed': failed,
                'errors': errors,
            }

        if first_page_data.get('cookies_str') and first_page_data['cookies_str'] != cookies_str:
            cookies_str = first_page_data['cookies_str']
            logger.info("获取闲鱼订单: Cookie已通过Set-Cookie刷新，后续页使用最新Cookie")

        if first_page_data.get('error'):
            errors.append(first_page_data['error'])
            return {
                'total_fetched': total_fetched,
                'new_inserted': new_inserted,
                'updated': updated,
                'failed': failed,
                'errors': errors,
            }

        total_count = first_page_data.get('total_count', 0)
        total_pages = max(1, (total_count + self._XIANYU_ORDER_PAGE_SIZE - 1) // self._XIANYU_ORDER_PAGE_SIZE)
        logger.info(f"获取闲鱼订单: 账号 {account.account_id} 总数{total_count}, 预计共{total_pages}页")

        for page in range(1, total_pages + 1):
            if page == 1:
                page_data = first_page_data
            else:
                try:
                    page_data = await self._fetch_sold_orders_page(
                        cookies_str, page, account_id=account.account_id
                    )
                except Exception as e:
                    errors.append(f"第{page}页请求失败: {str(e)}")
                    logger.error(f"获取闲鱼订单第{page}页失败: {e}")
                    break

                if not page_data:
                    errors.append(f"第{page}页返回空数据")
                    break

                if page_data.get('cookies_str') and page_data['cookies_str'] != cookies_str:
                    cookies_str = page_data['cookies_str']
                    logger.info("获取闲鱼订单: Cookie已通过Set-Cookie刷新，后续页使用最新Cookie")

                if page_data.get('error'):
                    errors.append(page_data['error'])
                    break

            items = page_data.get('items', [])
            next_page = page_data.get('next_page', False)

            if not items:
                logger.info(f"获取闲鱼订单: 第{page}/{total_pages}页无数据，结束获取")
                break

            parsed_items = []
            unique_order_nos = []
            seen_order_nos = set()
            page_parse_failed = 0

            for item in items:
                parsed = self._parse_sold_order_item(item)
                if not parsed or not parsed.get('order_no'):
                    failed += 1
                    page_parse_failed += 1
                    continue
                parsed_items.append(parsed)
                order_no = parsed['order_no']
                if order_no not in seen_order_nos:
                    seen_order_nos.add(order_no)
                    unique_order_nos.append(order_no)

            existing_orders_map = {}
            if unique_order_nos:
                existing_stmt = select(XYOrder).where(
                    XYOrder.account_id == account.account_id,
                    XYOrder.order_no.in_(unique_order_nos)
                )
                existing_result = await self.session.execute(existing_stmt)
                existing_orders_map = {
                    existing.order_no: existing
                    for existing in existing_result.scalars().all()
                }

            page_all_existing = (
                page_parse_failed == 0
                and bool(unique_order_nos)
                and len(existing_orders_map) == len(unique_order_nos)
            )

            for parsed in parsed_items:
                try:
                    result = await self._upsert_order(
                        parsed,
                        account,
                        existing=existing_orders_map.get(parsed['order_no'])
                    )
                    total_fetched += 1
                    if result == 'inserted':
                        new_inserted += 1
                    elif result == 'updated':
                        updated += 1
                except Exception as e:
                    await self.session.rollback()
                    failed += 1
                    logger.error(f"处理订单异常: {e}")

            logger.info(
                f"获取闲鱼订单: 第{page}/{total_pages}页完成, 本页{len(items)}条, "
                f"累计{total_fetched}条, 总数{total_count}, 全页已存在={page_all_existing}"
            )

            if page_all_existing:
                logger.info(f"获取闲鱼订单: 第{page}页订单已全部存在，停止继续获取更早页")
                break

            if not next_page or page >= total_pages:
                break

            await asyncio.sleep(1.5)

        return {
            'total_fetched': total_fetched,
            'new_inserted': new_inserted,
            'updated': updated,
            'failed': failed,
            'errors': errors,
        }

    async def _fetch_sold_orders_page(
        self, cookies_str: str, page: int,
        account_id: str = None, is_retry: bool = False
    ) -> Optional[dict]:
        """获取闲鱼卖家已售订单的单页数据
        
        支持令牌过期自动刷新Cookie并重试一次
        
        Args:
            cookies_str: Cookie字符串
            page: 页码（从1开始）
            account_id: 账号ID，用于令牌过期时更新数据库Cookie（可选）
            is_retry: 是否为令牌过期后的重试请求
            
        Returns:
            { items, next_page, total_count, error }
        """
        import json
        import time
        import aiohttp
        from common.utils.xianyu_utils import trans_cookies, generate_sign
        from common.utils.cookie_refresh import (
            is_token_expired_error, handle_token_expired_response,
            update_account_cookies_in_db,
            is_session_expired_error, trigger_password_login_async,
            mark_account_session_expired
        )
        
        cookies = trans_cookies(cookies_str)
        timestamp = str(int(time.time() * 1000))
        data_val = json.dumps({
            "pageNumber": page,
            "rowsPerPage": self._XIANYU_ORDER_PAGE_SIZE,
            "orderIds": "",
            "queryCode": "ALL",
            "orderSearchParam": "{}"
        }, separators=(',', ':'))
        
        token = cookies.get('_m_h5_tk', '').split('_')[0] if cookies.get('_m_h5_tk') else ''
        sign = generate_sign(timestamp, token, data_val)
        
        params = {
            'jsv': '2.7.2',
            'appKey': '34839810',
            't': timestamp,
            'sign': sign,
            'v': '1.0',
            'type': 'json',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'api': 'mtop.taobao.idle.trade.merchant.sold.get',
            'valueType': 'string',
            'sessionOption': 'AutoLoginOnly',
        }
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'idle_site_biz_code': 'COMMONPRO',
            'cookie': cookies_str,
            'Referer': 'https://seller.goofish.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://h5api.m.goofish.com/h5/mtop.taobao.idle.trade.merchant.sold.get/1.0/',
                params=params,
                data={'data': data_val},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as response:
                res_json = await response.json()
                
                ret = res_json.get('ret', [])
                ret_str = ret[0] if ret else ''
                retry_tag = '[令牌过期重试] ' if is_retry else ''
                
                if 'SUCCESS' not in ret_str:
                    # 检测令牌过期，尝试刷新Cookie并重试
                    if not is_retry and is_token_expired_error(ret):
                        logger.warning(
                            f"账号 {account_id or '未知账号'} 获取闲鱼订单列表第{page}页令牌过期，"
                            f"接口返回: ret={ret}，准备刷新Cookie后重试"
                        )
                        has_new, new_cookies_str = handle_token_expired_response(
                            response, cookies_str
                        )
                        if has_new:
                            if account_id:
                                await update_account_cookies_in_db(account_id, new_cookies_str)
                            # 用新Cookie重试，并将最新Cookie传递给调用方
                            retry_result = await self._fetch_sold_orders_page(
                                new_cookies_str, page, account_id, is_retry=True
                            )
                            if retry_result and 'cookies_str' not in retry_result:
                                retry_result['cookies_str'] = new_cookies_str
                            return retry_result
                        else:
                            logger.warning(f"账号 {account_id or '未知账号'} 获取闲鱼订单列表第{page}页令牌过期，但响应中没有Set-Cookie，无法重试")
                    
                    # 检测Session过期，标记账号冷却并触发后台异步密码登录（不阻塞、不重试）
                    if is_session_expired_error(ret):
                        logger.warning(
                            f"账号 {account_id or '未知账号'} 获取闲鱼订单列表第{page}页Session过期，"
                            f"接口返回: ret={ret}，触发后台异步密码登录"
                        )
                        if account_id:
                            mark_account_session_expired(account_id)
                            trigger_password_login_async(account_id)
                    
                    error_msg = ret_str or '未知错误'
                    logger.warning(
                        f"账号 {account_id or '未知账号'} {retry_tag}获取闲鱼订单列表第{page}页失败: "
                        f"ret={ret}, response={res_json}"
                    )
                    return {'items': [], 'next_page': False, 'total_count': 0, 'error': error_msg}
                
                # 成功时也打印返回值摘要
                logger.info(f"账号 {account_id or '未知账号'} {retry_tag}获取闲鱼订单列表第{page}页成功: ret={ret_str}")
        
        module = res_json.get('data', {}).get('module', {})
        items = module.get('items', [])
        next_page = module.get('nextPage', 'false') == 'true'
        total_count = int(module.get('totalCount', '0'))
        
        return {
            'items': items,
            'next_page': next_page,
            'total_count': total_count,
            'cookies_str': cookies_str,
        }

    def _parse_sold_order_item(self, item: dict) -> Optional[dict]:
        """解析闲鱼卖家订单列表中的单条订单
        
        Args:
            item: API返回的单条订单数据
            
        Returns:
            解析后的订单字典
        """
        from decimal import Decimal
        from datetime import datetime
        
        common = item.get('commonData', {})
        buyer_info = item.get('buyerInfoVO', {})
        price_vo = item.get('priceVO', {})
        right_vo = item.get('rightVO', {})
        
        order_no = common.get('orderId', '')
        if not order_no:
            return None
        
        # 状态映射
        raw_status = common.get('orderStatus', '')
        # 退款中特殊处理
        if common.get('inRefund') == 'true':
            status = 'refunding'
        else:
            status = self._XIANYU_STATUS_MAP.get(raw_status, 'unknown')
        
        # 小刀判断：btnList中存在tradeAction=SKIP_PIN
        is_bargain = False
        btn_list = right_vo.get('btnList', [])
        for btn in btn_list:
            if btn.get('tradeAction') == 'SKIP_PIN':
                is_bargain = True
                break
        
        # 评价状态
        seller_rate_status = common.get('sellerRateStatus', '')
        is_rated = seller_rate_status == '4'
        
        # 金额
        total_price = price_vo.get('totalPrice', '0')
        try:
            amount = Decimal(total_price)
        except Exception:
            amount = None
        
        # 数量
        try:
            quantity = int(price_vo.get('buyNum', '1'))
        except (ValueError, TypeError):
            quantity = 1
        
        # 下单时间
        placed_at = None
        create_time_str = common.get('createTime', '')
        if create_time_str:
            try:
                placed_at = datetime.strptime(create_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        
        return {
            'order_no': order_no,
            'status': status,
            'item_id': common.get('itemId', ''),
            'buyer_id': buyer_info.get('buyerId', ''),
            'buyer_nick': buyer_info.get('userNick', ''),
            'receiver_name': buyer_info.get('name', ''),
            'receiver_phone': buyer_info.get('phone', ''),
            'receiver_address': buyer_info.get('address', ''),
            'amount': amount,
            'quantity': quantity,
            'is_bargain': is_bargain,
            'is_rated': is_rated,
            'placed_at': placed_at,
        }

    async def _upsert_order(self, parsed: dict, account, existing: XYOrder | None = None) -> str:
        """比对并插入或更新订单
        
        Args:
            parsed: 解析后的订单字典
            account: XYAccount 对象
            
        Returns:
            'inserted' / 'updated' / 'skipped'
        """
        order_no = parsed['order_no']

        if existing is None:
            stmt = select(XYOrder).where(
                XYOrder.order_no == order_no,
                XYOrder.account_id == account.account_id
            )
            result = await self.session.execute(stmt)
            existing = result.scalars().first()

        if existing:
            update_values = {}
            # 始终更新状态
            if parsed.get('status') and parsed['status'] != (existing.status or ''):
                update_values['status'] = parsed['status']
            # 补充缺失数据
            if parsed.get('buyer_id') and not existing.buyer_id:
                update_values['buyer_id'] = parsed['buyer_id']
            if parsed.get('buyer_nick') and not existing.buyer_nick:
                update_values['buyer_nick'] = parsed['buyer_nick']
            if parsed.get('item_id') and not existing.item_id:
                update_values['item_id'] = parsed['item_id']
            if parsed.get('amount') is not None and not existing.amount:
                update_values['amount'] = parsed['amount']
            # quantity 同步策略：
            # 旧条件 `not existing.quantity or existing.quantity == 0` 在 existing.quantity=1
            # （Integer 列默认值）时永远为 False，导致一旦订单首次写入就不再同步 quantity，
            # 后续买家改件数（1→2）/ 同步路径首次写入用了默认值 1 等场景都无法纠正。
            # 改为：parsed quantity 解析为正整数且与 DB 现值不同就覆盖，让后续同步能纠正。
            if parsed.get('quantity'):
                try:
                    parsed_qty = int(parsed['quantity'])
                except (TypeError, ValueError):
                    parsed_qty = 0
                if parsed_qty > 0 and parsed_qty != (existing.quantity or 0):
                    update_values['quantity'] = parsed_qty
            # 收货人信息：有新数据且非空时更新
            if parsed.get('receiver_name') and not existing.receiver_name:
                update_values['receiver_name'] = parsed['receiver_name']
            if parsed.get('receiver_phone') and not existing.receiver_phone:
                update_values['receiver_phone'] = parsed['receiver_phone']
            if parsed.get('receiver_address') and not existing.receiver_address:
                update_values['receiver_address'] = parsed['receiver_address']
            # 小刀标记：只标记为True不回退
            if parsed.get('is_bargain') and not existing.is_bargain:
                update_values['is_bargain'] = True
            # 评价状态：始终更新
            if parsed.get('is_rated') != existing.is_rated:
                update_values['is_rated'] = parsed['is_rated']
            # 下单时间
            if parsed.get('placed_at') and not existing.placed_at:
                update_values['placed_at'] = parsed['placed_at']
            
            if update_values:
                update_stmt = (
                    update(XYOrder)
                    .where(XYOrder.id == existing.id)
                    .values(**update_values)
                )
                await self.session.execute(update_stmt)
                await self.session.commit()
                return 'updated'
            return 'skipped'
        else:
            new_order = XYOrder(
                owner_id=account.owner_id,
                account_id=account.account_id,
                order_no=order_no,
                status=parsed.get('status', 'unknown'),
                item_id=parsed.get('item_id', ''),
                buyer_id=parsed.get('buyer_id', ''),
                buyer_nick=parsed.get('buyer_nick', ''),
                receiver_name=parsed.get('receiver_name', ''),
                receiver_phone=parsed.get('receiver_phone', ''),
                receiver_address=parsed.get('receiver_address', ''),
                amount=parsed.get('amount'),
                quantity=parsed.get('quantity', 1),
                is_bargain=parsed.get('is_bargain', False),
                is_rated=parsed.get('is_rated', False),
                placed_at=parsed.get('placed_at'),
                source='fetch_xianyu',
            )
            self.session.add(new_order)
            await self.session.commit()
            return 'inserted'


