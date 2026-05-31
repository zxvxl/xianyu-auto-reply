"""
激活码生成日志模型

功能：
1. 定义激活码日志表结构（xy_activation_logs）
2. 记录机器码获取激活码/续期码的每一次操作
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base_class import Base


class XYActivationLog(Base):
    """激活码生成日志表"""

    __tablename__ = "xy_activation_logs"
    __table_args__ = (
        Index("idx_machine_type_time", "machine_id", "code_type", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="机器码")
    code_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="类型：generate/renew")
    generated_code: Mapped[str] = mapped_column(String(255), nullable=False, comment="生成的激活码/续期码")
    days: Mapped[int] = mapped_column(Integer, nullable=False, comment="有效天数")
    ip_address: Mapped[str | None] = mapped_column(String(64), comment="请求IP地址")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )
