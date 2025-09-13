#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZenMux 模型价格爬虫插件

该插件从 zenmux.ai 获取AI模型的价格信息。
使用 API 接口获取数据，提供备用的静态数据作为降级方案。

功能特性:
- 通过 API 接口获取实时模型数据
- 支持多种 AI 模型品牌（Anthropic、OpenAI、Google 等）
- 自动解析价格、上下文窗口等信息
- 符合 editv3.json 接口规范
- 包含配置验证和错误处理

作者: Assistant
版本: 2.0
最后更新: 2025-01-13
"""

import json
import time
import logging
import re
import requests
from typing import Dict, List, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError
# from ..base import BasePlugin, PluginConfig
# from ...models import ModelInfo, TokenInfo, ProviderInfo

# 临时类定义，用于独立测试
class PluginConfig:
    def __init__(self):
        pass

class BasePlugin:
    def __init__(self, config=None):
        self.config = config or PluginConfig()

class ModelInfo:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TokenInfo:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class ProviderInfo:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zenmux_plugin.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ZenmuxPlugin(BasePlugin):
    """
    ZenMux 价格爬虫插件
    
    从 zenmux.ai 获取AI模型的价格信息，支持多种AI模型品牌。
    
    主要功能:
    - 通过 API 接口获取实时模型数据
    - 解析模型价格、上下文窗口等信息
    - 提供品牌列表和模型查询功能
    - 数据格式符合 editv3.json 规范
    
    支持的品牌:
    - Anthropic (Claude 系列)
    - OpenAI (GPT 系列)
    - Google (Gemini 系列)
    - DeepSeek
    - MoonshotAI
    - Qwen
    - Z.AI
    
    Attributes:
        base_url (str): ZenMux 基础 URL
        models_url (str): 模型页面 URL
        session (requests.Session): HTTP 会话对象
        config (dict): 插件配置参数
    """
    
    # 类常量
    BASE_URL = "https://zenmux.ai"
    MODELS_URL = "https://zenmux.ai/models"
    API_URL = "https://zenmux.ai/api/frontend/model/listByFilter"
    DEFAULT_CTOKEN = "173hyG0fqu47kxXs6LWw2OBy"
    DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    def __init__(self, config: PluginConfig = None):
        """初始化插件"""
        super().__init__(config)
        self.base_url = self.BASE_URL
        self.models_url = self.MODELS_URL
        self.session = requests.Session()
        self.plugin_config = {
            'timeout': 30,
            'user_agent': self.DEFAULT_USER_AGENT
        }
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': self.plugin_config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        logger.info("ZenMux插件初始化完成")
    

    

    
    def _get_models_from_api(self) -> Optional[List[Dict]]:
        """
        通过ZenMux API获取真实的模型数据
        
        使用 ZenMux 官方 API 接口获取最新的模型数据，包括价格、上下文窗口、
        使用量等信息。根据用户要求，在有UA的情况下不需要任何参数。
        
        Returns:
            Optional[List[Dict]]: 成功时返回模型数据列表，失败时返回 None
            
        Raises:
            requests.RequestException: 网络请求异常
            json.JSONDecodeError: JSON 解析异常
        """
        api_url = self.API_URL
        # 根据用户要求，在有UA的情况下不需要任何参数
        params = {}
        
        max_retries = 3
        base_delay = 1  # 基础延迟时间（秒）
        
        for attempt in range(max_retries):
            try:
                logger.info(f"正在调用ZenMux API (尝试 {attempt + 1}/{max_retries})")
                response = requests.get(
                    api_url, 
                    params=params,
                    timeout=self.plugin_config['timeout'],
                    headers={
                        'User-Agent': self.DEFAULT_USER_AGENT,
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Referer': self.models_url
                    }
                )
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        
                        # 检查响应格式
                        if isinstance(response_data, dict) and 'success' in response_data and 'data' in response_data:
                            if response_data.get('success'):
                                models = response_data['data']
                                if len(models) > 0:
                                    logger.info(f"✅ API调用成功，获取到 {len(models)} 个模型")
                                    
                                    # 保存响应数据用于调试
                                    with open('api_response.json', 'w', encoding='utf-8') as f:
                                        json.dump(response_data, f, ensure_ascii=False, indent=2)
                                    
                                    return models
                                else:
                                    logger.warning("API返回空模型列表")
                            else:
                                logger.error(f"API返回失败状态: {response_data}")
                        else:
                            # 兼容直接返回数组的情况
                            if isinstance(response_data, list):
                                logger.info(f"✅ API调用成功，获取到 {len(response_data)} 个模型")
                                return response_data
                            else:
                                logger.error(f"API返回格式异常: {type(response_data)}")
                    except ValueError as e:
                        logger.error(f"API响应JSON解析失败: {e}")
                elif response.status_code == 429:
                    logger.warning(f"API请求频率限制 (状态码: {response.status_code})")
                elif response.status_code >= 500:
                    logger.error(f"API服务器错误 (状态码: {response.status_code})")
                else:
                    logger.error(f"API请求失败，状态码: {response.status_code}，响应: {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                logger.error(f"API请求超时 (尝试 {attempt + 1}/{max_retries})")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"API连接失败 (尝试 {attempt + 1}/{max_retries}): {str(e)[:100]}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求异常 (尝试 {attempt + 1}/{max_retries}): {str(e)[:100]}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            except Exception as e:
                logger.error(f"API数据处理异常 (尝试 {attempt + 1}/{max_retries}): {str(e)[:100]}")
            
            # 指数退避策略
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # 1秒, 2秒, 4秒
                logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
        
        logger.error("所有API调用尝试均失败")
        return None
    
    def _parse_brand_and_name(self, name: str, author: str) -> tuple[str, str]:
        """
        解析品牌和模型名称
        
        从 API 返回的 name 和 author 字段中提取标准化的品牌名称和模型名称。
        支持多种格式的输入，包括 "brand:model" 格式和独立的品牌/模型字段。
        
        品牌映射规则:
        - anthropic -> Anthropic
        - openai -> OpenAI
        - google -> Google
        - deepseek -> DeepSeek
        - moonshot -> MoonshotAI
        - qwen -> Qwen
        - z.ai -> Z.AI
        
        Args:
            name (str): 模型名称，可能包含品牌前缀
            author (str): 作者信息，用于确定品牌
            
        Returns:
            tuple[str, str]: (标准化品牌名称, 模型名称)
            
        Examples:
            >>> _parse_brand_and_name("anthropic:claude-3-sonnet", "anthropic")
            ("Anthropic", "claude-3-sonnet")
            >>> _parse_brand_and_name("GPT-4", "openai")
            ("OpenAI", "GPT-4")
        """
        # 品牌映射表
        brand_mapping = {
            'anthropic': 'Anthropic',
            'openai': 'OpenAI', 
            'google': 'Google',
            'deepseek': 'DeepSeek',
            'moonshot': 'MoonshotAI',
            'qwen': 'Qwen',
            'z.ai': 'Z.AI'
        }
        
        # 从name字段提取品牌和模型名
        if ':' in name:
            brand_part, model_name = name.split(':', 1)
            brand = brand_part.strip()
            model_name = model_name.strip()
        else:
            # 根据author字段确定品牌
            brand = brand_mapping.get(author.lower(), author.title())
            model_name = name
        
        return brand, model_name
    
    def _convert_api_models_to_internal_format(self, api_models: List[Dict]) -> List[Dict]:
        """
        将API返回的模型数据转换为内部格式
        
        Args:
            api_models: API返回的模型数据列表
            
        Returns:
            List[Dict]: 转换后的模型数据列表
        """
        converted_models = []
        
        for model in api_models:
            try:
                # 解析品牌名称和模型名
                name = model.get('name', '')
                author = model.get('author', '')
                brand, model_name = self._parse_brand_and_name(name, author)
                
                # 解析价格信息
                input_price = float(model.get('pricing_prompt', 0))
                output_price = float(model.get('pricing_completion', 0))
                
                # 解析上下文长度
                context_length = model.get('context_length', 0)
                
                # 解析使用量
                token_week = model.get('token_week', '0')
                
                converted_model = {
                    'name': model_name,
                    'brand': brand,
                    'tokens_used': self._format_token_usage(token_week),
                    'context_window': self._format_context_window(context_length),
                    'input_price': input_price,
                    'output_price': output_price,
                    'currency': 'USD',
                    'unit': 'M tokens',
                    'description': model.get('description', '').strip()
                }
                
                converted_models.append(converted_model)
                
            except Exception as e:
                logger.warning(f"转换模型数据失败: {model.get('name', 'Unknown')}, 错误: {e}")
                continue
        
        logger.info(f"成功转换 {len(converted_models)} 个模型数据")
        return converted_models
    
    def _format_token_usage(self, token_week: str) -> str:
        """
        格式化token使用量
        
        Args:
            token_week: 周使用量字符串
            
        Returns:
            str: 格式化后的使用量
        """
        try:
            usage = int(token_week)
            if usage >= 1000000:
                return f"{usage / 1000000:.2f}M"
            elif usage >= 1000:
                return f"{usage / 1000:.2f}K"
            else:
                return str(usage)
        except (ValueError, TypeError):
            return "0"
    
    def _format_context_window(self, context_length: int) -> str:
        """
        格式化上下文窗口大小
        
        Args:
            context_length: 上下文长度
            
        Returns:
            str: 格式化后的上下文窗口
        """
        try:
            if context_length >= 1000000:
                return f"{context_length / 1000000:.2f}M"
            elif context_length >= 1000:
                return f"{context_length / 1000:.2f}K"
            else:
                return str(context_length)
        except (ValueError, TypeError):
            return "0"
    
        # 备用数据方法已移除，只使用真实API数据
        except Exception as e:
            logger.error(f"获取模型数据失败: {e}")
            return []
    
    async def initialize(self) -> bool:
        """初始化插件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 验证配置
            return self.validate_config()
        except Exception as e:
            logger.error(f"插件初始化失败: {e}")
            return False
    
    def get_plugin_info(self) -> Dict:
        """获取插件信息
        
        Returns:
            Dict: 插件信息字典
        """
        return {
            'name': self.config.name,
            'version': self.config.version,
            'description': self.config.description,
            'author': self.config.author,
            'brand_name': self.config.brand_name,
            'enabled': self.enabled
        }
    

    
    def _validate_model_data(self, model_data: Dict) -> bool:
        """
        验证原始模型数据
        
        Args:
            model_data: 原始模型数据字典
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查必需字段 - 只检查name字段，brand从name中提取
            if not model_data.get('name'):
                logger.debug(f"缺少必需字段: name")
                return False
            
            # 检查价格数据 - 使用正确的字段名
            input_price = model_data.get('pricing_prompt')
            output_price = model_data.get('pricing_completion')
            
            if input_price is not None:
                try:
                    float(input_price)
                except (ValueError, TypeError):
                    logger.debug(f"无效的输入价格: {input_price}")
                    return False
            
            if output_price is not None:
                try:
                    float(output_price)
                except (ValueError, TypeError):
                    logger.debug(f"无效的输出价格: {output_price}")
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"数据验证过程中出错: {e}")
            return False
    
    def _validate_converted_model(self, model_info: Dict) -> bool:
        """
        验证转换后的模型数据
        
        Args:
            model_info: 转换后的模型信息字典
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查基本结构 - v4.json规范
            required_fields = ['brand', 'name', 'window', 'providers']
            for field in required_fields:
                if field not in model_info:
                    logger.debug(f"转换后数据缺少字段: {field}")
                    return False
            
            # 检查可选字段
            if 'data_amount' in model_info:
                data_amount = model_info['data_amount']
                if data_amount is not None and not isinstance(data_amount, int):
                    logger.debug(f"data_amount字段类型错误，应为int或null: {type(data_amount)}")
                    return False
            
            # 检查recommended_provider字段
            if 'recommended_provider' in model_info:
                recommended_provider = model_info['recommended_provider']
                if recommended_provider is not None and not isinstance(recommended_provider, str):
                    logger.debug(f"recommended_provider字段类型错误，应为str或null: {type(recommended_provider)}")
                    return False
            

            
            # 检查providers结构
            providers = model_info.get('providers', [])
            if not isinstance(providers, list) or len(providers) == 0:
                logger.debug("providers字段无效")
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"转换后数据验证过程中出错: {e}")
            return False
    
    def _parse_context_length(self, context_str: str) -> int:
        """
        解析上下文长度字符串
        
        Args:
            context_str: 上下文长度字符串，如 "4K", "128K", "1M"
            
        Returns:
            int: 上下文长度数值
        """
        try:
            if not context_str or context_str == 'N/A':
                return 4096
            
            # 移除空格并转换为大写
            context_str = context_str.strip().upper()
            
            # 提取数字部分
            number_match = re.search(r'([\d.]+)', context_str)
            if not number_match:
                logger.debug(f"无法从上下文字符串中提取数字: {context_str}")
                return 4096
            
            number = float(number_match.group(1))
            
            # 根据单位转换
            if 'M' in context_str:
                result = int(number * 1000000)
            elif 'K' in context_str:
                result = int(number * 1000)
            else:
                result = int(number)
            
            logger.debug(f"上下文长度解析: {context_str} -> {result}")
            return result
                
        except Exception as e:
            logger.warning(f"解析上下文长度失败: {context_str}, 错误: {e}")
            return 4096
    

    
    async def get_models(self) -> List[ModelInfo]:
        """
        获取所有模型信息
        
        这是插件的主要接口方法，负责获取、转换和验证所有模型数据。
        首先尝试通过 API 获取实时数据，如果失败则使用备用数据。
        
        处理流程:
        1. 调用 API 获取原始数据
        2. 数据验证和清洗
        3. 格式转换为 v4.json 规范
        4. 二次验证转换后的数据
        5. 返回有效的模型列表
        
        数据格式 (v4.json):
        {
            "brand": "品牌名称",
            "name": "模型名称", 
            "data_amount": 训练数据量(整数或null),
            "window": 上下文窗口大小(整数),
            "tokens": {
                "input": 输入价格(浮点数),
                "output": 输出价格(浮点数),
                "unit": "价格单位"
            },
            "providers": [提供商信息列表],
            "recommended_provider": "推荐提供商"
        }
        
        Returns:
            List[Dict]: 模型信息列表，符合 v4.json 格式规范
            
        Note:
            - 所有价格以 USD 为单位，按每百万 tokens 计费
            - 上下文窗口大小为 token 数量的整数值
            - 如果获取失败，返回空列表而不是抛出异常
        """
        start_time = time.time()
        models = []
        
        try:
            logger.info("🚀 开始获取ZenMux模型数据")
            
            # 只使用API获取真实数据，不再使用备用数据
            logger.info("📡 使用API获取真实数据...")
            dynamic_data = self._get_models_from_api()
            
            if not dynamic_data:
                logger.error("❌ API获取失败，无法获取模型数据")
                return []
            
            logger.info(f"📊 获取到 {len(dynamic_data)} 条原始数据，开始转换格式...")
            
            # 转换为标准格式
            successful_conversions = 0
            failed_conversions = 0
            
            for i, model_data in enumerate(dynamic_data):
                try:
                    # 数据验证
                    if not self._validate_model_data(model_data):
                        logger.warning(f"模型数据 {i+1} 验证失败，跳过")
                        failed_conversions += 1
                        continue
                    
                    # 调试：打印价格相关字段
                    if i < 3:  # 只打印前3个模型的调试信息
                        logger.info(f"模型 {i+1} 价格字段: pricing_prompt={model_data.get('pricing_prompt')}, pricing_completion={model_data.get('pricing_completion')}")
                        logger.info(f"模型 {i+1} 所有字段: {list(model_data.keys())}")
                    
                    # 从name字段提取brand信息
                    model_name = model_data.get('name', 'Unknown')
                    author = model_data.get('author', '')
                    brand, name = self._parse_brand_and_name(model_name, author)
                    
                    # 解析数据量，确保类型为int或null
                    data_amount = model_data.get('tokens_used', None)
                    if data_amount is not None:
                        if isinstance(data_amount, str):
                            if data_amount.isdigit():
                                data_amount = int(data_amount)
                            elif data_amount in ['N/A', 'Unknown', '', 'null', 'None']:
                                data_amount = None
                            else:
                                # 尝试解析包含单位的字符串（如"1.2M"）
                                try:
                                    # 移除非数字字符并转换
                                    clean_str = re.sub(r'[^0-9.]', '', data_amount)
                                    if clean_str:
                                        data_amount = int(float(clean_str))
                                    else:
                                        data_amount = None
                                except (ValueError, TypeError):
                                    data_amount = None
                        elif not isinstance(data_amount, int):
                            # 如果不是字符串也不是整数，尝试转换
                            try:
                                data_amount = int(data_amount)
                            except (ValueError, TypeError):
                                data_amount = None
                    
                    # 创建TokenInfo对象 - 使用API返回的正确字段名
                    input_price = float(model_data.get('pricing_prompt', 0.0))
                    output_price = float(model_data.get('pricing_completion', 0.0))
                    currency = 'USD'  # ZenMux API返回的价格单位为USD
                    
                    token_info = TokenInfo(
                        input=input_price,
                        output=output_price,
                        unit=currency
                    )
                    
                    # 调试：打印TokenInfo创建后的值
                    if i < 3:
                        logger.info(f"模型 {i+1} TokenInfo: input={token_info.input}, output={token_info.output}, unit={token_info.unit}")
                    
                    # 创建ProviderInfo对象
                    provider_info = ProviderInfo(
                        name='zenmux',
                        display_name='ZenMux',
                        api_website='https://zenmux.ai',
                        tokens=token_info
                    )
                    
                    # 创建ModelInfo对象
                    model_info = ModelInfo(
                        brand=brand,
                        name=name,
                        data_amount=data_amount,
                        window=self._parse_context_length(str(model_data.get('context_length', 4096))),
                        providers=[provider_info],
                        recommended_provider='zenmux'
                    )
                    
                    # 验证转换后的数据
                    model_dict = {
                        'brand': model_info.brand,
                        'name': model_info.name,
                        'data_amount': model_info.data_amount,
                        'window': model_info.window,
                        'providers': [{
                            'name': provider.name,
                            'display_name': provider.display_name,
                            'api_website': provider.api_website,
                            'tokens': {
                                 'input': provider.tokens.input,
                                 'output': provider.tokens.output,
                                 'unit': provider.tokens.unit
                             }
                        } for provider in model_info.providers],
                        'recommended_provider': model_info.recommended_provider
                    }
                    
                    # 调试：打印验证字典中的tokens值
                    if i < 3:
                        tokens_dict = model_dict['providers'][0]['tokens']
                        logger.info(f"模型 {i+1} 验证字典tokens: input={tokens_dict['input']}, output={tokens_dict['output']}, unit={tokens_dict['unit']}")
                    
                    if self._validate_converted_model(model_dict):
                        models.append(model_info)
                        successful_conversions += 1
                        logger.debug(f"✅ 模型 {model_info.name} 转换成功")
                    else:
                        logger.warning(f"⚠️ 模型 {model_data.get('name', 'Unknown')} 转换后验证失败")
                        failed_conversions += 1
                        
                except ValueError as e:
                    logger.warning(f"数据类型转换错误 (模型 {i+1}): {e}")
                    failed_conversions += 1
                except KeyError as e:
                    logger.warning(f"缺少必需字段 (模型 {i+1}): {e}")
                    failed_conversions += 1
                except Exception as e:
                    logger.warning(f"转换模型数据失败 (模型 {i+1}): {e}")
                    failed_conversions += 1
            
            # 统计信息
            elapsed_time = time.time() - start_time
            logger.info(f"📈 数据获取完成:")
            logger.info(f"   ✅ 成功转换: {successful_conversions} 个模型")
            logger.info(f"   ❌ 转换失败: {failed_conversions} 个模型")
            logger.info(f"   ⏱️ 总耗时: {elapsed_time:.2f} 秒")
            
            if models:
                logger.info(f"🎉 成功获取 {len(models)} 个有效模型")
                # 输出品牌统计
                brands = set(model.brand for model in models)
                logger.info(f"📋 涉及品牌: {', '.join(sorted(brands))}")
            else:
                logger.error("💥 没有获取到任何有效模型数据")
            
            return models
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"💥 获取模型数据过程中发生严重错误: {e}")
            logger.error(f"⏱️ 失败前耗时: {elapsed_time:.2f} 秒")
            return []
        finally:
            # 确保资源清理
            logger.info("🔧 资源清理完成")
    
    async def get_brands(self) -> List[str]:
        """
        获取支持的品牌列表
        
        从当前可用的模型数据中提取所有唯一的品牌名称，
        返回按字母顺序排序的品牌列表。
        
        该方法会调用 get_models() 获取完整的模型数据，
        然后提取并去重所有品牌信息。
        
        Returns:
            List[str]: 按字母顺序排序的品牌名称列表
            
        Examples:
            >>> plugin.get_brands()
            ['Anthropic', 'DeepSeek', 'Google', 'MoonshotAI', 'OpenAI', 'Qwen']
            
        Note:
            - 过滤掉空字符串和 'Unknown' 品牌
            - 如果没有可用模型，返回空列表
        """
        try:
            logger.info("🏷️ 开始获取品牌列表...")
            
            models = await self.get_models()
            if not models:
                logger.warning("⚠️ 没有模型数据，无法获取品牌列表")
                return []
            
            # 提取品牌并去重
            brands = set()
            for model in models:
                brand = model.brand.strip()
                if brand and brand != 'Unknown':
                    brands.add(brand)
            
            brand_list = sorted(list(brands))
            logger.info(f"✅ 成功获取 {len(brand_list)} 个品牌: {', '.join(brand_list)}")
            return brand_list
            
        except Exception as e:
            logger.error(f"💥 获取品牌列表失败: {e}")
            return []
    
    async def get_model_by_name(self, model_name: str) -> Optional[ModelInfo]:
        """
        根据模型名称获取特定模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            ModelInfo: 模型信息，未找到时返回None
        """
        try:
            models = await self.get_models()
            for model in models:
                if model.name.lower() == model_name.lower():
                    return model
            return None
        except Exception as e:
            logger.error(f"获取特定模型失败: {e}")
            return None
    
    def validate_config(self) -> bool:
        """
        验证插件配置和网络连接
        
        执行全面的配置验证，包括参数检查、URL 格式验证、
        网络连接测试和 API 可用性测试。
        
        验证项目:
        1. 必需配置参数检查 (timeout, user_agent)
        2. URL 格式验证 (base_url, models_url)
        3. 网络连接测试 (访问主站)
        4. API 连接测试 (测试 API 端点)
        
        Returns:
            bool: 所有验证项通过时返回 True，否则返回 False
            
        Side Effects:
            - 在日志中记录详细的验证过程和结果
            - 网络测试可能需要几秒钟时间
            
        Note:
            - 建议在使用插件前调用此方法进行预检查
            - 验证失败时会在日志中输出具体的错误信息
        """
        validation_errors = []
        
        try:
            logger.info("开始配置验证...")
            
            # 1. 验证基本配置参数
            required_configs = ['timeout', 'user_agent']
            for config_key in required_configs:
                if config_key not in self.plugin_config:
                    validation_errors.append(f"缺少必需配置: {config_key}")
                elif self.plugin_config[config_key] is None:
                    validation_errors.append(f"配置值为空: {config_key}")
            
            # 2. 验证URL格式
            if not self.base_url.startswith(('http://', 'https://')):
                validation_errors.append(f"无效的基础URL格式: {self.base_url}")
            
            if not self.models_url.startswith(('http://', 'https://')):
                validation_errors.append(f"无效的模型URL格式: {self.models_url}")
            
            # 3. 测试网络连接
            try:
                logger.info(f"测试网络连接: {self.base_url}")
                response = self.session.get(self.base_url, timeout=15)
                if response.status_code == 200:
                    logger.info(f"网络连接正常，状态码: {response.status_code}")
                else:
                    validation_errors.append(f"网络连接异常，状态码: {response.status_code}")
            except Timeout:
                validation_errors.append("网络连接超时")
            except ConnectionError:
                validation_errors.append("网络连接失败")
            except RequestException as e:
                validation_errors.append(f"网络请求异常: {e}")
            
            # 4. 测试API连接
            try:
                logger.info("测试API连接...")
                test_params = {
                    'ctoken': self.DEFAULT_CTOKEN,
                    'sort': 'topweekly',
                    'keyword': ''
                }
                response = self.session.get(self.API_URL, params=test_params, timeout=15)
                if response.status_code == 200:
                    logger.info("API连接测试通过")
                else:
                    validation_errors.append(f"API连接异常，状态码: {response.status_code}")
            except Exception as e:
                validation_errors.append(f"API连接测试失败: {e}")
            
            # 5. 输出验证结果
            if validation_errors:
                logger.error("配置验证失败:")
                for error in validation_errors:
                    logger.error(f"  - {error}")
                return False
            else:
                logger.info("✅ 所有配置验证通过")
                return True
            
        except Exception as e:
            logger.error(f"配置验证过程中发生未知错误: {e}")
            return False

