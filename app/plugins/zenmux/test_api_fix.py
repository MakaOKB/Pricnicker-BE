#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API字段修复 - 简化版本
"""

import json
import requests
import logging
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleZenmuxTest:
    """简化的ZenMux测试类"""
    
    API_URL = "https://zenmux.ai/api/frontend/model/listByFilter"
    DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    def _get_models_from_api(self) -> Optional[List[Dict]]:
        """从API获取模型数据"""
        try:
            logger.info("正在调用ZenMux API...")
            response = requests.get(
                self.API_URL,
                timeout=30,
                headers={
                    'User-Agent': self.DEFAULT_USER_AGENT,
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Referer': 'https://zenmux.ai/models'
                }
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # 检查响应格式
                if isinstance(response_data, dict) and 'success' in response_data and 'data' in response_data:
                    if response_data.get('success'):
                        data = response_data['data']
                        logger.info(f"✅ API调用成功，获取到 {len(data)} 个模型")
                        return data
                    else:
                        logger.error(f"API返回失败状态: {response_data}")
                        return None
                else:
                    # 兼容直接返回数组的情况
                    if isinstance(response_data, list):
                        logger.info(f"✅ API调用成功，获取到 {len(response_data)} 个模型")
                        return response_data
                    else:
                        logger.error(f"API返回格式异常: {type(response_data)}")
                        return None
            else:
                logger.error(f"API请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            return None
    
    def test_price_parsing(self):
        """测试价格解析"""
        models = self._get_models_from_api()
        if not models:
            return False
        
        logger.info("\n=== 价格字段测试 ===")
        
        # 检查前3个模型的价格字段
        for i, model in enumerate(models[:3]):
            logger.info(f"\n模型 {i+1}: {model.get('name', 'Unknown')}")
            logger.info(f"  pricing_prompt: {model.get('pricing_prompt')}")
            logger.info(f"  pricing_completion: {model.get('pricing_completion')}")
            
            # 测试价格解析
            try:
                input_price = float(model.get('pricing_prompt', 0.0))
                output_price = float(model.get('pricing_completion', 0.0))
                logger.info(f"  解析后价格: 输入=${input_price}, 输出=${output_price} USD")
            except (ValueError, TypeError) as e:
                logger.error(f"  价格解析失败: {e}")
                return False
        
        return True

def main():
    """主函数"""
    print("🚀 测试ZenMux API字段修复...")
    
    tester = SimpleZenmuxTest()
    success = tester.test_price_parsing()
    
    if success:
        print("\n✅ API字段测试成功！pricing_prompt和pricing_completion字段解析正常")
    else:
        print("\n❌ API字段测试失败")
    
    return success

if __name__ == "__main__":
    main()