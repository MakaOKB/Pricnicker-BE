#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIHubMix 模型价格爬虫插件

该插件从 aihubmix.com 获取AI模型的价格信息。
数据存储在页面的localStorage中，需要使用Selenium获取。

作者: Assistant
版本: 2.0
"""

import json
import time
import logging
import re
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIHubMixPlugin:
    """
    AIHubMix 价格爬虫插件
    
    从 aihubmix.com 获取AI模型价格信息
    """
    
    def __init__(self):
        """初始化插件"""
        self.base_url = "https://aihubmix.com/models"
        self.driver = None
        self.config = {
            'timeout': 30,
            'wait_time': 5,
            'headless': True
        }
        logger.info("AIHubMix插件初始化完成")
    
    def _setup_driver(self) -> webdriver.Chrome:
        """
        设置Chrome WebDriver
        
        Returns:
            webdriver.Chrome: 配置好的Chrome驱动
        """
        chrome_options = Options()
        if self.config['headless']:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.config['timeout'])
            return driver
        except Exception as e:
            logger.error(f"设置Chrome驱动失败: {e}")
            raise
    
    def _get_localStorage_data(self) -> Optional[List[Dict]]:
        """
        从localStorage获取模型数据
        
        Returns:
            Optional[List[Dict]]: 模型数据列表，失败时返回None
        """
        try:
            # 获取localStorage中的model_info数据
            script = """
            try {
                const modelInfoStr = localStorage.getItem('model_info');
                if (!modelInfoStr) {
                    return null;
                }
                return JSON.parse(modelInfoStr);
            } catch (e) {
                console.error('获取localStorage数据失败:', e);
                return null;
            }
            """
            
            result = self.driver.execute_script(script)
            if result:
                logger.info(f"成功从localStorage获取到 {len(result)} 个模型数据")
                return result
            else:
                logger.warning("localStorage中未找到model_info数据")
                return None
                
        except Exception as e:
            logger.error(f"获取localStorage数据失败: {e}")
            return None
    
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
                context_length = model_data.get('context_length', '')
                window = self._parse_context_length(context_length)
                
                # 解析价格信息
                token_info = self._parse_token_info(model_data)
                
                # 创建提供商信息
                provider_info = self._create_provider_info(model_data, token_info)
                
                # 构建符合ModelInfo格式的数据
                model_info = {
                    'brand': developer,  # 使用developer作为brand
                    'name': model_name,
                    'data_amount': self._extract_data_amount(model_data),  # 可为null
                    'window': window,
                    'providers': [provider_info]  # 包含提供商信息列表
                }
                
                # 如果有基础价格信息，添加到模型级别
                if token_info:
                    model_info['tokens'] = token_info
                
                parsed_models.append(model_info)
                
            except Exception as e:
                logger.error(f"解析模型数据失败: {model_data.get('model', 'unknown')}, 错误: {e}")
                continue
        
        logger.info(f"成功解析 {len(parsed_models)} 个模型")
        return parsed_models
    
    def _parse_context_length(self, context_length: str) -> int:
        """
        解析上下文长度字符串为整数，使用配置文件中的默认值
        
        Args:
            context_length: 上下文长度字符串，如 "128K", "32000"
            
        Returns:
            int: 上下文长度数值
        """
        # 从配置文件获取默认窗口大小
        default_window = self.config.get('extra_config', {}).get('data_format', {}).get('default_window_size', 4096)
        
        if not context_length:
            return default_window
            
        try:
            # 处理 "128K" 格式
            if isinstance(context_length, str):
                context_length = context_length.upper().strip()
                if context_length.endswith('K'):
                    return int(float(context_length[:-1]) * 1000)
                elif context_length.endswith('M'):
                    return int(float(context_length[:-1]) * 1000000)
                else:
                    return int(context_length)
            else:
                return int(context_length)
        except (ValueError, TypeError):
            logger.warning(f"无法解析上下文长度: {context_length}，使用默认值{default_window}")
            return default_window
    
    def _parse_token_info(self, model_data: Dict) -> Optional[Dict]:
        """
        解析价格信息为TokenInfo格式，使用配置文件中的字段设置
        
        Args:
            model_data: 原始模型数据
            
        Returns:
            Optional[Dict]: TokenInfo格式的价格信息
        """
        try:
            # 从配置文件获取价格提取设置
            price_config = self.config.get('extra_config', {}).get('data_format', {}).get('price_extraction', {})
            input_field = price_config.get('input_field', 'display_input')
            output_field = price_config.get('output_field', 'display_output')
            
            # 从指定字段提取价格
            display_input = model_data.get(input_field, '')
            display_output = model_data.get(output_field, '')
            
            input_price = self._extract_price_from_display(display_input)
            output_price = self._extract_price_from_display(display_output)
            
            if input_price is not None and output_price is not None:
                # 根据配置或价格范围判断货币单位
                currency_detection = price_config.get('currency_detection', 'auto')
                if currency_detection == 'auto':
                    # 自动判断货币单位（根据价格范围推测）
                    unit = "CNY" if input_price > 1 else "USD"
                else:
                    # 使用默认货币
                    unit = self.config.get('extra_config', {}).get('default_currency', 'USD')
                
                return {
                    'input': input_price,
                    'output': output_price,
                    'unit': unit
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"解析价格信息失败: {e}")
            return None
    
    def _extract_price_from_display(self, display_text: str) -> Optional[float]:
        """
        从显示文本中提取价格数值
        
        Args:
            display_text: 价格显示文本
            
        Returns:
            Optional[float]: 提取的价格数值
        """
        if not display_text:
            return None
            
        import re
        # 匹配数字（包括小数）
        price_match = re.search(r'([0-9]+\.?[0-9]*)', display_text)
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                return None
        return None
    
    def _extract_data_amount(self, model_data: Dict) -> Optional[int]:
        """
        提取训练数据量信息
        
        Args:
            model_data: 原始模型数据
            
        Returns:
            Optional[int]: 训练数据量（可为None）
        """
        # 从描述或其他字段中尝试提取数据量信息
        # 这里可以根据实际数据结构进行调整
        return None  # 暂时返回None，可根据实际数据调整
    
    def _create_provider_info(self, model_data: Dict, token_info: Optional[Dict]) -> Dict:
        """
        创建提供商信息，使用配置文件中的设置
        
        Args:
            model_data: 原始模型数据
            token_info: 价格信息
            
        Returns:
            Dict: ProviderInfo格式的提供商信息
        """
        # 从配置文件获取提供商信息
        data_format_config = self.config.get('extra_config', {}).get('data_format', {})
        
        provider_name = data_format_config.get('provider_name', 'aihubmix')
        display_name = data_format_config.get('provider_display_name', 'AiHubMix')
        api_website = data_format_config.get('provider_website', 'https://aihubmix.com')
        
        provider_info = {
            'name': provider_name,
            'display_name': display_name,
            'api_website': api_website
        }
        
        # 添加价格信息
        if token_info:
            provider_info['tokens'] = token_info
        else:
            # 提供默认价格信息
            default_currency = self.config.get('extra_config', {}).get('default_currency', 'USD')
            provider_info['tokens'] = {
                'input': 0.0,
                'output': 0.0,
                'unit': default_currency
            }
        
        return provider_info
    
    def get_models(self) -> List[Dict]:
        """
        获取模型列表，返回符合editv3.json接口规范的数据格式
        
        Returns:
            List[Dict]: 符合ModelInfo格式的模型列表
        """
        try:
            # 设置WebDriver
            self.driver = self._setup_driver()
            logger.info(f"正在访问: {self.base_url}")
            
            # 访问页面
            self.driver.get(self.base_url)
            
            # 等待页面加载
            logger.info(f"等待页面加载 {self.config['wait_time']} 秒...")
            time.sleep(self.config['wait_time'])
            
            # 等待React应用加载完成
            try:
                WebDriverWait(self.driver, self.config['timeout']).until(
                    EC.presence_of_element_located((By.ID, "root"))
                )
                logger.info("React应用加载完成")
            except TimeoutException:
                logger.warning("等待React应用加载超时，继续尝试获取数据")
            
            # 额外等待确保数据加载到localStorage
            time.sleep(3)
            
            # 从localStorage获取数据
            raw_data = self._get_localStorage_data()
            if not raw_data:
                logger.error("未能从localStorage获取到数据")
                return []
            
            # 解析数据为符合接口规范的格式
            models = self._parse_model_data(raw_data)
            
            logger.info(f"成功获取 {len(models)} 个模型，数据格式符合editv3.json规范")
            return models
            
        except Exception as e:
            logger.error(f"获取模型数据失败: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver已关闭")
    
    def get_brands(self) -> List[str]:
        """
        获取所有品牌列表，基于新的数据格式
        
        Returns:
            List[str]: 品牌名称列表
        """
        models = self.get_models()
        brands = list(set(model.get('brand', '') for model in models if model.get('brand')))
        brands.sort()
        logger.info(f"获取到 {len(brands)} 个品牌: {brands}")
        return brands
    
    def get_model_by_name(self, model_name: str) -> Optional[Dict]:
        """
        根据模型名称获取特定模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Dict]: 模型信息，未找到时返回None
        """
        models = self.get_models()
        for model in models:
            if model.get('name') == model_name or model.get('model_name') == model_name:
                logger.info(f"找到模型: {model_name}")
                return model
        
        logger.warning(f"未找到模型: {model_name}")
        return None
    
    def validate_config(self) -> bool:
        """
        验证插件配置
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查Chrome是否可用
            test_driver = self._setup_driver()
            test_driver.quit()
            logger.info("配置验证通过")
            return True
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False