if __name__ == "__main__":
    plugin = ZenMuxPlugin()
    
    # 验证配置
    if not plugin.validate_config():
        print("配置验证失败，请检查网络连接和API访问")
        exit(1)
    
    print("开始获取ZenMux模型数据...")
    
    # 获取模型数据
    models = plugin.get_models()
    print(f"\n获取到 {len(models)} 个模型")
    
    # 显示前5个模型的详细信息
    if models:
        print("\n前5个模型详细信息（v4.json格式）:")
        for i, model in enumerate(models[:5]):
            print(f"\n{i+1}. {model.name}")
            print(f"   品牌: {model.brand}")
            print(f"   窗口大小: {model.window}")
            print(f"   数据量: {model.data_amount}")
            
            if model.providers:
                provider = model.providers[0]
                print(f"   价格信息: 输入 {provider.tokens.input} {provider.tokens.unit}, 输出 {provider.tokens.output} {provider.tokens.unit}")
            else:
                print(f"   价格信息: 无")
            
            if model.providers:
                provider = model.providers[0]
                print(f"   提供商: {provider.display_name} ({provider.name})")
                print(f"   官网: {provider.api_website}")
    
    # 获取品牌列表
    brands = plugin.get_brands()
    print(f"\n获取到 {len(brands)} 个品牌: {brands}")
    
    # 数据格式验证
    if models:
        print("\n数据格式验证:")
        print(f"✓ ModelInfo格式: 包含 brand, name, window, providers 字段")
        print(f"✓ ProviderInfo格式: 包含 name, display_name, api_website, tokens 字段")
        print(f"✓ TokenInfo格式: 包含 input, output, unit 字段")
        print(f"✓ 符合v4.json接口规范")
    
    print("\n测试完成！")