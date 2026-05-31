"""订单状态检查服务 - 检查订单是否可以发货/评价"""
from __future__ import annotations

from typing import Dict

from loguru import logger

class OrderStatusChecker:
    """订单状态检查服务
    
    功能：
    1. check_can_ship - 检查订单是否可以发货
    2. check_can_rate - 检查订单是否可以评价
    
    通过调用闲鱼API获取订单状态节点，分析是否满足发货/评价条件
    支持令牌过期自动刷新Cookie并重试
    """
    
    def __init__(self, cookies_str: str, account_id: str = None):
        """初始化订单状态检查服务
        
        Args:
            cookies_str: Cookie字符串
            account_id: 账号ID，用于令牌过期时更新数据库Cookie（可选）
        """
        # 清洗 cookies_str 中的换行符，防止 header injection
        self.cookies_str = (cookies_str or "").replace("\r", "").replace("\n", "")
        self.account_id = account_id
    
    async def check_can_ship(self, order_id: str) -> Dict:
        """检查订单是否可以发货
        
        判断逻辑：
        - 已付款 + 待发货状态 → 可以发货
        - 小刀订单：已付款 + (已刀成/待发货) → 可以发货
        
        Args:
            order_id: 订单号
            
        Returns:
            {
                'success': bool,  # 请求是否成功
                'can_ship': bool,  # 是否可以发货
                'reason': str,  # 原因说明
                'order_status': str  # 当前订单状态描述
            }
        """
        try:
            # 获取原始API响应
            raw_response = await self._fetch_raw_order_detail(order_id)
            if not raw_response:
                return {
                    'success': False,
                    'can_ship': False,
                    'reason': '无法获取订单状态信息',
                    'order_status': '未知'
                }
            
            # 解析订单状态节点
            status_nodes = self._extract_order_status_nodes(raw_response)
            
            # 如果状态节点为空，尝试从 orderStatusInfo 获取状态
            if not status_nodes:
                order_status_title = self._extract_order_status_title(raw_response)
                if order_status_title:
                    if '交易关闭' in order_status_title:
                        await self._update_order_status_to_cancelled(order_id)
                        return {
                            'success': True,
                            'can_ship': False,
                            'reason': '订单已关闭',
                            'order_status': order_status_title
                        }
                    elif '交易成功' in order_status_title:
                        return {
                            'success': True,
                            'can_ship': False,
                            'reason': '订单已交易成功',
                            'order_status': order_status_title
                        }
                
                return {
                    'success': False,
                    'can_ship': False,
                    'reason': '订单状态节点解析失败',
                    'order_status': '未知'
                }
            
            # 分析订单状态
            can_ship, reason, order_status = self._analyze_can_ship(status_nodes)
            
            return {
                'success': True,
                'can_ship': can_ship,
                'reason': reason,
                'order_status': order_status
            }
            
        except Exception as e:
            logger.error(f"检查订单 {order_id} 是否可发货失败: {e}")
            return {
                'success': False,
                'can_ship': False,
                'reason': f'检查失败: {str(e)}',
                'order_status': '未知'
            }
    
    async def check_can_rate(self, order_id: str) -> Dict:
        """检查订单是否可以评价
        
        判断逻辑：
        - 交易成功 + 待评价状态 → 可以评价
        
        Args:
            order_id: 订单号
            
        Returns:
            {
                'success': bool,  # 请求是否成功
                'can_rate': bool,  # 是否可以评价
                'reason': str,  # 原因说明
                'order_status': str  # 当前订单状态描述
            }
        """
        try:
            # 获取原始API响应
            raw_response = await self._fetch_raw_order_detail(order_id)
            if not raw_response:
                return {
                    'success': False,
                    'can_rate': False,
                    'reason': '无法获取订单状态信息',
                    'order_status': '未知'
                }
            
            # 解析订单状态节点
            status_nodes = self._extract_order_status_nodes(raw_response)
            
            # 如果状态节点为空，尝试从 orderStatusInfo 获取状态
            if not status_nodes:
                order_status_title = self._extract_order_status_title(raw_response)
                if order_status_title:
                    if '交易关闭' in order_status_title:
                        await self._update_order_status_to_cancelled(order_id)
                        return {
                            'success': True,
                            'can_rate': False,
                            'reason': '订单已关闭',
                            'order_status': order_status_title
                        }
                    elif '交易成功' in order_status_title:
                        return {
                            'success': True,
                            'can_rate': False,
                            'reason': '订单已交易成功，但无法确定是否可评价',
                            'order_status': order_status_title
                        }
                
                return {
                    'success': False,
                    'can_rate': False,
                    'reason': '订单状态节点解析失败',
                    'order_status': '未知'
                }
            
            # 分析订单状态
            can_rate, reason, order_status = self._analyze_can_rate(status_nodes)
            
            return {
                'success': True,
                'can_rate': can_rate,
                'reason': reason,
                'order_status': order_status
            }
            
        except Exception as e:
            logger.error(f"检查订单 {order_id} 是否可评价失败: {e}")
            return {
                'success': False,
                'can_rate': False,
                'reason': f'检查失败: {str(e)}',
                'order_status': '未知'
            }
    
    async def _fetch_raw_order_detail(self, order_id: str, is_retry: bool = False) -> Optional[Dict]:
        """获取订单详情的原始API响应
        
        支持令牌过期自动刷新Cookie并重试一次
        
        Args:
            order_id: 订单号
            is_retry: 是否为令牌过期后的重试请求
            
        Returns:
            原始API响应JSON，失败返回None
        """
        try:
            import json
            import time
            import aiohttp
            from common.utils.xianyu_utils import trans_cookies, generate_sign
            from common.utils.cookie_refresh import (
                is_token_expired_error, handle_token_expired_response,
                update_account_cookies_in_db,
                is_session_expired_error, trigger_password_login_async,
                mark_account_session_expired
            )
            
            cookies = trans_cookies(self.cookies_str)
            timestamp = str(int(time.time() * 1000))
            data_val = json.dumps({"tid": order_id}, separators=(',', ':'))
            
            token = cookies.get('_m_h5_tk', '').split('_')[0] if cookies.get('_m_h5_tk') else ''
            sign = generate_sign(timestamp, token, data_val)
            
            params = {
                'jsv': '2.7.2',
                'appKey': '34839810',
                't': timestamp,
                'sign': sign,
                'v': '1.0',
                'type': 'originaljson',
                'accountSite': 'xianyu',
                'dataType': 'json',
                'timeout': '20000',
                'api': 'mtop.idle.web.trade.order.detail',
                'sessionOption': 'AutoLoginOnly',
                'spm_cnt': 'a21ybx.order-detail.0.0',
            }
            
            headers = {
                'accept': 'application/json',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.goofish.com',
                'referer': 'https://www.goofish.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36',
                'cookie': self.cookies_str,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://h5api.m.goofish.com/h5/mtop.idle.web.trade.order.detail/1.0/',
                    params=params,
                    data={'data': data_val},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    res_json = await response.json()
                    
                    ret_list = res_json.get('ret', [])
                    retry_tag = '[令牌过期重试] ' if is_retry else ''
                    
                    if not any('SUCCESS' in ret for ret in ret_list):
                        # 检测令牌过期，尝试刷新Cookie并重试
                        if not is_retry and is_token_expired_error(ret_list):
                            logger.warning(
                                f"账号 {self.account_id or '未知账号'} 订单 {order_id} 查询详情令牌过期，"
                                f"接口返回: ret={ret_list}，准备刷新Cookie后重试"
                            )
                            has_new, new_cookies_str = handle_token_expired_response(
                                response, self.cookies_str
                            )
                            if has_new:
                                # 更新数据库
                                if self.account_id:
                                    await update_account_cookies_in_db(self.account_id, new_cookies_str)
                                # 更新本地Cookie并重试
                                self.cookies_str = new_cookies_str
                                return await self._fetch_raw_order_detail(order_id, is_retry=True)
                            else:
                                logger.warning(f"账号 {self.account_id or '未知账号'} 订单 {order_id} 查询详情令牌过期，但响应中没有Set-Cookie，无法重试")
                        
                        # 检测Session过期，标记账号冷却并触发后台异步密码登录（不阻塞、不重试）
                        if is_session_expired_error(ret_list):
                            logger.warning(
                                f"账号 {self.account_id or '未知账号'} 订单 {order_id} 查询详情Session过期，"
                                f"接口返回: ret={ret_list}，触发后台异步密码登录"
                            )
                            if self.account_id:
                                mark_account_session_expired(self.account_id)
                                trigger_password_login_async(self.account_id)
                        
                        logger.warning(
                            f"账号 {self.account_id or '未知账号'} {retry_tag}订单 {order_id} 查询详情API失败: "
                            f"ret={ret_list}, response={res_json}"
                        )
                        return None
                    
                    # 成功时也打印返回值摘要
                    logger.info(f"账号 {self.account_id or '未知账号'} {retry_tag}订单 {order_id} 查询详情API成功: ret={ret_list}")
                    return res_json
                    
        except Exception as e:
            logger.error(f"账号 {self.account_id or '未知账号'} 获取订单 {order_id} 原始详情失败: {e}")
            return None
    
    def _extract_order_status_nodes(self, raw_response: Dict) -> Optional[list]:
        """从原始API响应中提取订单状态节点列表
        
        Args:
            raw_response: 原始API响应
            
        Returns:
            订单状态节点列表
        """
        try:
            data = raw_response.get('data', {})
            components = data.get('components', [])
            
            for component in components:
                render_type = component.get('render', '')
                if render_type == 'orderStatusVO':
                    comp_data = component.get('data', {})
                    status_nodes = comp_data.get('orderStatusNodeList', [])
                    if status_nodes:
                        return status_nodes
                    else:
                        logger.debug(f"orderStatusNodeList 为空，将尝试从 orderStatusInfo.title 获取状态")
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"提取订单状态节点异常: {e}")
            return None
    
    def _extract_order_status_title(self, raw_response: Dict) -> Optional[str]:
        """从原始API响应中提取订单状态标题
        
        Args:
            raw_response: 原始API响应
            
        Returns:
            订单状态标题
        """
        try:
            data = raw_response.get('data', {})
            components = data.get('components', [])
            
            for component in components:
                render_type = component.get('render', '')
                if render_type == 'orderStatusVO':
                    comp_data = component.get('data', {})
                    order_status_info = comp_data.get('orderStatusInfo', {})
                    title = order_status_info.get('title', '')
                    if title:
                        logger.info(f"从 orderStatusInfo 提取到状态标题: {title}")
                        return title
            
            return None
            
        except Exception as e:
            logger.error(f"提取订单状态标题异常: {e}")
            return None
    
    async def _update_order_status_to_cancelled(self, order_id: str) -> None:
        """更新订单状态为已关闭
        
        Args:
            order_id: 订单号
        """
        try:
            from common.db.session import async_session_maker
            
            async with async_session_maker() as session:
                stmt = update(XYOrder).where(XYOrder.order_no == order_id).values(status="cancelled")
                await session.execute(stmt)
                await session.commit()
                logger.info(f"订单 {order_id} 状态已更新为 cancelled（交易关闭）")
        except Exception as e:
            logger.error(f"更新订单 {order_id} 状态失败: {e}")
    
    def _analyze_can_ship(self, status_nodes: list) -> tuple:
        """分析订单状态节点，判断是否可以发货
        
        可发货条件：
        1. 普通订单：已付款(completed=True) + 待发货(completed=False)
        2. 小刀订单：已付款(completed=True) + 已刀成/待发货(任意状态) + 待收货(completed=False)
        
        Args:
            status_nodes: 订单状态节点列表
            
        Returns:
            (can_ship: bool, reason: str, order_status: str)
        """
        # 构建状态映射
        status_map = {}
        for node in status_nodes:
            title = node.get('title', '')
            completed = node.get('completed', False)
            status_map[title] = completed
        
        # 获取当前订单状态描述
        current_status_parts = []
        for node in status_nodes:
            title = node.get('title', '')
            completed = node.get('completed', False)
            if completed:
                current_status_parts.append(title)
        order_status = ' → '.join(current_status_parts) if current_status_parts else '未知'
        
        # 检查是否已付款
        is_paid = status_map.get('已付款', False)
        if not is_paid:
            return False, '订单未付款', order_status
        
        # 检查是否已发货
        is_shipped = status_map.get('已发货', False)
        if is_shipped:
            return False, '订单已发货', order_status
        
        # 检查是否交易成功/已完成
        is_success = status_map.get('交易成功', False)
        if is_success:
            return False, '订单已交易成功', order_status
        
        # 检查是否待发货状态
        has_pending_ship = '待发货' in status_map
        has_bargain_done = '已刀成' in status_map  # 小刀订单特有状态
        has_bargain_pending = '待刀成' in status_map  # 小刀订单等待刀成
        
        if has_bargain_pending and not status_map.get('待刀成', False):
            # 小刀订单还在等待刀成
            return False, '小刀订单等待刀成', order_status
        
        if has_pending_ship or has_bargain_done:
            # 已付款且处于待发货状态
            return True, '订单已付款，可以发货', order_status
        
        return False, '订单状态不满足发货条件', order_status
    
    def _analyze_can_rate(self, status_nodes: list) -> tuple:
        """分析订单状态节点，判断是否可以评价
        
        可评价条件：
        - 交易成功(completed=True) + 待评价(completed=False)
        
        Args:
            status_nodes: 订单状态节点列表
            
        Returns:
            (can_rate: bool, reason: str, order_status: str)
        """
        # 构建状态映射
        status_map = {}
        for node in status_nodes:
            title = node.get('title', '')
            completed = node.get('completed', False)
            status_map[title] = completed
        
        # 获取当前订单状态描述
        current_status_parts = []
        for node in status_nodes:
            title = node.get('title', '')
            completed = node.get('completed', False)
            if completed:
                current_status_parts.append(title)
        order_status = ' → '.join(current_status_parts) if current_status_parts else '未知'
        
        # 检查是否交易成功
        is_success = status_map.get('交易成功', False)
        if not is_success:
            return False, '订单未交易成功', order_status
        
        # 检查是否已评价
        is_rated = status_map.get('已评价', False)
        if is_rated:
            return False, '订单已评价', order_status
        
        # 检查是否待评价状态
        has_pending_rate = '待评价' in status_map
        is_pending_rate_completed = status_map.get('待评价', False)
        
        if has_pending_rate and not is_pending_rate_completed:
            # 交易成功且处于待评价状态
            return True, '订单已交易成功，可以评价', order_status
        
        return False, '订单状态不满足评价条件', order_status


# 便捷函数
async def check_can_ship(order_id: str, cookie_string: str, account_id: str = None) -> Dict:
    """检查订单是否可以发货（便捷函数）
    
    Args:
        order_id: 订单号
        cookie_string: Cookie字符串
        account_id: 账号ID，用于令牌过期时更新数据库Cookie（可选）
        
    Returns:
        检查结果字典
    """
    checker = OrderStatusChecker(cookie_string, account_id)
    result = await checker.check_can_ship(order_id)
    # 将更新后的cookies字符串附加到结果中，方便调用方同步
    result['cookies_str'] = checker.cookies_str
    return result


async def check_can_rate(order_id: str, cookie_string: str, account_id: str = None) -> Dict:
    """检查订单是否可以评价（便捷函数）
    
    Args:
        order_id: 订单号
        cookie_string: Cookie字符串
        account_id: 账号ID，用于令牌过期时更新数据库Cookie（可选）
        
    Returns:
        检查结果字典
    """
    checker = OrderStatusChecker(cookie_string, account_id)
    result = await checker.check_can_rate(order_id)
    # 将更新后的cookies字符串附加到结果中，方便调用方同步
    result['cookies_str'] = checker.cookies_str
    return result
