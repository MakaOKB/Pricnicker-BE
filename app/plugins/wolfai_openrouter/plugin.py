#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WolfAI OpenRouter 插件实现

该插件从 OpenRouter API 获取模型价格信息，支持多种AI模型提供商。
OpenRouter 是一个统一的 AI 模型 API 平台，聚合了多家模型提供商。

主要功能:
- 从 OpenRouter API 获取实时模型数据
- 解析模型价格信息（输入/输出价格）
- 提取模型品牌和上下文窗口信息
- 支持多种模型提供商（OpenAI、Anthropic、Google等）

作者: PricNicker Team
版本: 1.0.0
最后更新: 2025-01-13
"""

import asyncio
import json
import logging
import re
from typing import List, Dict, Any, Optional
import aiohttp
from ..base import BasePlugin, PluginConfig
from ...models import ModelInfo

# 配置日志
logger = logging.getLogger(__name__)

class WolfaiOpenrouterPlugin(BasePlugin):
    """
    WolfAI OpenRouter 插件类
    
    从 OpenRouter API 获取模型价格信息的插件实现。
    OpenRouter 聚合了多家 AI 模型提供商，提供统一的 API 接口。
    """
    
    def __init__(self, config: PluginConfig):
        """
        初始化插件
        
        Args:
            config: 插件配置对象
        """
        super().__init__(config)
        self.api_url = config.extra_config.get('api_url', 'https://openrouter.ai/api/frontend/models')
        self.base_url = config.extra_config.get('base_url', 'https://openrouter.ai')
        self.user_agent = config.extra_config.get('user_agent', 
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        self.supported_brands = config.extra_config.get('supported_brands', [
            'OpenAI', 'Anthropic', 'Google', 'Qwen', 'Meta', 'Mistral', 
            'DeepSeek', 'xAI', 'Cohere', 'Perplexity', 'Meituan', 'Other'
        ])
        
        logger.info("WolfAI OpenRouter插件初始化完成")
    
    async def validate_config(self) -> bool:
        """
        验证插件配置
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查必要的配置项
            if not self.api_url:
                logger.error("API URL 未配置")
                return False
            
            if not self.base_url:
                logger.error("Base URL 未配置")
                return False
            
            # 测试 API 连接
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': self.user_agent,
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
                
                async with session.get(
                    self.api_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("WolfAI OpenRouter插件配置验证通过")
                        return True
                    else:
                        logger.error(f"API 连接失败，状态码: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return False
    
    async def get_models(self) -> List[ModelInfo]:
        """
        获取模型列表
        
        Returns:
            List[ModelInfo]: 模型信息列表
        """
        try:
            # 获取原始数据
            raw_data = await self._fetch_api_data()
            if not raw_data:
                logger.warning("未获取到API数据")
                return []
            
            # 解析模型数据
            models = self._parse_models(raw_data)
            logger.info(f"成功解析 {len(models)} 个模型")
            
            return models
        
        except Exception as e:
            logger.error(f"获取模型列表失败: {str(e)}")
            return []
    
    async def _fetch_api_data(self) -> Optional[Dict[str, Any]]:
        """
        从 API 获取原始数据
        
        Returns:
            Optional[Dict[str, Any]]: API 返回的原始数据
        """
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://openrouter.ai/',
                'Origin': 'https://openrouter.ai'
            }
            
            async with aiohttp.ClientSession() as session:
                logger.info(f"请求 OpenRouter API: {self.api_url}")
                
                async with session.get(
                    self.api_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"成功获取API数据，包含 {len(data.get('data', []))} 个模型")
                        return data
                    else:
                        logger.error(f"API请求失败，状态码: {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"API请求异常: {str(e)}")
            return None
    
    def _parse_models(self, data: Dict[str, Any]) -> List[ModelInfo]:
        """
        解析模型数据
        
        Args:
            data: API 返回的原始数据
            
        Returns:
            List[ModelInfo]: 解析后的模型信息列表
        """
        models = []
        
        try:
            model_list = data.get('data', [])
            if not model_list:
                logger.warning("API数据中未找到模型列表")
                return models
            
            for model_data in model_list:
                try:
                    # 解析基本信息
                    model_info = self._parse_single_model(model_data)
                    if model_info:
                        models.append(model_info)
                
                except Exception as e:
                    logger.warning(f"解析单个模型失败: {str(e)}")
                    continue
            
            return models
        
        except Exception as e:
            logger.error(f"解析模型数据失败: {str(e)}")
            return models
    
    def _parse_single_model(self, model_data: Dict[str, Any]) -> Optional[ModelInfo]:
        """
        解析单个模型数据
        
        Args:
            model_data: 单个模型的原始数据
            
        Returns:
            Optional[ModelInfo]: 解析后的模型信息
        """
        try:
            # 获取基本信息
            name = model_data.get('name', '')
            short_name = model_data.get('short_name', '')
            slug = model_data.get('slug', '')
            author = model_data.get('author', '')
            description = model_data.get('description', '')
            
            # 获取上下文长度
            context_length = model_data.get('context_length', 0)
            
            # 获取端点信息
            endpoint = model_data.get('endpoint', {})
            if not endpoint:
                return None
            
            # 获取价格信息
            pricing = endpoint.get('pricing', {})
            if not pricing:
                return None
            
            # 解析价格
            input_price = float(pricing.get('prompt', '0') or '0')
            output_price = float(pricing.get('completion', '0') or '0')
            
            # 提取品牌信息
            brand = self.extract_brand(model_data)
            
            # 提取上下文窗口
            context_window = self.extract_context_window(model_data)
            
            # 创建 ModelInfo 对象
            model_info = ModelInfo(
                name=name or short_name or slug,
                brand=brand,
                input_price=input_price,
                output_price=output_price,
                context_window=context_window,
                description=description[:200] if description else '',
                extra_info={
                    'slug': slug,
                    'author': author,
                    'provider_name': endpoint.get('provider_name', ''),
                    'provider_display_name': endpoint.get('provider_display_name', ''),
                    'model_variant_slug': endpoint.get('model_variant_slug', ''),
                    'quantization': endpoint.get('quantization'),
                    'is_free': endpoint.get('is_free', False),
                    'supports_tool_parameters': endpoint.get('supports_tool_parameters', False),
                    'supports_reasoning': endpoint.get('supports_reasoning', False),
                    'input_modalities': model_data.get('input_modalities', []),
                    'output_modalities': model_data.get('output_modalities', []),
                    'group': model_data.get('group', ''),
                    'hf_slug': model_data.get('hf_slug', ''),
                    'created_at': model_data.get('created_at', ''),
                    'updated_at': model_data.get('updated_at', '')
                }
            )
            
            return model_info
        
        except Exception as e:
            logger.warning(f"解析单个模型数据失败: {str(e)}")
            return None
    
    def extract_brand(self, model_data: Dict[str, Any]) -> str:
        """
        提取模型品牌信息
        
        Args:
            model_data: 模型数据
            
        Returns:
            str: 品牌名称
        """
        try:
            # 优先使用 author 字段
            author = model_data.get('author', '').strip()
            if author:
                # 标准化品牌名称
                author_lower = author.lower()
                
                # 品牌映射
                brand_mapping = {
                    'openai': 'OpenAI',
                    'anthropic': 'Anthropic',
                    'google': 'Google',
                    'qwen': 'Qwen',
                    'meta': 'Meta',
                    'mistral': 'Mistral',
                    'deepseek': 'DeepSeek',
                    'xai': 'xAI',
                    'cohere': 'Cohere',
                    'perplexity': 'Perplexity',
                    'meituan': 'Meituan'
                }
                
                for key, brand in brand_mapping.items():
                    if key in author_lower:
                        return brand
                
                # 如果没有匹配到，返回首字母大写的 author
                return author.title()
            
            # 尝试从 group 字段提取
            group = model_data.get('group', '').strip()
            if group and group != 'Other':
                return group
            
            return 'Other'
        
        except Exception as e:
            logger.warning(f"提取品牌信息失败: {str(e)}")
            return 'Other'
    
    def extract_context_window(self, model_data: Dict[str, Any]) -> int:
        """
        提取模型上下文窗口大小
        
        Args:
            model_data: 模型数据
            
        Returns:
            int: 上下文窗口大小
        """
        try:
            # 直接从 context_length 字段获取
            context_length = model_data.get('context_length')
            if context_length and isinstance(context_length, (int, float)):
                return int(context_length)
            
            # 从端点信息获取
            endpoint = model_data.get('endpoint', {})
            if endpoint:
                endpoint_context = endpoint.get('context_length')
                if endpoint_context and isinstance(endpoint_context, (int, float)):
                    return int(endpoint_context)
            
            # 默认值
            return 4096
        
        except Exception as e:
            logger.warning(f"提取上下文窗口失败: {str(e)}")
            return 4096
    
    def get_supported_brands(self) -> List[str]:
        """
        获取支持的品牌列表
        
        Returns:
            List[str]: 支持的品牌列表
        """
        return self.supported_brands.copy()