#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIHubMix 模型价格爬虫插件

该插件从 aihubmix.com API 获取AI模型的价格信息。
使用 API 端点: https://aihubmix.com/call/mdl_info

作者: Assistant
版本: 3.0
"""

import json
import logging
import re
import requests
from typing import Dict, List, Optional
# from ..base import BasePlugin, PluginConfig
# from ...models import ModelInfo, TokenInfo, ProviderInfo

# 临时类定义用于测试
class TokenInfo:
    def __init__(self, input, output, unit):
        self.input = input
        self.output = output
        self.unit = unit

class ProviderInfo:
    def __init__(self, name, website=None, display_name=None, api_website=None, tokens=None, **kwargs):
        self.name = name
        self.website = website or api_website
        self.display_name = display_name
        self.api_website = api_website
        self.tokens = tokens
        # 接受其他任意参数以避免错误
        for key, value in kwargs.items():
            setattr(self, key, value)

class ModelInfo:
    def __init__(self, name, provider=None, context_window=None, token_info=None, brand=None, data_amount=None, window=None, providers=None, **kwargs):
        self.name = name
        self.provider = provider
        self.context_window = context_window or window
        self.token_info = token_info
        self.brand = brand
        self.data_amount = data_amount
        self.window = window
        self.providers = providers or []
        # 接受其他任意参数以避免错误
        for key, value in kwargs.items():
            setattr(self, key, value)

class PluginConfig:
    def __init__(self):
        pass

class BasePlugin:
    def __init__(self, config):
        self.config = config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AihubmixPlugin(BasePlugin):
    """
    AIHubMix 价格爬虫插件
    
    从 aihubmix.com API 获取AI模型价格信息
    """
    
    def __init__(self, config: PluginConfig):
        """初始化插件"""
        super().__init__(config)
        self.api_url = "https://aihubmix.com/call/mdl_info"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://aihubmix.com/models',
            'Origin': 'https://aihubmix.com'
        }
        self._models_cache = None  # 添加缓存机制
        logger.info("AIHubMix插件初始化完成")
    
    def _fetch_api_data(self) -> Optional[List[Dict]]:
        """
        从 API 获取模型数据
        
        Returns:
            Optional[List[Dict]]: 模型数据列表，失败时返回None
        """
        try:
            logger.info(f"正在请求 API: {self.api_url}")
            response = requests.get(self.api_url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"API 请求失败，状态码: {response.status_code}")
                return None
            
            data = response.json()
            if not data.get('success', False):
                logger.error("API 返回失败状态")
                return None
            
            models_data = data.get('data', [])
            logger.info(f"成功从 API 获取到 {len(models_data)} 个模型数据")
            return models_data
            
        except requests.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取 API 数据失败: {e}")
            return None
    
    def _parse_context_length(self, model_data: Dict) -> int:
        """
        解析上下文长度，从多个字段中提取
        
        Args:
            model_data: 模型数据字典
            
        Returns:
            int: 上下文长度数值
        """
        # 首先检查 context_length 字段
        context_length = model_data.get('context_length', '')
        if context_length and str(context_length).strip():
            return self._extract_number_with_unit(str(context_length))
        
        # 从描述中提取上下文信息
        desc = model_data.get('desc', '') or model_data.get('desc_en', '')
        if desc:
            # 匹配各种上下文长度表达方式
            patterns = [
                r'([0-9]+[KMB]?)\s*(?:令牌|token|上下文|context)',
                r'([0-9]+[KMB]?)\s*(?:tokens?|contexts?)',
                r'(?:支持|context|window).*?([0-9]+[KMB]?)\s*(?:令牌|token)',
                r'([0-9]+[KMB]?)\s*(?:token|令牌)\s*(?:上下文|context)',
                r'上下文长度.*?([0-9]+[KMB]?)',
                r'context.*?length.*?([0-9]+[KMB]?)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, desc, re.IGNORECASE)
                if match:
                    context_str = match.group(1)
                    parsed_value = self._extract_number_with_unit(context_str)
                    if parsed_value > 4096:  # 只有当解析出的值大于默认值时才使用
                        return parsed_value
        
        # 从模型名称中提取（如 "Baichuan3-Turbo-128k"）
        model_name = model_data.get('model', '') or model_data.get('model_name', '')
        if model_name:
            match = re.search(r'[-_]([0-9]+[KMB]?)(?:$|[-_])', model_name, re.IGNORECASE)
            if match:
                context_str = match.group(1)
                parsed_value = self._extract_number_with_unit(context_str)
                if parsed_value > 4096:
                    return parsed_value
        
        return 4096  # 默认值
    
    def _extract_number_with_unit(self, text: str) -> int:
        """
        从文本中提取数字和单位，转换为实际数值
        
        Args:
            text: 包含数字和单位的文本，如 "128K", "32k", "4096"
            
        Returns:
            int: 转换后的数值
        """
        if not text:
            return 4096
        
        # 移除所有空格并转为小写
        text = str(text).replace(' ', '').lower()
        
        # 提取数字和单位
        match = re.search(r'([0-9.]+)([kmb]?)', text)
        if not match:
            return 4096
        
        number_str, unit = match.groups()
        try:
            number = float(number_str)
            
            # 根据单位转换
            if unit == 'k':
                return int(number * 1000)
            elif unit == 'm':
                return int(number * 1000000)
            elif unit == 'b':
                return int(number * 1000000000)
            else:
                return int(number)
        except ValueError:
            return 4096
    
    def _parse_token_info(self, model_data: Dict) -> Optional[Dict]:
        """
        解析模型的价格信息，直接使用API返回的价格比率
        
        Args:
            model_data: 模型数据字典
            
        Returns:
            Optional[Dict]: 包含input, output, unit的价格信息字典
        """
        try:
            # 直接获取API返回的价格比率，不做任何计算
            model_ratio = model_data.get('model_ratio', 0)
            completion_ratio = model_data.get('completion_ratio', model_ratio)
            
            if model_ratio is not None and completion_ratio is not None:
                return {
                    'input': float(model_ratio),
                    'output': float(completion_ratio), 
                    'unit': 'ratio'  # 使用ratio作为单位，表示这是API返回的原始比率
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"解析价格信息失败: {e}")
            return None
    
    def _extract_data_amount(self, model_data: Dict) -> Optional[int]:
        """
        提取模型的数据量信息
        
        Args:
            model_data: 模型数据字典
            
        Returns:
            Optional[int]: 数据量，单位为GB
        """
        # 从描述中尝试提取数据量信息
        desc = model_data.get('desc', '')
        if desc:
            # 查找类似 "训练数据量: 1.5TB" 的模式
            data_match = re.search(r'([0-9.]+)\s*([KMGT]?B)', desc, re.IGNORECASE)
            if data_match:
                amount_str, unit = data_match.groups()
                try:
                    amount = float(amount_str)
                    unit = unit.upper()
                    
                    if unit == 'TB':
                        return int(amount * 1000)
                    elif unit == 'GB':
                        return int(amount)
                    elif unit == 'MB':
                        return int(amount / 1000)
                    elif unit == 'KB':
                        return int(amount / 1000000)
                except ValueError:
                    pass
        
        return None
    
    def _create_provider_info(self, model_data: Dict, token_info: Optional[Dict]) -> ProviderInfo:
        """
        创建提供商信息对象
        
        Args:
            model_data: 模型数据字典
            token_info: 价格信息字典
            
        Returns:
            ProviderInfo: 提供商信息对象
        """
        # 创建TokenInfo对象
        if token_info:
            tokens = TokenInfo(
                input=token_info['input'],
                output=token_info['output'],
                unit=token_info['unit']
            )
        else:
            tokens = TokenInfo(input=0.0, output=0.0, unit='CNY')
        
        # 创建ProviderInfo对象
        provider_info = ProviderInfo(
            name='aihubmix',
            display_name='AIHubMix',
            api_website='https://aihubmix.com',
            tokens=tokens
        )
        
        return provider_info
    
    def _parse_model_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        解析模型数据，转换为符合editv3.json接口规范的ModelInfo格式
        
        Args:
            raw_data: 原始模型数据列表
            
        Returns:
            List[Dict]: 符合ModelInfo格式的模型数据列表
        """
        parsed_models = []
        
        for model_data in raw_data:
            try:
                # 提取基本信息
                model_name = model_data.get('model', '') or model_data.get('model_name', '')
                developer = model_data.get('developer', '')
                
                # 解析上下文窗口大小
                window = self._parse_context_length(model_data)
                
                # 解析价格信息
                token_info = self._parse_token_info(model_data)
                
                # 创建提供商信息
                provider_info = self._create_provider_info(model_data, token_info)
                
                # 将ProviderInfo对象转换为字典
                provider_dict = {
                    'name': provider_info.name,
                    'display_name': provider_info.display_name,
                    'api_website': provider_info.api_website,
                    'tokens': {
                        'input': provider_info.tokens.input,
                        'output': provider_info.tokens.output,
                        'unit': provider_info.tokens.unit
                    }
                }
                
                # 构建符合ModelInfo格式的数据
                model_info = {
                    'brand': developer or 'Unknown',
                    'name': model_name,
                    'window': window,
                    'data_amount': self._extract_data_amount(model_data),
                    'tokens': {
                        'input': provider_info.tokens.input,
                        'output': provider_info.tokens.output,
                        'unit': provider_info.tokens.unit
                    } if token_info else None,
                    'providers': [provider_dict]
                }
                
                parsed_models.append(model_info)
                
            except Exception as e:
                logger.warning(f"解析模型数据失败: {e}, 模型数据: {model_data}")
                continue
        
        logger.info(f"成功解析 {len(parsed_models)} 个模型数据")
        return parsed_models
    
    async def get_models(self) -> List[ModelInfo]:
        """
        获取模型列表，返回ModelInfo对象列表
        
        Returns:
            List[ModelInfo]: ModelInfo对象列表
        """
        try:
            # 从 API 获取数据
            raw_data = self._fetch_api_data()
            if not raw_data:
                logger.error("未能从 API 获取到数据")
                return []
            
            # 解析数据为ModelInfo格式
            models = self._parse_model_data(raw_data)
            
            # 转换为ModelInfo对象列表
            formatted_models = []
            for model_data in models:
                # 创建TokenInfo
                token_info_dict = model_data.get('tokens')
                token_info = TokenInfo(
                    input=token_info_dict.get('input', 0.0),
                    output=token_info_dict.get('output', 0.0),
                    unit=token_info_dict.get('unit', 'CNY')
                ) if token_info_dict else TokenInfo(input=0.0, output=0.0, unit='CNY')
                
                # 创建ProviderInfo列表
                provider_infos = []
                for provider_dict in model_data.get('providers', []):
                    provider_tokens_dict = provider_dict.get('tokens', {})
                    provider_tokens = TokenInfo(
                        input=provider_tokens_dict.get('input', 0.0),
                        output=provider_tokens_dict.get('output', 0.0),
                        unit=provider_tokens_dict.get('unit', 'CNY')
                    )
                    
                    provider_info = ProviderInfo(
                        name=provider_dict.get('name', 'aihubmix'),
                        display_name=provider_dict.get('display_name', 'AIHubMix'),
                        api_website=provider_dict.get('api_website', 'https://aihubmix.com'),
                        tokens=provider_tokens
                    )
                    provider_infos.append(provider_info)
                
                # 创建ModelInfo对象
                model_info = ModelInfo(
                    brand=model_data.get('brand', 'Unknown'),
                    name=model_data.get('name', 'Unknown'),
                    data_amount=model_data.get('data_amount'),
                    window=model_data.get('window', 4096),
                    providers=provider_infos,
                    token_info=token_info
                )
                
                formatted_models.append(model_info)
            
            logger.info(f"成功获取 {len(formatted_models)} 个模型，转换为ModelInfo对象")
            return formatted_models
            
        except Exception as e:
            logger.error(f"获取模型数据失败: {e}")
            return []
    
    async def get_brands(self) -> List[str]:
        """
        获取所有品牌列表
        
        Returns:
            List[str]: 品牌名称列表
        """
        models = await self.get_models()
        brands = list(set(model.brand for model in models if model.brand))
        brands.sort()
        logger.info(f"获取到 {len(brands)} 个品牌: {brands}")
        return brands
    
    async def get_model_by_name(self, model_name: str) -> Optional[ModelInfo]:
        """
        根据模型名称获取特定模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[ModelInfo]: 模型信息，未找到时返回None
        """
        models = await self.get_models()
        for model in models:
            if model.name == model_name:
                logger.info(f"找到模型: {model_name}")
                return model
        
        logger.warning(f"未找到模型: {model_name}")
        return None
    
    async def validate_config(self) -> bool:
        """
        验证插件配置是否正确
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 测试 API 连接
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                logger.info("API 连接测试成功")
                return True
            else:
                logger.error(f"API 连接测试失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False

# 测试代码
if __name__ == "__main__":
    import asyncio
    
    async def test_plugin():
        # 创建插件实例
        config = PluginConfig()
        plugin = AihubmixPlugin(config)
        
        print("开始测试修改后的价格解析逻辑...")
        
        # 获取模型数据
        models = await plugin.get_models()
        
        if models:
            print(f"\n成功获取 {len(models)} 个模型")
            
            # 显示前10个模型的价格信息
            print("\n=== 前10个模型的价格信息（直接使用API比率） ===")
            for i, model in enumerate(models[:10]):
                if model.token_info:
                    print(f"{i+1}. {model.name}:")
                    print(f"   输入价格: {model.token_info.input} {model.token_info.unit}")
                    print(f"   输出价格: {model.token_info.output} {model.token_info.unit}")
                else:
                    print(f"{i+1}. {model.name}: 无价格信息")
            
            # 统计价格信息
            models_with_price = [m for m in models if m.token_info]
            unique_input_prices = set(m.token_info.input for m in models_with_price)
            unique_output_prices = set(m.token_info.output for m in models_with_price)
            
            print(f"\n=== 价格统计 ===")
            print(f"有价格信息的模型: {len(models_with_price)}/{len(models)}")
            print(f"不同的输入价格比率: {len(unique_input_prices)} 种")
            print(f"不同的输出价格比率: {len(unique_output_prices)} 种")
            print(f"输入价格比率范围: {min(unique_input_prices):.6f} - {max(unique_output_prices):.6f}")
            print(f"输出价格比率范围: {min(unique_output_prices):.6f} - {max(unique_output_prices):.6f}")
            
        else:
            print("获取模型数据失败")
        
        print("\n测试完成！")
    
    # 运行异步测试
    asyncio.run(test_plugin())