"""
错误码定义

通用错误码，覆盖 90% 场景。
路由中使用: ApiResponse(success=False, code="NOT_FOUND", message="订单不存在")
枚举仅做参考和自动补全，不强制 import。
"""
from enum import Enum


class ErrorCode(str, Enum):
    """通用错误码枚举"""

    # 参数错误（请求体/查询参数不合法）
    PARAM_INVALID = "PARAM_INVALID"

    # 资源不存在
    NOT_FOUND = "NOT_FOUND"

    # 未登录 / Token 过期
    UNAUTHORIZED = "UNAUTHORIZED"

    # 无权限（已登录但无权操作该资源）
    FORBIDDEN = "FORBIDDEN"

    # 冲突（资源已存在 / 重复操作）
    CONFLICT = "CONFLICT"

    # 超出限制（频率限制 / 数量上限）
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"

    # 外部服务错误（闲鱼API / 支付宝 / AI服务不可用）
    EXTERNAL_ERROR = "EXTERNAL_ERROR"

    # 内部错误（未预期的异常）
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # 业务逻辑不满足（前置条件不符合，如余额不足、订单状态不允许）
    BUSINESS_ERROR = "BUSINESS_ERROR"
