"""
消息过滤规则模型

功能：
1. 定义消息过滤规则表结构（xy_message_filters）
2. 按账号维度存储关键词过滤规则
"""
from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base_class import Base, TimestampMixin


class XYMessageFilter(TimestampMixin, Base):
    """消息过滤规则表"""

    __tablename__ = "xy_message_filters"
    __table_args__ = (
        UniqueConstraint("account_id", "keyword", "filter_type", name="uk_account_keyword_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True, comment="账号标识")
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="过滤关键词")
    filter_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="过滤类型")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
