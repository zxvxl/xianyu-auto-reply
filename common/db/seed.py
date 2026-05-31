"""
初始化数据（幂等）

包含：
- 默认管理员 admin/admin123
- 系统设置（13 项）
- 定时任务配置（11 项）
- 随机发布地址（155 条）

所有写入均为幂等操作（INSERT IGNORE / 存在即跳过），可重复执行。
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from common.db.session import async_session_maker
from common.db.default_publish_addresses import build_default_publish_addresses
from common.utils.security import get_password_hash


async def seed():
    """执行所有种子数据写入"""
    await _seed_admin()
    await _seed_system_settings()
    await _seed_scheduled_tasks()
    await _seed_publish_addresses()
    await _seed_redis_platform_day()


# ============================================================
# 默认管理员
# ============================================================

async def _seed_admin():
    """创建默认管理员 admin/admin123（已存在则跳过）"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                text("SELECT id FROM xy_users WHERE username = 'admin' LIMIT 1")
            )
            if result.fetchone():
                return

            password_hash = get_password_hash("admin123")
            await session.execute(
                text("""
                    INSERT INTO xy_users (username, email, password_hash, status, role, created_at, updated_at)
                    VALUES ('admin', 'admin@example.com', :password_hash, 'ACTIVE', 'ADMIN', NOW(), NOW())
                """),
                {"password_hash": password_hash},
            )
            await session.commit()
            logger.info("默认管理员创建成功 (admin/admin123)")
    except IntegrityError:
        pass
    except Exception as e:
        logger.error(f"创建管理员失败: {e}")


# ============================================================
# 系统设置
# ============================================================

_DEFAULT_SETTINGS = (
    ("disclaimer.title", "免责声明", "系统免责声明标题"),
    (
        "disclaimer.content",
        "数据存储说明\n"
        "1. 本系统在运行过程中，为保障服务正常运行，会存储用户账号密码、登录 Cookie、商品信息、卡券信息等业务数据。\n"
        "2. 上述数据仅用于系统功能运行、自动化处理和业务管理，不作为其他用途。\n"
        "3. 请您自行确认服务器环境、账号权限和数据保管措施的安全性。\n"
        "\n"
        "用户须知\n"
        "1. 用户应确保使用本系统的行为符合相关平台规则和法律法规。\n"
        "2. 因用户自身违规操作、账号共享、密码泄露、服务器安全问题导致的损失，由用户自行承担。\n"
        "3. 建议用户定期备份重要数据，因系统故障、第三方平台变更、不可抗力等导致的异常或损失，本系统不承担责任。\n"
        "4. 本系统依赖第三方平台接口和网络环境，无法保证服务始终连续、稳定、无中断。\n"
        "\n"
        "隐私与风险提示\n"
        "1. 请勿在未充分评估风险的情况下接入生产环境或敏感账号。\n"
        "2. 使用本系统即表示您已充分理解并接受相关风险，并愿意自行承担相应责任。",
        "系统免责声明正文",
    ),
    ("disclaimer.checkbox_text", "我已阅读并同意以上免责声明", "免责声明勾选提示文案"),
    ("disclaimer.agree_button_text", "同意并继续", "免责声明同意按钮文案"),
    ("disclaimer.disagree_button_text", "不同意", "免责声明不同意按钮文案"),
    ("login.system_name", "闲鱼管理系统", "登录页系统名称"),
    ("login.system_title", "高效专业的\n闲鱼自动化管理平台", "登录页系统标题"),
    ("login.system_description", "自动回复、智能客服、订单管理、数据分析，一站式解决闲鱼运营难题", "登录页系统描述"),
    (
        "auth.footer_ad_html",
        '© 2026 划算云服务器 ·<a href="http://www.hsykj.com" target="_BLANK">www.hsykj.com</a>',
        "登录页和注册页底部广告 HTML",
    ),
    ("theme.effect", "solid", "系统主题效果（solid-纯色，gradient-炫彩）"),
    ("theme.color_preset", "ocean", "系统主题颜色预设"),
    ("log.retention_days", "7", "日志保留天数（所有模块生效，修改后重启服务生效）"),
    ("show_default_login_info", "true", "登录页是否展示默认账号密码提示"),
)


