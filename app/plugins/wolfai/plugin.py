#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WolfAI 模型价格爬虫插件

该插件从 WolfAI 获取AI模型的价格信息。
使用 API 端点: https://wolfai.top/api/pricing

功能特性:
- 通过 API 接口获取实时模型数据
- 支持多种 AI 模型品牌（OpenAI、Anthropic、Google、DeepSeek 等）
- 自动解析价格、上下文窗口等信息
- 符合 editv3.json 接口规范
- 包含配置验证和错误处理

作者: PricNicker Team
版本: 1.0.0
最后更新: 2025-01-13
"""

import json
import logging
import re
import requests
from typing import Dict, List, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError
from ..base import BasePlugin, PluginConfig
from ...models import ModelInfo, TokenInfo, ProviderInfo

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wolfai_plugin.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class WolfaiPlugin(BasePlugin):
    """
    WolfAI 价格爬虫插件
    
    从 WolfAI 获取AI模型的价格信息，支持多种AI模型品牌。
    
    主要功能:
    - 通过 API 接口获取实时模型数据
    - 解析模型价格、上下文窗口等信息
    - 提供品牌列表和模型查询功能
    - 数据格式符合 editv3.json 规范
    
    支持的品牌:
    - OpenAI (GPT 系列)
    - Anthropic (Claude 系列)
    - Google (Gemini 系列)
    - DeepSeek
    - Qwen
    - GLM
    - 其他主流 AI 模型
    
    Attributes:
        api_url (str): WolfAI 定价 API URL
        base_url (str): WolfAI 基础 URL
        session (requests.Session): HTTP 会话对象
        config (dict): 插件配置参数
    """
    
    def __init__(self, config: PluginConfig = None):
        """初始化插件"""
        super().__init__(config)
        self.api_url = "https://wolfai.top/api/pricing"
        self.base_url = "https://wolfai.top"
        self.session = requests.Session()
        self.plugin_config = {
            'timeout': 30,
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': self.plugin_config['user_agent'],
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://wolfai.top/',
            'Origin': 'https://wolfai.top'
        })
        
        logger.info("WolfAI插件初始化完成")
    
    async def validate_config(self) -> bool:
        """
        验证插件配置
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 验证API URL是否可访问
            response = self.session.get(self.api_url, timeout=self.plugin_config['timeout'])
            if response.status_code == 200:
                logger.info("WolfAI插件配置验证通过")
                return True
            else:
                logger.error(f"WolfAI API访问失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"WolfAI插件配置验证失败: {str(e)}")
            return False
    
    def _extract_brand_from_model_name(self, model_name: str) -> str:
        """
        从模型名称中提取品牌信息
        
        Args:
            model_name (str): 模型名称
            
        Returns:
            str: 品牌名称
        """
        # 品牌映射表
        brand_mapping = {
            'gpt': 'OpenAI',
            'claude': 'Anthropic',
            'gemini': 'Google',
            'deepseek': 'DeepSeek',
            'qwen': 'Qwen',
            'glm': 'GLM',
            'llama': 'Meta',
            'grok': 'xAI',
            'o1': 'OpenAI',
            'o3': 'OpenAI',
            'o4': 'OpenAI',
            'dall-e': 'OpenAI',
            'text-embedding': 'OpenAI',
            'tts': 'OpenAI',
            'whisper': 'OpenAI',
            'mj': 'Midjourney',
            'qwq': 'Qwen'
        }
        
        model_lower = model_name.lower()
        for key, brand in brand_mapping.items():
            if key in model_lower:
                return brand
        
        return 'Unknown'
    
    def _extract_context_window(self, model_name: str, tags: str = "") -> int:
        """
        从模型名称或标签中提取上下文窗口大小
        
        Args:
            model_name (str): 模型名称
            tags (str): 模型标签
            
        Returns:
            int: 上下文窗口大小（token数）
        """
        # 合并模型名称和标签进行匹配
        text = f"{model_name} {tags}".lower()
        
        # 匹配各种上下文窗口格式
        patterns = [
            r'(\d+)m',  # 1M, 2M 等
            r'(\d+)k',  # 128K, 200K 等
            r'(\d+\.\d+)k',  # 16.4K 等
            r'(\d+)万',  # 中文万
            r'context[_\s]*(\d+)',  # context_128k
            r'ctx[_\s]*(\d+)',  # ctx_128k
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    value = float(matches[0])
                    if 'm' in text:
                        return int(value * 1000000)  # M -> tokens
                    elif 'k' in text:
                        return int(value * 1000)  # K -> tokens
                    elif '万' in text:
                        return int(value * 10000)  # 万 -> tokens
                    else:
                        return int(value)
                except ValueError:
                    continue
        
        # 默认值
        return 4096
    
    def _parse_pricing_data(self, data: Dict) -> List[ModelInfo]:
        """
        解析WolfAI API返回的定价数据
        
        Args:
            data (Dict): API返回的原始数据
            
        Returns:
            List[ModelInfo]: 解析后的模型信息列表
        """
        models = []
        
        try:
            # WolfAI API 返回的数据结构
            model_list = data.get('data', [])
            
            logger.info(f"开始解析WolfAI模型数据，共{len(model_list)}个模型")
            
            for model_data in model_list:
                try:
                    model_name = model_data.get('model_name', '')
                    if not model_name:
                        continue
                    
                    # 提取基本信息
                    description = model_data.get('description', '')
                    tags = model_data.get('tags', '')
                    icon = model_data.get('icon', '')
                    
                    # 提取品牌信息
                    brand = self._extract_brand_from_model_name(model_name)
                    
                    # 提取上下文窗口
                    context_window = self._extract_context_window(model_name, tags)
                    
                    # 解析价格信息
                    model_ratio = model_data.get('model_ratio', 0)
                    completion_ratio = model_data.get('completion_ratio', 0)
                    model_price = model_data.get('model_price', 0)
                    quota_type = model_data.get('quota_type', 0)
                    
                    # 计算价格（根据WolfAI的定价逻辑）
                    if quota_type == 0:  # 按比例计费
                        # 使用 model_ratio 和 completion_ratio 计算价格
                        input_price = model_ratio / 1000000 if model_ratio > 0 else 0.000001
                        output_price = completion_ratio / 1000000 if completion_ratio > 0 else 0.000001
                    else:  # 固定价格
                        # 使用 model_price
                        input_price = model_price if model_price > 0 else 0.000001
                        output_price = model_price if model_price > 0 else 0.000001
                    
                    # 创建TokenInfo对象
                    token_info = TokenInfo(
                        input_price=input_price,
                        output_price=output_price,
                        currency="USD",
                        unit="1K tokens"
                    )
                    
                    # 创建ProviderInfo对象
                    provider_info = ProviderInfo(
                        name="wolfai",
                        display_name="WolfAI",
                        api_website="https://wolfai.top",
                        full_name=f"wolfai/{model_name.lower().replace(' ', '-')}",
                        tokens=token_info
                    )
                    
                    # 创建ModelInfo对象
                    model_info = ModelInfo(
                        name=model_name,
                        display_name=model_name,
                        description=description,
                        context_window=context_window,
                        token_info=token_info,
                        provider_info=provider_info,
                        tags=tags.split(',') if tags else [],
                        capabilities=[],
                        extra_info={
                            'vendor_id': model_data.get('vendor_id'),
                            'quota_type': quota_type,
                            'model_ratio': model_ratio,
                            'completion_ratio': completion_ratio,
                            'model_price': model_price,
                            'icon': icon,
                            'enable_groups': model_data.get('enable_groups', []),
                            'supported_endpoint_types': model_data.get('supported_endpoint_types', [])
                        }
                    )
                    
                    models.append(model_info)
                    
                except Exception as e:
                    logger.warning(f"解析模型 {model_data.get('model_name', 'unknown')} 时出错: {str(e)}")
                    continue
            
            logger.info(f"成功解析{len(models)}个模型")
            
            # 显示前5个模型的信息
            for i, model in enumerate(models[:5]):
                logger.info(f"模型{i+1}: {model.name}, 输入价格: ${model.token_info.input_price:.6f}/USD, 输出价格: ${model.token_info.output_price:.6f}/USD")
            
            return models
            
        except Exception as e:
            logger.error(f"解析WolfAI定价数据时出错: {str(e)}")
            return []
    
    async def get_models(self) -> List[ModelInfo]:
        """
        获取WolfAI的模型列表
        
        Returns:
            List[ModelInfo]: 模型信息列表
            
        Raises:
            Exception: 当获取模型信息失败时抛出异常
        """
        try:
            logger.info("开始请求WolfAI API获取模型数据")
            
            response = self.session.get(
                self.api_url,
                timeout=self.plugin_config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("成功获取WolfAI API数据")
                return self._parse_pricing_data(data)
            else:
                logger.error(f"WolfAI API请求失败，状态码: {response.status_code}")
                raise Exception(f"API请求失败: {response.status_code}")
                
        except RequestException as e:
            logger.error(f"WolfAI API请求异常: {str(e)}")
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取WolfAI模型数据时出错: {str(e)}")
            raise
    
    async def get_model_pricing(self, model_name: str) -> Optional[Dict]:
        """
        获取特定模型的价格信息
        
        Args:
            model_name (str): 模型名称
            
        Returns:
            Optional[Dict]: 模型价格信息，如果未找到则返回None
        """
        try:
            models = await self.get_models()
            for model in models:
                if model.name == model_name:
                    return {
                        'model_name': model.name,
                        'input_price': model.token_info.input_price,
                        'output_price': model.token_info.output_price,
                        'currency': model.token_info.currency,
                        'unit': model.token_info.unit,
                        'context_window': model.context_window,
                        'provider': model.provider_info.name,
                        'brand': model.provider_info.brand
                    }
            return None
        except Exception as e:
            logger.error(f"获取模型 {model_name} 价格信息时出错: {str(e)}")
            return None
    
    def get_brands(self) -> List[str]:
        """
        获取支持的品牌列表
        
        Returns:
            List[str]: 品牌名称列表
        """
        return ['OpenAI', 'Anthropic', 'Google', 'DeepSeek', 'Qwen', 'GLM', 'Meta', 'xAI', 'Midjourney', 'Unknown']
    
    def get_plugin_info(self) -> Dict:
        """
        获取插件信息
        
        Returns:
            Dict: 插件信息字典
        """
        return {
            'name': 'wolfai',
            'version': '1.0.0',
            'description': 'WolfAI模型价格爬虫插件',
            'author': 'PricNicker Team',
            'brand_name': 'WolfAI',
            'api_url': self.api_url,
            'supported_brands': self.get_brands()
        }

if __name__ == "__main__":
    # 测试代码
    import asyncio
    from dataclasses import dataclass

    @dataclass
    class TestPluginConfig:
        name: str = "wolfai"
        version: str = "1.0.0"
        description: str = "WolfAI模型价格爬虫插件"
        author: str = "PricNicker Team"
        brand_name: str = "WolfAI"
        enabled: bool = True

    async def test_plugin():
        """测试插件功能"""
        config = TestPluginConfig()
        plugin = WolfaiPlugin(config)
        
        # 测试配置验证
        print("测试配置验证...")
        is_valid = await plugin.validate_config()
        print(f"配置验证结果: {is_valid}")
        
        if is_valid:
            # 测试获取模型列表
            print("\n测试获取模型列表...")
            models = await plugin.get_models()
            print(f"获取到 {len(models)} 个模型")
            
            # 显示前几个模型的信息
            for i, model in enumerate(models[:3]):
                print(f"模型 {i+1}: {model.name}")
                print(f"  品牌: {model.provider_info.brand}")
                print(f"  输入价格: ${model.token_info.input_price:.6f}")
                print(f"  输出价格: ${model.token_info.output_price:.6f}")
                print(f"  上下文窗口: {model.context_window}")
                print()
            
            # 测试获取品牌列表
            print("支持的品牌:")
            brands = plugin.get_brands()
            print(f"{', '.join(brands)}")
            
            # 测试插件信息
            print("\n插件信息:")
            info = plugin.get_plugin_info()
            for key, value in info.items():
                print(f"{key}: {value}")

    asyncio.run(test_plugin())