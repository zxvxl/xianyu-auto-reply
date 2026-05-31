"""
结构化日志上下文

功能：
1. 提供 context_patcher，将 account_id / chat_id 自动注入日志 message 前缀
2. 各服务入口通过 logger.bind(account_id=..., chat_id=...) 设置上下文
3. 不改变现有 logger.info/warning/error 调用，零侵入

使用方式：
    # 在消息处理入口
    log = logger.bind(account_id="abc123", chat_id="xyz")
    log.info("收到消息")  # 输出: [abc123][xyz] 收到消息

    # 或者用 contextualize（独立 task 内自动隔离）
    with logger.contextualize(account_id="abc123", chat_id="xyz"):
        logger.info("收到消息")  # 输出: [abc123][xyz] 收到消息
"""
from __future__ import annotations


def context_patcher(record: dict) -> None:
    """将上下文信息注入 message 前缀

    在 setup_logging 后调用 logger.patch(context_patcher) 即可生效。
    """
    extra = record["extra"]
    parts = []
    if extra.get("account_id"):
        parts.append(f"[{extra['account_id']}]")
    if extra.get("chat_id"):
        parts.append(f"[chat:{extra['chat_id']}]")
    if parts:
        record["message"] = f"{''.join(parts)} {record['message']}"
