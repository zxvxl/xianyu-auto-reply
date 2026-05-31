"""
统一发货服务

所有发货路径（自动/定时/手动）的共享前置检查逻辑。
确保无论触发来源,发货前检查的判断标准完全一致。

使用方式:
    service = DeliveryPreCheck(account_id=cookie_id)
    result = await service.pre_check(PreCheckRequest(
        account_id=cookie_id, order_no=order_no, buyer_id=buyer_id, item_id=item_id
    ))
    if not result.allowed:
        return  # 不允许发货
    # 继续执行发货...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger


@dataclass
class PreCheckRequest:
    """发货前检查请求"""
    account_id: str
    order_no: str
    buyer_id: str
    item_id: Optional[str] = None
    chat_id: Optional[str] = None
    trigger: str = "auto"  # auto | scheduled | manual


@dataclass
class PreCheckResult:
    """发货前检查结果"""
    allowed: bool = True
    reason: str = ""
    action: str = "allow"  # allow | block | card_only

    # 详细信息(供日志和调试)
    rule_code: Optional[str] = None
    order_amount: Optional[str] = None


class DeliveryPreCheck:
    """统一的发货前检查服务

    检查项（按顺序执行,任一失败即终止）:
    1. 订单金额检查（金额≤0禁止发货）
    2. 禁止发货规则引擎（xy_delivery_block_rules）
    3. 卡券可用性检查（预留,暂不执行）

    注意:Redis 分布式锁由调用方在外层管理,不在此服务内获取/释放。
    """

    def __init__(self, account_id: str):
        self.account_id = account_id

    async def pre_check(self, request: PreCheckRequest) -> PreCheckResult:
        """执行全部前置检查

        注意:本方法不获取 Redis 分布式锁。锁应由调用方在整个发货流程
        的外层管理(覆盖 pre_check + 执行发货 + 写日志的完整生命周期)。
        """
        result = PreCheckResult()

        # 1. 订单金额检查
        amount_ok, amount = await self._check_order_amount(request.order_no)
        result.order_amount = amount
        if not amount_ok:
            result.allowed = False
            result.reason = f"订单金额为 {amount}，禁止发货"
            result.action = "block"
            return result

        # 2. 禁止发货规则引擎
        rule_result = await self._check_delivery_block_rules(
            account_id=request.account_id,
            order_no=request.order_no,
            buyer_id=request.buyer_id,
            item_id=request.item_id,
        )
        if rule_result["action"] != "allow":
            result.allowed = (rule_result["action"] == "card_only")
            result.reason = rule_result.get("reason_text", "禁止发货规则命中")
            result.action = rule_result["action"]
            result.rule_code = rule_result.get("rule_code")
            return result

        # 3. 卡券可用性检查（可选,调用方也会做）
        # 暂不在 pre_check 里做,避免重复查询

        return result

    # ==================== 内部方法 ====================

    async def _check_order_amount(self, order_no: str) -> tuple[bool, str | None]:
        """检查订单金额是否>0"""
        try:
            from common.db.session import async_session_maker
            from sqlalchemy import text

            async with async_session_maker() as session:
                result = await session.execute(
                    text("SELECT amount FROM xy_orders WHERE order_no = :order_no LIMIT 1"),
                    {"order_no": order_no},
                )
                row = result.fetchone()
                if not row:
                    return True, None  # 订单不存在时不拦截(让后续逻辑处理)
                amount = row[0]
                if amount is not None:
                    from decimal import Decimal
                    if Decimal(str(amount)) <= 0:
                        return False, str(amount)
                return True, str(amount) if amount else None
        except Exception as e:
            logger.warning(f"[{self.account_id}] 检查订单金额失败(允许继续): {e}")
            return True, None

    async def _check_delivery_block_rules(
        self,
        account_id: str,
        order_no: str,
        buyer_id: str,
        item_id: str | None,
    ) -> dict:
        """执行禁止发货规则引擎检查

        调用现有的 AutoDeliveryHandler.pre_delivery_check_and_close 中的规则加载逻辑,
        但不执行"关闭订单/发消息"等副作用动作。

        TODO: 后续将 pre_delivery_check_and_close 中的规则判断逻辑
              提取到这里,消除与 AutoDeliveryHandler 的耦合。
        """
        try:
            from common.db.session import async_session_maker
            from sqlalchemy import text

            async with async_session_maker() as session:
                # 查询该账号已启用的禁止发货规则
                result = await session.execute(
                    text("""
                        SELECT rule_code, block_reason, auto_close_order, 
                               only_card_after_close, excluded_item_ids, config
                        FROM xy_delivery_block_rules
                        WHERE account_id = :account_id AND enabled = 1
                        ORDER BY priority ASC
                    """),
                    {"account_id": account_id},
                )
                rules = result.fetchall()

                if not rules:
                    return {"action": "allow"}

                # 逐条规则检查
                for rule in rules:
                    rule_code = rule[0]
                    block_reason = rule[1]
                    auto_close = rule[2]
                    only_card = rule[3]
                    excluded_items = rule[4]  # JSON
                    config = rule[5]  # JSON

                    # 检查排除商品列表
                    if item_id and excluded_items:
                        import json
                        try:
                            excluded = json.loads(excluded_items) if isinstance(excluded_items, str) else excluded_items
                            if item_id in excluded:
                                continue  # 该商品被排除,跳过本规则
                        except Exception:
                            pass

                    # TODO: 根据 rule_code 执行具体检查逻辑
                    # 如 buyer_credit_zero 需要调 API 查买家信用分,当前为 stub
                    # 在具体规则判定逻辑实现前,此处暂时跳过(不拦截)
                    # 实现后取消下面的 continue,改为真正的判定
                    continue  # STUB: 规则判定未实现,暂不拦截

                    # --- 以下为规则命中后的返回(待实现后启用) ---
                    # action = "card_only" if only_card else "block"
                    # return {
                    #     "action": action,
                    #     "reason_text": block_reason or "禁止发货",
                    #     "rule_code": rule_code,
                    #     "auto_close_enabled": bool(auto_close),
                    #     "only_card_enabled": bool(only_card),
                    # }

            return {"action": "allow"}
        except Exception as e:
            logger.warning(f"[{account_id}] 禁止发货规则检查失败(允许继续): {e}")
            return {"action": "allow"}
