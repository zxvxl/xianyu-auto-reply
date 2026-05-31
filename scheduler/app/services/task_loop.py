"""
统一任务循环

消除 11 个重复的 _run_X_loop 方法,提供:
1. 统一的循环逻辑(配置读取 → 是否启用 → 执行 → 等待)
2. Redis 分布式锁(防止多 scheduler 实例重复执行)
"""
from __future__ import annotations

import asyncio
from typing import Any, Protocol

from loguru import logger

from app.services.scheduled_task_service import ScheduledTaskService


class TaskExecutor(Protocol):
    """任务执行器协议(只需有 execute 方法)"""
    async def execute(self) -> Any: ...


async def run_task_loop(
    task_code: str,
    executor: TaskExecutor,
    default_interval: int,
    default_enabled: bool,
    running_flag: asyncio.Event | None = None,
) -> None:
    """统一的定时任务循环

    Args:
        task_code: 任务代码(对应 xy_scheduled_tasks.task_code)
        executor: 任务执行器实例(需要有 .execute() 方法)
        default_interval: 默认执行间隔(秒)
        default_enabled: 默认是否启用
        running_flag: 外部控制的停止标志(set=运行中, clear=停止)
    """
    logger.info(f"[{task_code}] 任务循环开始")

    # 初始加载配置
    try:
        from common.db.session import async_session_maker
        async with async_session_maker() as session:
            service = ScheduledTaskService(session)
            await service.load_task_config(task_code)
    except Exception as e:
        logger.warning(f"[{task_code}] 初始加载配置失败,使用默认值: {e}")

    while running_flag is None or running_flag.is_set():
        # 读取配置
        config = ScheduledTaskService.get_cached_config(task_code)
        if not config:
            config = {"interval_seconds": default_interval, "enabled": default_enabled}

        interval = config.get("interval_seconds", default_interval)
        enabled = config.get("enabled", default_enabled)

        if enabled:
            # 获取 Redis 分布式锁(防多实例重复执行)
            lock_acquired = False
            try:
                lock_acquired = await _try_acquire_task_lock(task_code, ttl=max(interval * 2, 60))
            except Exception as e:
                logger.debug(f"[{task_code}] 获取分布式锁失败(降级为直接执行): {e}")
                lock_acquired = True  # Redis 不可用时降级

            if lock_acquired:
                try:
                    await executor.execute()
                except asyncio.CancelledError:
                    logger.info(f"[{task_code}] 任务被取消")
                    break
                except Exception as e:
                    logger.error(f"[{task_code}] 任务执行异常: {e}")
            else:
                logger.debug(f"[{task_code}] 其他实例正在执行,本轮跳过")

        # 等待下一次执行
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info(f"[{task_code}] 任务等待被取消")
            break

    logger.info(f"[{task_code}] 任务循环结束")


async def _try_acquire_task_lock(task_code: str, ttl: int) -> bool:
    """尝试获取 Redis 任务锁

    key: scheduler:task:{task_code}
    TTL: 2倍间隔时间(确保执行完成前不过期)
    """
    try:
        from common.db.redis_client import get_redis_client
        redis = await get_redis_client()
        key = f"scheduler:task:{task_code}"
        # SET NX EX: 只有不存在时才设置,自动过期
        result = await redis.set(key, "1", nx=True, ex=ttl)
        return result is not None
    except Exception:
        return True  # Redis 不可用时降级为允许执行
