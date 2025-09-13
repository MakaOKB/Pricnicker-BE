"""ZenMux模型服务商插件

该插件提供ZenMux平台上各种大语言模型的价格和信息查询功能。
支持多个品牌的模型，包括OpenAI、Anthropic、Google等。
"""

from .plugin import ZenMuxPlugin

__version__ = "1.0.0"
__author__ = "PricNicker Team"
__description__ = "ZenMux模型服务商插件"

# 插件入口点
PluginClass = ZenmuxPlugin

__all__ = ["ZenmuxPlugin", "PluginClass"]