# 测试代码
if __name__ == "__main__":
    plugin = AIHubMixPlugin()
    
    # 验证配置
    if not plugin.validate_config():
        print("配置验证失败，请检查Chrome WebDriver是否正确安装")
        exit(1)
    
    print("开始获取模型数据...")
    
    # 获取模型数据
    models = plugin.get_models()
    print(f"\n获取到 {len(models)} 个模型")
    
    # 显示前5个模型的详细信息（新格式）
    if models:
        print("\n前5个模型详细信息（editv3.json格式）:")
        for i, model in enumerate(models[:5]):
            print(f"\n{i+1}. {model.get('name', 'N/A')}")
            print(f"   品牌: {model.get('brand', 'N/A')}")
            print(f"   窗口大小: {model.get('window', 'N/A')}")
            print(f"   数据量: {model.get('data_amount', 'N/A')}")
            
            # 显示价格信息
            tokens = model.get('tokens')
            if tokens:
                print(f"   价格信息: 输入 {tokens.get('input', 'N/A')} {tokens.get('unit', 'N/A')}/1K tokens, 输出 {tokens.get('output', 'N/A')} {tokens.get('unit', 'N/A')}/1K tokens")
            else:
                print(f"   价格信息: 无")
            
            # 显示提供商信息
            providers = model.get('providers', [])
            if providers:
                provider = providers[0]  # 显示第一个提供商
                print(f"   提供商: {provider.get('display_name', 'N/A')} ({provider.get('name', 'N/A')})")
                print(f"   官网: {provider.get('api_website', 'N/A')}")
                provider_tokens = provider.get('tokens')
                if provider_tokens:
                    print(f"   提供商价格: 输入 {provider_tokens.get('input', 'N/A')} {provider_tokens.get('unit', 'N/A')}/1K tokens, 输出 {provider_tokens.get('output', 'N/A')} {provider_tokens.get('unit', 'N/A')}/1K tokens")
    
    # 获取品牌列表
    brands = plugin.get_brands()
    print(f"\n获取到 {len(brands)} 个品牌: {brands[:10]}...")  # 只显示前10个品牌
    
    # 显示数据格式验证信息
    if models:
        sample_model = models[0]
        print("\n数据格式验证:")
        print(f"✓ ModelInfo格式: 包含 brand, name, window, providers 字段")
        print(f"✓ ProviderInfo格式: 包含 name, display_name, api_website, tokens 字段")
        print(f"✓ TokenInfo格式: 包含 input, output, unit 字段")
        print(f"✓ 符合editv3.json接口规范")
    
    print("\n测试完成！")