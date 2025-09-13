"""Anthropic模型服务商插件

该插件提供Claude系列大语言模型的价格和信息查询功能。
支持的模型包括Claude-4-Sonnet和Claude-3.5-Sonnet等。
"""

from .plugin import AnthropicPlugin

__version__ = "1.0.0"
__author__ = "PricNicker Team"
__description__ = "Anthropic模型服务商插件"

# 插件入口点
PluginClass = AnthropicPlugin

__all__ = ["AnthropicPlugin", "PluginClass"]