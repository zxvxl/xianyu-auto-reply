"""
订单服务模块

此模块供 backend-web、websocket、scheduler 共同使用。
"""
from common.services.order_service_pkg.order_service import OrderService
from common.services.order_service_pkg.order_detail_service import OrderDetailService
from common.services.order_service_pkg.order_status_checker import (
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
