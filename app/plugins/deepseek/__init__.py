"""DeepSeek模型服务商插件

该插件提供DeepSeek系列大语言模型的价格和信息查询功能。
支持的模型包括DeepSeek-V3.1和DeepSeek-V2.5等。
"""

from .plugin import DeepseekPlugin

__version__ = "1.0.0"
__author__ = "PricNicker Team"
__description__ = "DeepSeek模型服务商插件"

# 插件入口点
PluginClass = DeepseekPlugin

__all__ = ["DeepseekPlugin", "PluginClass"]