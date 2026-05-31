"""订单详情服务 - 获取和更新订单详情信息"""
from __future__ import annotations

from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from common.models.xy_order import XYOrder

class OrderDetailService:
    """订单详情服务 - 用于异步获取和更新订单详情信息
    
    功能：
    1. 通过API获取订单详情（规格、数量、收货人等）
    2. 更新订单信息到数据库
    """
    
    def __init__(self, cookie_id: str, cookies_str: str):
        """初始化订单详情服务
        
        Args:
            cookie_id: 账号ID
            cookies_str: Cookie字符串
        """
        self.cookie_id = cookie_id
        # 清洗 cookies_str 中的换行符，防止 header injection
        self.cookies_str = (cookies_str or "").replace("\r", "").replace("\n", "")
    
    async def fetch_and_update_order_detail(
        self,
        order_id: str,
        item_id: str = None,
        buyer_id: str = None
    ) -> bool:
        """获取订单详情并更新到数据库
        
        Args:
            order_id: 订单ID
            item_id: 商品ID（可选，用于更新）
            buyer_id: 买家ID（可选，用于更新）
            
        Returns:
            是否成功
        """
        try:
            from datetime import datetime
            from common.db.session import async_session_maker
            
            # 获取订单详情
            detail = await self._fetch_order_detail(order_id)
            api_failed = detail is None
            
            async with async_session_maker() as session:
                # 查询现有订单
                stmt = select(XYOrder).where(XYOrder.order_no == order_id)
                result = await session.execute(stmt)
                existing_order = result.scalars().first()
                
                if not existing_order:
                    logger.warning(f"【{self.cookie_id}】订单 {order_id} 不存在，无法更新")
                    return False
                
                # 构建更新字段
                update_values = {}
                
                # 更新item_id和buyer_id（如果数据库中为空）
                if item_id and not existing_order.item_id:
                    update_values['item_id'] = item_id
                if buyer_id and not existing_order.buyer_id:
                    update_values['buyer_id'] = buyer_id
                
                # 从API详情中补充item_id和buyer_id（如果参数未传入且数据库中为空）
                if detail:
                    if detail.get('item_id') and not existing_order.item_id and 'item_id' not in update_values:
                        update_values['item_id'] = detail['item_id']
                    if detail.get('buyer_id') and not existing_order.buyer_id and 'buyer_id' not in update_values:
                        update_values['buyer_id'] = detail['buyer_id']
                    # 从API状态节点中检测小刀订单
                    if detail.get('is_bargain') and not existing_order.is_bargain:
                        update_values['is_bargain'] = True
                
                # 更新从API获取的详情
                if detail:
                    if detail.get('spec_name'):
                        update_values['spec_name'] = detail['spec_name']
                    if detail.get('spec_value'):
                        update_values['spec_value'] = detail['spec_value']
                    if detail.get('amount'):
                        update_values['amount'] = detail['amount']
                    if detail.get('quantity'):
                        update_values['quantity'] = detail['quantity']
                    
                    # 下单时间：如果API返回了时间且数据库中为空，则更新
                    placed_at_str = detail.get('placed_at_str', '')
                    if placed_at_str and not existing_order.placed_at:
                        try:
                            placed_at = datetime.strptime(placed_at_str, '%Y-%m-%d %H:%M:%S')
                            update_values['placed_at'] = placed_at
                        except ValueError:
                            logger.warning(f"【{self.cookie_id}】订单 {order_id} 下单时间格式不匹配: {placed_at_str}")
                    
                    # 收货人信息：如果新获取的不为空，且（数据库为空 或 数据库中包含脱敏字符*），则更新
                    if self._should_update_receiver_field(detail.get('receiver_name', ''), existing_order.receiver_name):
                        update_values['receiver_name'] = detail['receiver_name']
                    if self._should_update_receiver_field(detail.get('receiver_phone', ''), existing_order.receiver_phone):
                        update_values['receiver_phone'] = detail['receiver_phone']
                    if self._should_update_receiver_field(detail.get('receiver_address', ''), existing_order.receiver_address):
                        update_values['receiver_address'] = detail['receiver_address']
                
                if update_values:
                    stmt = update(XYOrder).where(XYOrder.order_no == order_id).values(**update_values)
                    await session.execute(stmt)
                    await session.commit()
                    if api_failed:
                        logger.warning(f"【{self.cookie_id}】订单 {order_id} API获取详情失败，仅通过参数更新了: {list(update_values.keys())}")
                    else:
                        logger.info(f"【{self.cookie_id}】订单 {order_id} 信息已更新: {list(update_values.keys())}")
                    return True
                else:
                    if api_failed:
                        logger.warning(f"【{self.cookie_id}】订单 {order_id} API获取详情失败，且无可更新字段（请查看上方API调用失败日志）")
                        return False
                    logger.info(f"【{self.cookie_id}】订单 {order_id} 无需更新")
                    return True
                    
        except Exception as e:
            logger.error(f"【{self.cookie_id}】获取并更新订单详情失败: {e}")
            return False
    
    def _should_update_receiver_field(self, new_value: str, old_value: str) -> bool:
        """判断是否需要更新收货人字段
        
        Args:
            new_value: 新值
            old_value: 旧值
            
        Returns:
            是否需要更新
        """
        if not new_value:
            return False
        if not old_value:
            return True
        # 如果旧值包含脱敏字符，且新值不包含，则更新
        if '*' in old_value and '*' not in new_value:
            return True
        return False
    
    async def _fetch_order_detail(self, order_id: str, retry_count: int = 0) -> Optional[Dict]:
        """通过API获取订单详情
        
        参照发货服务的模式：每次请求后存储set-cookie，令牌过期时用新cookie重试
        
        Args:
            order_id: 订单ID
            retry_count: 当前重试次数
            
        Returns:
            订单详情字典，包含spec_name, spec_value, amount, quantity, receiver_name等
        """
        max_retry = 3
        
        try:
            import json
            import time
            import aiohttp
            from common.utils.xianyu_utils import trans_cookies, generate_sign
            
            cookies = trans_cookies(self.cookies_str)
            timestamp = str(int(time.time() * 1000))
            data_val = json.dumps({"tid": order_id}, separators=(',', ':'))
            
            # 从Cookie中获取token用于签名
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
                    
                    # 处理响应中的set-cookie，更新本地cookie并写入数据库
                    await self._handle_response_cookies(response)
                    
                    # 打印API返回结果用于分析
                    logger.info(f"【{self.cookie_id}】订单 {order_id} API返回: ret={res_json.get('ret', [])}")
                    
                    # 检查响应是否成功
                    ret_list = res_json.get('ret', [])
                    if not any('SUCCESS' in ret for ret in ret_list):
                        # 打印详细的失败原因
                        ret_str = ', '.join(ret_list) if ret_list else '无返回信息'
                        logger.warning(f"【{self.cookie_id}】订单 {order_id} API调用失败: {ret_str}")
                        
                        # 令牌过期时，用更新后的cookie重试
                        from common.utils.cookie_refresh import is_token_expired_error
                        if is_token_expired_error(ret_list):
                            if retry_count < max_retry - 1:
                                logger.info(f"【{self.cookie_id}】订单 {order_id} 令牌过期，已更新Cookie，准备重试({retry_count + 1}/{max_retry - 1})...")
                                await asyncio.sleep(0.5)
                                return await self._fetch_order_detail(order_id, retry_count + 1)
                        
                        return None
                    
                    # 解析返回数据
                    return self._parse_order_detail_response(order_id, res_json)
                    
        except Exception as e:
            logger.error(f"【{self.cookie_id}】获取订单详情异常: {type(e).__name__}: {e}")
            if retry_count < max_retry - 1:
                await asyncio.sleep(0.5)
                return await self._fetch_order_detail(order_id, retry_count + 1)
            return None
    
    async def _handle_response_cookies(self, response) -> None:
        """处理响应中的set-cookie，更新本地cookie并写入数据库
        
        令牌过期时服务端会在响应头中返回新的cookie（包含新的_m_h5_tk），
        存储后重试请求即可使用新的token签名
        
        Args:
            response: HTTP响应对象
        """
        try:
            from common.utils.cookie_refresh import (
                extract_cookies_from_response, merge_cookies,
                update_account_cookies_in_db
            )
            
            new_cookies = extract_cookies_from_response(response)
            if new_cookies:
                self.cookies_str = merge_cookies(self.cookies_str, new_cookies)
                # 写入数据库
                await update_account_cookies_in_db(self.cookie_id, self.cookies_str)
                logger.info(
                    f"【{self.cookie_id}】已从响应中合并 {len(new_cookies)} 个Cookie字段并更新到数据库"
                )
        except Exception as e:
            logger.warning(f"【{self.cookie_id}】处理响应Cookie失败: {e}")
    
    def _parse_order_detail_response(self, order_id: str, res_json: dict) -> Optional[Dict]:
        """解析API返回的订单详情数据
        
        Args:
            order_id: 订单号
            res_json: API返回的JSON数据
            
        Returns:
            解析后的订单详情字典
        """
        try:
            data = res_json.get('data', {})
            components = data.get('components', [])
            
            result = {
                'item_id': '',
                'buyer_id': '',
                'spec_name': '',
                'spec_value': '',
                'quantity': '1',
                'amount': '',
                'receiver_name': '',
                'receiver_phone': '',
                'receiver_address': '',
                'is_bargain': False,
            }
            
            # 从顶层data中提取buyer_id和item_id（作为兜底）
            top_peer_user_id = data.get('peerUserId', '')
            top_item_id = data.get('itemId', '')
            if top_peer_user_id:
                result['buyer_id'] = str(top_peer_user_id)
            if top_item_id:
                result['item_id'] = str(top_item_id)
            
            for component in components:
                render_type = component.get('render', '')
                comp_data = component.get('data', {})
                
                # 解析订单信息（包含商品信息）
                if render_type == 'orderInfoVO':
                    logger.info(f"【{self.cookie_id}】订单 {order_id} orderInfoVO keys: {list(comp_data.keys())}")
                    item_info = comp_data.get('itemInfo', {})
                    logger.info(f"【{self.cookie_id}】订单 {order_id} itemInfo keys: {list(item_info.keys())}")
                    
                    # 从orderInfoList中提取下单时间
                    order_info_list = comp_data.get('orderInfoList', [])
                    if order_info_list:
                        logger.info(f"【{self.cookie_id}】订单 {order_id} orderInfoList: {order_info_list}")
                        for info_item in order_info_list:
                            label = info_item.get('label', '') or info_item.get('key', '') or info_item.get('name', '')
                            value = info_item.get('value', '') or info_item.get('text', '')
                            if '时间' in label or 'time' in label.lower() or 'Time' in label:
                                result['placed_at_str'] = value
                                logger.info(f"【{self.cookie_id}】订单 {order_id} 提取到下单时间: {value}")
                    
                    # 获取商品ID
                    api_item_id = item_info.get('itemId', '') or comp_data.get('itemId', '')
                    if api_item_id:
                        result['item_id'] = str(api_item_id)
                    
                    # 获取买家ID
                    api_buyer_id = comp_data.get('buyerUserId', '') or comp_data.get('buyerId', '')
                    if api_buyer_id:
                        result['buyer_id'] = str(api_buyer_id)
                    
                    # 获取数量
                    buy_amount = item_info.get('buyAmount', '1')
                    result['quantity'] = str(buy_amount)
                    
                    # 获取价格
                    price = item_info.get('price', '')
                    if price:
                        result['amount'] = str(price)
                    
                    # 获取规格信息（格式：规格名:规格值）
                    sku_info = item_info.get('skuInfo', '')
                    if sku_info and ':' in sku_info:
                        parts = sku_info.split(':', 1)
                        result['spec_name'] = parts[0].strip()
                        result['spec_value'] = parts[1].strip() if len(parts) > 1 else ''
                
                # 解析收货地址信息
                elif render_type == 'addressInfoVO':
                    result['receiver_name'] = comp_data.get('name', '')
                    result['receiver_phone'] = comp_data.get('phoneNumber', '')
                    result['receiver_address'] = comp_data.get('address', '')
                
                # 解析订单状态，检测小刀订单
                elif render_type == 'orderStatusVO':
                    status_nodes = comp_data.get('orderStatusNodeList', [])
                    for node in status_nodes:
                        node_title = node.get('title', '')
                        if node_title in ('已刀成', '待刀成'):
                            result['is_bargain'] = True
                            break
            
            logger.info(f"【{self.cookie_id}】订单 {order_id} 详情解析成功: item_id={result['item_id']}, buyer_id={result['buyer_id']}, 价格={result['amount']}, 规格={result['spec_name']}:{result['spec_value']}, 小刀={result['is_bargain']}")
            return result
            
        except Exception as e:
            logger.error(f"【{self.cookie_id}】订单 {order_id} 解析API响应失败: {e}")
            return None


