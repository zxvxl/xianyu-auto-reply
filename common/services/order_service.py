"""
订单服务（门面模块）

实际实现已拆分到 order_service_pkg/ 子包中。
本文件保持向后兼容，外部 import 路径无需修改。
"""
from common.services.order_service_pkg import (
    OrderService,
    OrderDetailService,
    OrderStatusChecker,
    check_can_ship,
    check_can_rate,
)

__all__ = [
    "OrderService",
    "OrderDetailService",
    "OrderStatusChecker",
    "check_can_ship",
    "check_can_rate",
]
