"""
HTTP 重试工具

提供简单的异步重试装饰器,用于跨服务 HTTP 调用。
失败时指数退避重试,超过次数后抛出最后一个异常。
"""
from __future__ import annotations

import asyncio
import functools
from typing import Callable, TypeVar

from loguru import logger

T = TypeVar("T")


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """异步重试装饰器

    Args:
        max_attempts: 最大尝试次数(含首次)
        base_delay: 首次重试等待秒数
        backoff_factor: 退避乘数(每次失败后等待时间翻倍)
        exceptions: 需要重试的异常类型

    Usage:
        @async_retry(max_attempts=3, base_delay=1.0)
        async def call_external_service():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.warning(
                            f"[retry] {func.__name__} 失败 {max_attempts} 次,放弃: {e}"
                        )
                        raise
                    delay = base_delay * (backoff_factor ** (attempt - 1))
                    logger.debug(
                        f"[retry] {func.__name__} 第{attempt}次失败,{delay:.1f}s 后重试: {e}"
                    )
                    await asyncio.sleep(delay)
            raise last_exception  # 不应到达

        return wrapper

    return decorator
