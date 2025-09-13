#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMXAPI 插件包初始化文件

该文件定义了 DMXAPI 插件的入口点和导出接口。
插件提供从 DMXAPI 获取AI模型价格信息的功能。

主要功能:
- 导出插件主类 DmxPlugin
- 定义插件元数据信息
- 提供插件版本和描述信息
- 支持插件的动态加载和初始化

作者: PricNicker Team
版本: 1.0.0
最后更新: 2025-01-13
"""

from .plugin import DmxPlugin

# 插件元数据
__version__ = "1.0.0"
__author__ = "PricNicker Team"
__description__ = "DMXAPI模型价格爬虫插件"
__plugin_name__ = "dmx"
__brand_name__ = "DMXAPI"

# 导出的公共接口
__all__ = [
    'DmxPlugin',
    '__version__',
    '__author__',
    '__description__',
    '__plugin_name__',
    '__brand_name__'
]

# 插件工厂函数
def create_plugin(config=None):
    """
    创建 DMXAPI 插件实例
    
    Args:
        config: 插件配置对象，可选
        
    Returns:
        DmxPlugin: 插件实例
    """
    return DmxPlugin(config)

# 获取插件信息的便捷函数
def get_plugin_info():
    """
    获取插件基本信息
    
    Returns:
        dict: 包含插件信息的字典
    """
    return {
        'name': __plugin_name__,
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'brand_name': __brand_name__,
        'plugin_class': 'DmxPlugin',
        'api_endpoint': 'https://www.dmxapi.cn/api/pricing',
        'supported_brands': [
            'OpenAI', 'Anthropic', 'Google', 'DeepSeek', 'Qwen',
            'GLM', 'Doubao', 'ERNIE', 'Hunyuan', 'Moonshot',
            'MiniMax', 'Baichuan', 'iFLYTEK'
        ]
    }

# 插件健康检查函数
async def health_check():
    """
    检查插件是否可以正常工作
    
    Returns:
        dict: 健康检查结果
    """
    try:
        # 创建一个简单的配置对象
        from dataclasses import dataclass
        
        @dataclass
        class SimpleConfig:
            name: str = "dmx"
            version: str = "1.0.0"
            description: str = "DMXAPI模型价格爬虫插件"
            author: str = "PricNicker Team"
            brand_name: str = "DMXAPI"
            enabled: bool = True
        
        plugin = create_plugin(SimpleConfig())
        is_valid = await plugin.validate_config()
        
        return {
            'status': 'healthy' if is_valid else 'unhealthy',
            'plugin': __plugin_name__,
            'version': __version__,
            'config_valid': is_valid,
            'message': 'Plugin is working properly' if is_valid else 'Plugin configuration validation failed'
        }
    except Exception as e:
        return {
            'status': 'error',
            'plugin': __plugin_name__,
            'version': __version__,
            'config_valid': False,
            'message': f'Health check failed: {str(e)}'
        }

# 插件兼容性检查
def check_compatibility():
    """
    检查插件与当前环境的兼容性
    
    Returns:
        dict: 兼容性检查结果
    """
    import sys
    import requests
    
    requirements = {
        'python_version': '3.7+',
        'required_packages': ['requests', 'asyncio']
    }
    
    compatibility = {
        'compatible': True,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'requirements': requirements,
        'issues': []
    }
    
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        compatibility['compatible'] = False
        compatibility['issues'].append('Python version must be 3.7 or higher')
    
    # 检查必需的包
    try:
        import requests
        import asyncio
    except ImportError as e:
        compatibility['compatible'] = False
        compatibility['issues'].append(f'Missing required package: {str(e)}')
    
    return compatibility

if __name__ == "__main__":
    # 测试插件初始化
    import asyncio
    
    async def test_init():
        """测试插件初始化和基本功能"""
        print(f"DMXAPI 插件测试 v{__version__}")
        print("=" * 50)
        
        # 显示插件信息
        print("\n=== 插件信息 ===")
        info = get_plugin_info()
        for key, value in info.items():
            if key == 'supported_brands':
                print(f"{key}: {', '.join(value)}")
            else:
                print(f"{key}: {value}")
        
        # 兼容性检查
        print("\n=== 兼容性检查 ===")
        compat = check_compatibility()
        print(f"兼容性: {'通过' if compat['compatible'] else '失败'}")
        print(f"Python版本: {compat['python_version']}")
        if compat['issues']:
            print("问题:")
            for issue in compat['issues']:
                print(f"  - {issue}")
        
        # 健康检查
        print("\n=== 健康检查 ===")
        health = await health_check()
        print(f"状态: {health['status']}")
        print(f"配置有效: {health['config_valid']}")
        print(f"消息: {health['message']}")
        
        # 创建插件实例测试
        print("\n=== 插件实例测试 ===")
        try:
            plugin = create_plugin()
            print(f"插件实例创建成功: {type(plugin).__name__}")
            
            # 获取品牌列表
            brands = plugin.get_brands()
            print(f"支持的品牌数量: {len(brands)}")
            
            # 获取插件信息
            plugin_info = plugin.get_plugin_info()
            print(f"插件名称: {plugin_info['name']}")
            print(f"插件版本: {plugin_info['version']}")
            
        except Exception as e:
            print(f"插件实例创建失败: {e}")
        
        print("\n测试完成!")
    
    # 运行测试
    asyncio.run(test_init())