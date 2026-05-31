"""
推广返佣系统 - 数据库检测服务（兼容层）

实际实现已统一到 common.db.bootstrap.check_database_connection
"""
from common.db.bootstrap import check_database_connection

__all__ = ["check_database_connection"]