async def _seed_system_settings():
    """初始化系统设置（已存在则跳过）"""
    try:
        async with async_session_maker() as session:
            for key, value, description in _DEFAULT_SETTINGS:
                await session.execute(
                    text("""
                        INSERT IGNORE INTO xy_system_settings (`key`, value, description, updated_at)
                        VALUES (:key, :value, :description, NOW())
                    """),
                    {"key": key, "value": value, "description": description},
                )
            await session.commit()
    except Exception as e:
        logger.error(f"初始化系统设置失败: {e}")


# ============================================================
# 定时任务配置
# ============================================================

_DEFAULT_TASKS = (
    ("redelivery", "补发货任务", 5, True, "定时补发货任务"),
    ("rate", "补评价任务", 20, True, "定时补评价任务"),
    ("polish", "擦亮任务", 60, True, "定时擦亮商品任务"),
    ("day_switch", "平台日切换任务", 60, True, "定时执行平台日切换任务"),
    ("cleanup_browser_data", "清理被禁用账号浏览器数据任务", 600, False, "定时清理被禁用账号的浏览器数据"),
    ("fetch_orders", "获取闲鱼订单任务", 600, True, "定时获取闲鱼订单数据"),
    ("login_renew", "登录续期任务", 600, False, "定时执行闲鱼账号登录续期"),
    ("cookies_refresh", "COOKIES续期任务", 600, False, "定时执行闲鱼账号浏览器COOKIES续期"),
    ("api_cookie_renew", "接口续期Cookies任务", 3600, True, "定时通过 hasLogin.do 接口为启用账号续期Cookies并同步Set-Cookie"),
    ("close_notice", "关闭账号消息通知任务", 600, False, "定时关闭账号消息通知"),
    ("red_flower", "求小红花任务", 300, True, "定时自动求小红花"),
)


async def _seed_scheduled_tasks():
    """初始化定时任务配置（已存在则跳过）"""
    try:
        async with async_session_maker() as session:
            for task_code, task_name, interval_seconds, enabled, description in _DEFAULT_TASKS:
                await session.execute(
                    text("""
                        INSERT IGNORE INTO xy_scheduled_tasks
                        (task_code, task_name, interval_seconds, enabled, description, created_at, updated_at)
                        VALUES (:task_code, :task_name, :interval_seconds, :enabled, :description, NOW(), NOW())
                    """),
                    {
                        "task_code": task_code,
                        "task_name": task_name,
                        "interval_seconds": interval_seconds,
                        "enabled": enabled,
                        "description": description,
                    },
                )
            await session.commit()
    except Exception as e:
        logger.error(f"初始化定时任务失败: {e}")


# ============================================================
# 随机发布地址
# ============================================================

async def _seed_publish_addresses():
    """初始化随机发布地址（已存在则跳过）"""
    try:
        addresses = build_default_publish_addresses()
        async with async_session_maker() as session:
            for i, addr in enumerate(addresses, 1):
                await session.execute(
                    text("""
                        INSERT IGNORE INTO xy_publish_addresses
                        (name, search_keyword, weight, sort_order, is_enabled, use_count, remark, created_at, updated_at)
                        VALUES (:name, :name, 1, :sort_order, 1, 0, '系统默认', NOW(), NOW())
                    """),
                    {"name": addr, "sort_order": i},
                )
            await session.commit()
    except Exception as e:
        logger.warning(f"初始化随机发布地址失败（不影响系统运行）: {e}")



# ============================================================
# Redis 平台日
# ============================================================

async def _seed_redis_platform_day():
    """初始化 Redis 平台日（已存在则跳过）"""
    try:
        from datetime import datetime
        from common.db.redis_client import get_redis_client

        redis_client = await get_redis_client()
        existing_day = await redis_client.get("platform:day")
        if not existing_day:
            current_day = datetime.now().strftime("%Y-%m-%d")
            await redis_client.set("platform:day", current_day)
            logger.info(f"Redis 平台日初始化: {current_day}")
    except Exception as e:
        logger.warning(f"初始化 Redis 平台日失败（不影响系统运行）: {e}")
