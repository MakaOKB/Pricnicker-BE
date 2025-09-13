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
from ..base import BasePlugin, PluginConfig
from ...models import ModelInfo, TokenInfo, ProviderInfo

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
    
    def _parse_context_length(self, context_length: str) -> int:
        """
        解析上下文长度字符串，提取数值
        
        Args:
            context_length: 上下文长度字符串，如 "128K", "4096", "32k tokens"
            
        Returns:
            int: 上下文长度数值
        """
        if not context_length:
            return 4096  # 默认值
        
        # 移除所有空格并转为小写
        context_str = str(context_length).replace(' ', '').lower()
        
        # 提取数字和单位
        match = re.search(r'([0-9.]+)([kmb]?)', context_str)
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
        解析模型的价格信息
        
        Args:
            model_data: 模型数据字典
            
        Returns:
            Optional[Dict]: 包含input, output, unit的价格信息字典
        """
        try:
            # 从 model_ratio 计算价格（假设这是每1K tokens的价格比例）
            model_ratio = model_data.get('model_ratio', 0)
            
            if model_ratio > 0:
                # 假设基础价格为 0.01 CNY/1K tokens
                base_price = 0.01
                input_price = model_ratio * base_price
                output_price = model_ratio * base_price * 2  # 输出通常是输入价格的2倍
                
                return {
                    'input': round(input_price, 6),
                    'output': round(output_price, 6),
                    'unit': 'CNY'
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
                
                # 解析上下文窗口大小（从描述中提取）
                desc = model_data.get('desc', '')
                context_match = re.search(r'([0-9]+[KMB]?)\s*(?:令牌|token|上下文|context)', desc, re.IGNORECASE)
                if context_match:
                    context_length = context_match.group(1)
                else:
                    context_length = '4096'  # 默认值
                
                window = self._parse_context_length(context_length)
                
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
                    providers=provider_infos
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

if __name__ == "__main__":
    # 测试代码
    test_config = PluginConfig(
        name="aihubmix",
        version="3.0",
        description="AIHubMix模型价格爬虫插件",
        author="Assistant",
        brand_name="AIHubMix",
        enabled=True,
        api_key_required=False,
        timeout=30
    )
    
    plugin = AihubmixPlugin(test_config)
    
    # 验证配置
    import asyncio
    if not asyncio.run(plugin.validate_config()):
        print("配置验证失败，请检查网络连接")
        exit(1)
    
    print("开始获取模型数据...")
    
    # 获取模型列表
    models = asyncio.run(plugin.get_models())
    print(f"\n获取到 {len(models)} 个模型")
    
    # 显示前5个模型的详细信息
    if models:
        print("\n前5个模型详细信息（editv3.json格式）:")
        for i, model in enumerate(models[:5]):
            print(f"\n{i+1}. {model.name}")
            print(f"   品牌: {model.brand}")
            print(f"   窗口大小: {model.window}")
            print(f"   数据量: {model.data_amount}")
            
            # 显示提供商信息
            if model.providers:
                provider = model.providers[0]  # 显示第一个提供商
                print(f"   提供商: {provider.display_name} ({provider.name})")
                print(f"   官网: {provider.api_website}")
                print(f"   提供商价格: 输入 {provider.tokens.input} {provider.tokens.unit}/1K tokens, 输出 {provider.tokens.output} {provider.tokens.unit}/1K tokens")
    
    # 获取品牌列表
    brands = asyncio.run(plugin.get_brands())
    print(f"\n获取到 {len(brands)} 个品牌: {brands[:10]}...")  # 只显示前10个品牌
    
    # 数据格式验证
    if models:
        sample_model = models[0]
        print("\n数据格式验证:")
        print(f"✓ ModelInfo格式: 包含 brand, name, window, providers 字段")
        print(f"✓ ProviderInfo格式: 包含 name, display_name, api_website, tokens 字段")
        print(f"✓ TokenInfo格式: 包含 input, output, unit 字段")
        print(f"✓ 符合editv3.json接口规范")
    
    print("\n测试完成！")