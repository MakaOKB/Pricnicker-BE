#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMXAPI 模型价格爬虫插件

该插件从 DMXAPI 获取AI模型的价格信息。
使用 API 端点: https://www.dmxapi.cn/api/pricing

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
        logging.FileHandler('dmx_plugin.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DmxPlugin(BasePlugin):
    """
    DMXAPI 价格爬虫插件
    
    从 DMXAPI 获取AI模型的价格信息，支持多种AI模型品牌。
    
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
        api_url (str): DMXAPI 定价 API URL
        base_url (str): DMXAPI 基础 URL
        session (requests.Session): HTTP 会话对象
        config (dict): 插件配置参数
    """
    
    def __init__(self, config: PluginConfig = None):
        """初始化插件"""
        super().__init__(config)
        self.api_url = "https://www.dmxapi.cn/api/pricing"
        self.base_url = "https://www.dmxapi.cn"
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
            'Referer': 'https://www.dmxapi.cn/',
            'Origin': 'https://www.dmxapi.cn'
        })
        
        logger.info("DMXAPI插件初始化完成")
    
    async def validate_config(self) -> bool:
        """
        验证插件配置
        
        Returns:
            bool: 配置是否有效
        """
        try:
            logger.info("开始验证DMXAPI插件配置...")
            
            # 测试API连接
            response = self.session.get(
                self.api_url,
                timeout=self.plugin_config['timeout']
            )
            
            if response.status_code == 200:
                logger.info("DMXAPI配置验证成功")
                return True
            else:
                logger.error(f"API响应状态码异常: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def _extract_brand_from_model_name(self, model_name: str) -> str:
        """
        从模型名称中提取品牌信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            str: 品牌名称
        """
        model_name_lower = model_name.lower()
        
        # 品牌映射规则
        brand_mapping = {
            'gpt': 'OpenAI',
            'o1': 'OpenAI', 
            'o3': 'OpenAI',
            'o4': 'OpenAI',
            'claude': 'Anthropic',
            'gemini': 'Google',
            'deepseek': 'DeepSeek',
            'qwen': 'Qwen',
            'glm': 'GLM',
            'doubao': 'Doubao',
            'ernie': 'ERNIE',
            'hunyuan': 'Hunyuan',
            'moonshot': 'Moonshot',
            'kimi': 'Moonshot',
            'abab': 'MiniMax',
            'baichuan': 'Baichuan',
            'spark': 'iFLYTEK'
        }
        
        for key, brand in brand_mapping.items():
            if key in model_name_lower:
                return brand
        
        # 如果没有匹配到，返回默认值
        return 'Unknown'
    
    def _extract_context_window(self, model_name: str) -> int:
        """
        从模型名称中提取上下文窗口大小
        
        Args:
            model_name: 模型名称
            
        Returns:
            int: 上下文窗口大小
        """
        # 常见的窗口大小模式
        patterns = [
            r'(\d+)k',  # 如 128k, 32k
            r'(\d+)K',  # 如 128K, 32K
        ]
        
        for pattern in patterns:
            match = re.search(pattern, model_name)
            if match:
                return int(match.group(1)) * 1000
        
        # 默认窗口大小映射
        model_name_lower = model_name.lower()
        if 'gpt-4' in model_name_lower:
            return 128000
        elif 'gpt-3.5' in model_name_lower:
            return 16000
        elif 'claude' in model_name_lower:
            return 200000
        elif 'gemini' in model_name_lower:
            return 128000
        elif 'deepseek' in model_name_lower:
            return 128000
        
        return 4096  # 默认值
    
    def _parse_pricing_data(self, data: Dict) -> List[ModelInfo]:
        """
        解析定价数据并转换为ModelInfo对象列表
        
        Args:
            data: API返回的原始数据
            
        Returns:
            List[ModelInfo]: 模型信息对象列表
        """
        models = []
        
        try:
            # 打印原始数据结构用于调试
            logger.info(f"原始数据结构: {list(data.keys())}")
            
            # 获取模型定价数据 - 根据实际API响应调整
            data_section = data.get('data', {})
            model_pricing = data_section.get('model_completion_ratio', {})
            
            if not model_pricing:
                logger.warning(f"未找到模型定价数据，data字段中可用的键: {list(data_section.keys())}")
                return models
            
            logger.info(f"开始解析 {len(model_pricing)} 个模型的定价数据")
            
            for model_name, pricing_info in model_pricing.items():
                try:
                    # 跳过非文本模型（如图像、音频等）
                    if any(skip_word in model_name.lower() for skip_word in 
                          ['image', 'audio', 'video', 'dall-e', 'mj_', 'kling_', 'flux']):
                        continue
                    
                    # 提取品牌信息
                    brand = self._extract_brand_from_model_name(model_name)
                    
                    # 提取上下文窗口
                    window = self._extract_context_window(model_name)
                    
                    # 解析价格信息 - pricing_info 可能是整数或字典
                    if isinstance(pricing_info, dict):
                        input_price = pricing_info.get('CompletionRatio', 0) / 1000000
                        output_price = pricing_info.get('PromptRatio', 0) / 1000000
                    elif isinstance(pricing_info, (int, float)):
                        # 调试：打印原始价格值
                        logger.debug(f"模型 {model_name} 原始价格: {pricing_info}")
                        # 如果是数字，直接使用（不除以1000000，因为API返回的可能已经是正确的价格）
                        # 根据观察到的数值范围，这些可能是以微分为单位的价格
                        if pricing_info >= 1000:  # 如果是大数值，可能需要转换
                            input_price = pricing_info / 1000000
                            output_price = pricing_info / 1000000
                        else:  # 如果是小数值，直接使用
                            input_price = float(pricing_info)
                            output_price = float(pricing_info)
                    else:
                        logger.warning(f"未知的价格信息格式: {type(pricing_info)}")
                        continue
                    
                    # 创建TokenInfo对象
                    tokens = TokenInfo(
                        input=input_price,
                        output=output_price,
                        unit='USD'  # DMXAPI使用美元计价
                    )
                    
                    # 创建ProviderInfo对象
                    provider_info = ProviderInfo(
                        name='dmx',
                        display_name='DMXAPI',
                        api_website='https://www.dmxapi.cn',
                        full_name=f'dmx/{model_name.lower().replace(" ", "-")}',
                        tokens=tokens
                    )
                    
                    # 创建ModelInfo对象
                    model_info = ModelInfo(
                        brand=brand,
                        name=f"{model_name} (DMXAPI)",
                        data_amount=None,
                        window=window,
                        providers=[provider_info]
                    )
                    
                    models.append(model_info)
                    
                except Exception as e:
                    logger.warning(f"解析模型 {model_name} 时出错: {e}")
                    continue
            
            logger.info(f"成功解析 {len(models)} 个模型")
            return models
            
        except Exception as e:
            logger.error(f"解析定价数据失败: {e}")
            return []
    
    async def get_models(self) -> List[ModelInfo]:
        """
        获取所有模型信息
        
        Returns:
            List[ModelInfo]: 模型信息列表
        """
        try:
            logger.info(f"正在请求 DMXAPI: {self.api_url}")
            
            response = self.session.get(
                self.api_url,
                timeout=self.plugin_config['timeout']
            )
            
            if response.status_code != 200:
                logger.error(f"API请求失败，状态码: {response.status_code}")
                return []
            
            data = response.json()
            logger.info(f"成功获取API数据")
            
            # 解析数据
            models = self._parse_pricing_data(data)
            
            logger.info(f"获取到 {len(models)} 个模型")
            return models
            
        except RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取模型数据失败: {e}")
            return []
    
    async def get_model_pricing(self, model_name: str) -> Optional[Dict]:
        """
        获取特定模型的价格信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Dict]: 价格信息字典，失败时返回None
        """
        models = await self.get_models()
        
        for model in models:
            if model_name in model.name:
                if model.providers:
                    provider = model.providers[0]
                    return {
                        'model_name': model.name,
                        'brand': model.brand,
                        'input_price': provider.tokens.input,
                        'output_price': provider.tokens.output,
                        'unit': provider.tokens.unit,
                        'window': model.window,
                        'provider': provider.display_name
                    }
        
        return None
    
    def get_brands(self) -> List[str]:
        """
        获取支持的品牌列表
        
        Returns:
            List[str]: 品牌名称列表
        """
        return [
            'OpenAI', 'Anthropic', 'Google', 'DeepSeek', 'Qwen', 
            'GLM', 'Doubao', 'ERNIE', 'Hunyuan', 'Moonshot', 
            'MiniMax', 'Baichuan', 'iFLYTEK'
        ]
    
    def get_plugin_info(self) -> Dict:
        """
        获取插件信息
        
        Returns:
            Dict: 插件信息字典
        """
        return {
            'name': self.config.name if self.config else 'dmx',
            'version': self.config.version if self.config else '1.0.0',
            'description': self.config.description if self.config else 'DMXAPI模型价格爬虫插件',
            'author': self.config.author if self.config else 'PricNicker Team',
            'brand_name': self.config.brand_name if self.config else 'DMXAPI',
            'enabled': self.enabled
        }

if __name__ == "__main__":
    # 测试代码
    import asyncio
    from dataclasses import dataclass
    
    @dataclass
    class TestPluginConfig:
        name: str = "dmx"
        version: str = "1.0.0"
        description: str = "DMXAPI模型价格爬虫插件"
        author: str = "PricNicker Team"
        brand_name: str = "DMXAPI"
        enabled: bool = True
    
    async def test_plugin():
        """测试插件功能"""
        print("DMXAPI插件功能测试")
        print("=" * 50)
        
        try:
            # 创建插件实例
            plugin = DmxPlugin(TestPluginConfig())
            
            # 验证配置
            print("\n=== 测试配置验证 ===")
            is_valid = await plugin.validate_config()
            print(f"配置验证结果: {'通过' if is_valid else '失败'}")
            
            if not is_valid:
                print("配置验证失败，跳过后续测试")
                return
            
            # 获取模型列表
            print("\n=== 测试获取模型列表 ===")
            models = await plugin.get_models()
            print(f"获取到 {len(models)} 个模型")
            
            # 显示前5个模型的详细信息
            if models:
                print("\n前5个模型详细信息:")
                for i, model in enumerate(models[:5]):
                    print(f"\n{i+1}. {model.name}")
                    print(f"   品牌: {model.brand}")
                    print(f"   窗口大小: {model.window}")
                    
                    if model.providers:
                        provider = model.providers[0]
                        print(f"   输入价格: ${provider.tokens.input:.6f}/{provider.tokens.unit}")
                        print(f"   输出价格: ${provider.tokens.output:.6f}/{provider.tokens.unit}")
                        print(f"   提供商: {provider.display_name}")
            
            # 获取品牌列表
            print("\n=== 测试获取品牌列表 ===")
            brands = plugin.get_brands()
            print(f"支持的品牌: {', '.join(brands)}")
            
            print("\n测试完成!")
            
        except Exception as e:
            print(f"测试过程中出错: {e}")
    
    # 运行测试
    asyncio.run(test_plugin())