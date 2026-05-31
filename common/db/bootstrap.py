"""
数据库初始化入口

启动时调用 init_db()：
  1. 执行 schema.sql 建表（CREATE TABLE IF NOT EXISTS，幂等）
  2. 执行 seed.py 灌初始化数据（幂等）
"""
from pathlib import Path

from loguru import logger
from sqlalchemy import text

from common.db.session import async_engine

_DB_DIR = Path(__file__).parent


async def init_db():
    """数据库初始化（幂等，启动时安全调用）"""
    logger.info("开始数据库初始化...")

    # 1. 建表
    await _execute_sql_file(_DB_DIR / "schema.sql")

    # 2. 种子数据
    from common.db.seed import seed
    await seed()

    logger.info("数据库初始化完成")


async def _execute_sql_file(path: Path):
    """逐条执行 SQL 文件（按分号+空行分割）"""
    content = path.read_text(encoding="utf-8")
    # 按 ";\n\n" 分割（每条语句之间有空行）
    statements = [s.strip() for s in content.split(";\n\n") if s.strip()]
    async with async_engine.begin() as conn:
        for stmt in statements:
            # 跳过纯注释行
            clean = "\n".join(
                line for line in stmt.splitlines()
                if line.strip() and not line.strip().startswith("--")
            )
            if clean:
                await conn.execute(text(clean))
