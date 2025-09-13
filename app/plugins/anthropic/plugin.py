from typing import List
from ..base import BasePlugin, PluginConfig
from ...models import ModelInfo, TokenInfo


class AnthropicPlugin(BasePlugin):
    """Anthropic模型服务商插件
    
    提供Claude系列模型的信息和价格数据
    """
    
    def __init__(self, config: PluginConfig):
        """初始化Anthropic插件
        
        Args:
            config: 插件配置对象
        """
        super().__init__(config)
        self.supported_models = config.extra_config.get('supported_models', [])
        self.default_currency = config.extra_config.get('default_currency', 'USD')
        self.api_version = config.extra_config.get('api_version', '2023-06-01')
    
    async def validate_config(self) -> bool:
        """验证插件配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查必要的配置项
            if not self.config.brand_name:
                print("Anthropic plugin: brand_name is required")
                return False
            
            if not self.supported_models:
                print("Anthropic plugin: supported_models is required in extra_config")
                return False
            
            # 检查API密钥要求
            if self.config.api_key_required:
                # 在实际应用中，这里应该检查环境变量或配置中的API密钥
                # api_key = os.getenv('ANTHROPIC_API_KEY')
                # if not api_key:
                #     print("Anthropic plugin: API key is required but not found")
                #     return False
                pass
            
            # 可以在这里添加更多的配置验证逻辑
            # 例如：API密钥验证、网络连接测试等
            
            return True
        
        except Exception as e:
            print(f"Anthropic plugin config validation failed: {e}")
            return False
    
    async def get_models(self) -> List[ModelInfo]:
        """获取Anthropic模型列表
        
        Returns:
            List[ModelInfo]: Anthropic模型信息列表
            
        Raises:
            Exception: 当获取模型信息失败时抛出异常
        """
        try:
            # 在实际应用中，这里可能会调用Anthropic的API来获取最新的模型信息和价格
            # 目前使用静态数据作为示例
            
            models = [
                ModelInfo(
                    brand=self.config.brand_name,
                    name="Claude-4-Sonnet",
                    data_amount=None,  # Anthropic通常不公开训练数据量
                    window=200000,
                    tokens=TokenInfo(
                        input=3.0,
                        output=15.0,
                        unit=self.default_currency
                    )
                ),
                ModelInfo(
                    brand=self.config.brand_name,
                    name="Claude-3.5-Sonnet",
                    data_amount=None,
                    window=200000,
                    tokens=TokenInfo(
                        input=3.0,
                        output=15.0,
                        unit=self.default_currency
                    )
                )
            ]
            
            # 过滤只返回配置中支持的模型
            filtered_models = [
                model for model in models 
                if model.name in self.supported_models
            ]
            
            return filtered_models
        
        except Exception as e:
            print(f"Anthropic plugin: Failed to get models - {e}")
            raise Exception(f"Failed to retrieve Anthropic models: {e}")
    
    async def get_model_pricing(self, model_name: str) -> dict:
        """获取特定模型的价格信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            dict: 价格信息字典
        """
        models = await self.get_models()
        
        for model in models:
            if model.name == model_name:
                return {
                    "model_name": model.name,
                    "input_price": model.tokens.input,
                    "output_price": model.tokens.output,
                    "currency": model.tokens.unit,
                    "window_size": model.window,
                    "api_version": self.api_version
                }
        
        raise ValueError(f"Model {model_name} not found in Anthropic plugin")
    
    async def health_check(self) -> dict:
        """检查插件健康状态
        
        Returns:
            dict: 健康状态信息
        """
        try:
            # 在实际应用中，这里可以调用Anthropic API进行健康检查
            # 目前返回基本的状态信息
            
            models = await self.get_models()
            
            return {
                "status": "healthy",
                "plugin_name": self.config.name,
                "brand": self.config.brand_name,
                "models_count": len(models),
                "enabled": self.is_enabled,
                "api_version": self.api_version
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "plugin_name": self.config.name,
                "error": str(e)
            }
    
    async def cleanup(self):
        """清理插件资源
        
        在插件卸载时调用，用于清理资源
        """
        # 在这里可以添加清理逻辑，例如：
        # - 关闭API连接
        # - 清理缓存
        # - 保存状态等
        print(f"Anthropic plugin cleanup completed")