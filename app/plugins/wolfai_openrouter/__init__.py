#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WolfAI OpenRouter 插件包初始化文件

该文件定义了 WolfAI OpenRouter 插件的入口点和导出接口。
插件提供从 OpenRouter API 获取多家AI模型提供商价格信息的功能。

主要功能:
- 导出插件主类 WolfaiOpenrouterPlugin
- 定义插件元数据信息
- 提供插件版本和描述信息
- 支持插件的动态加载和初始化

作者: PricNicker Team
版本: 1.0.0
最后更新: 2025-01-13
"""

from .plugin import WolfaiOpenrouterPlugin

# 插件元数据
__version__ = "1.0.0"
__author__ = "PricNicker Team"
__description__ = "WolfAI OpenRouter 模型价格爬虫插件，从 OpenRouter API 获取多家模型提供商价格信息"
__plugin_name__ = "wolfai_openrouter"
__brand_name__ = "WolfAI (OpenRouter)"

# 导出的公共接口
__all__ = [
    'WolfaiOpenrouterPlugin',
    '__version__',
    '__author__',
    '__description__',
    '__plugin_name__',
    '__brand_name__'
]

# 插件工厂函数
def create_plugin(config=None):
    """
    创建插件实例
    
    Args:
        config: 插件配置对象，如果为None则使用默认配置
        
    Returns:
        WolfaiOpenrouterPlugin: 插件实例
    """
    from dataclasses import dataclass
    from typing import Dict, Any, Optional
    
    @dataclass
    class SimpleConfig:
        name: str = "wolfai_openrouter"
        version: str = "1.0.0"
        description: str = "WolfAI OpenRouter 模型价格爬虫插件"
        author: str = "PricNicker Team"
        brand_name: str = "WolfAI (OpenRouter)"
        enabled: bool = True
        api_key_required: bool = False
        base_url: Optional[str] = None
        timeout: int = 30
        rate_limit: Optional[int] = None
        extra_config: Dict[str, Any] = None
        
        def __post_init__(self):
            if self.extra_config is None:
                self.extra_config = {
                    "api_url": "https://openrouter.ai/api/frontend/models",
                    "base_url": "https://openrouter.ai",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "supported_brands": [
                        "OpenAI", "Anthropic", "Google", "Qwen", "Meta", "Mistral", 
                        "DeepSeek", "xAI", "Cohere", "Perplexity", "Meituan", "Other"
                    ]
                }
    
    if config is None:
        config = SimpleConfig()
    
    return WolfaiOpenrouterPlugin(config)

def get_plugin_info():
    """
    获取插件基本信息
    
    Returns:
        dict: 包含插件基本信息的字典
    """
    return {
        'name': __plugin_name__,
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'brand_name': __brand_name__,
        'api_url': 'https://openrouter.ai/api/frontend/models',
        'supported_brands': [
            'OpenAI', 'Anthropic', 'Google', 'Qwen', 'Meta', 'Mistral', 
            'DeepSeek', 'xAI', 'Cohere', 'Perplexity', 'Meituan', 'Other'
        ],
        'features': [
            '实时模型价格获取',
            '多品牌模型支持',
            '自动价格解析',
            '上下文窗口识别',
            '配置验证',
            '聚合多家提供商数据'
        ]
    }

async def health_check():
    """
    插件健康检查
    
    Returns:
        dict: 健康检查结果
    """
    try:
        plugin = create_plugin()
        
        # 验证配置
        config_valid = await plugin.validate_config()
        
        if config_valid:
            return {
                'status': 'healthy',
                'config_valid': True,
                'message': 'Plugin is working properly'
            }
        else:
            return {
                'status': 'unhealthy',
                'config_valid': False,
                'message': 'Plugin configuration validation failed'
            }
    except Exception as e:
        return {
            'status': 'error',
            'config_valid': False,
            'message': f'Health check failed: {str(e)}'
        }

def check_compatibility():
    """
    检查插件兼容性
    
    Returns:
        dict: 兼容性检查结果
    """
    try:
        import aiohttp
        import json
        import re
        
        # 检查必要的依赖
        required_modules = ['aiohttp', 'json', 're']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            return {
                'compatible': False,
                'message': f'Missing required modules: {", ".join(missing_modules)}'
            }
        
        return {
            'compatible': True,
            'message': 'All dependencies are available'
        }
    except Exception as e:
        return {
            'compatible': False,
            'message': f'Compatibility check failed: {str(e)}'
        }

# 测试代码
if __name__ == "__main__":
    print("WolfAI OpenRouter Plugin Test")
    print("=" * 50)
    
    import asyncio

    async def test_init():
        """测试插件初始化和基本功能"""
        
        # 测试插件信息
        print("1. 插件信息:")
        info = get_plugin_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        print()
        
        # 测试兼容性检查
        print("2. 兼容性检查:")
        compatibility = check_compatibility()
        print(f"   兼容性: {compatibility['compatible']}")
        print(f"   消息: {compatibility['message']}")
        print()
        
        # 测试健康检查
        print("3. 健康检查:")
        health = await health_check()
        print(f"   状态: {health['status']}")
        print(f"   配置有效: {health['config_valid']}")
        print(f"   消息: {health['message']}")
        print()
        
        # 测试插件创建
        print("4. 插件创建测试:")
        try:
            plugin = create_plugin()
            print(f"   插件类型: {type(plugin).__name__}")
            print(f"   插件启用状态: {plugin.enabled}")
            print(f"   API URL: {plugin.api_url}")
            print("   插件创建成功!")
        except Exception as e:
            print(f"   插件创建失败: {str(e)}")
        print()
        
        print("测试完成!")

    asyncio.run(test_init())