"""
数据库初始化入口

提供：
  - check_database_connection(): 检查数据库连通性
  - init_db(): 建表 + 种子数据（幂等）
"""
from pathlib import Path

from loguru import logger
from sqlalchemy import text

from common.db.session import async_engine


async def check_database_connection() -> bool:
    """检查数据库连接是否正常（SELECT 1）"""
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

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
