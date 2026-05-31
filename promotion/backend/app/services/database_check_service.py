"""
推广返佣系统 - 数据库检测服务

功能：检查数据库连接是否正常
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy import text

from common.db.session import async_session_maker


async def check_database_connection() -> bool:
    """检查数据库连接是否正常。"""
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False
