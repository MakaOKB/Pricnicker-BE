from typing import List
from ..base import BasePlugin, PluginConfig
from ...models import ModelInfo, TokenInfo


class DeepseekPlugin(BasePlugin):
    """DeepSeek模型服务商插件
    
    提供DeepSeek系列模型的信息和价格数据
    """
    
    def __init__(self, config: PluginConfig):
        """初始化DeepSeek插件
        
        Args:
            config: 插件配置对象
        """
        super().__init__(config)
        self.supported_models = config.extra_config.get('supported_models', [])
        self.default_currency = config.extra_config.get('default_currency', 'CNY')
    
    async def validate_config(self) -> bool:
        """验证插件配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查必要的配置项
            if not self.config.brand_name:
                print("DeepSeek plugin: brand_name is required")
                return False
            
            if not self.supported_models:
                print("DeepSeek plugin: supported_models is required in extra_config")
                return False
            
            # 可以在这里添加更多的配置验证逻辑
            # 例如：API密钥验证、网络连接测试等
            
            return True
        
        except Exception as e:
            print(f"DeepSeek plugin config validation failed: {e}")
            return False
    
    async def get_models(self) -> List[ModelInfo]:
        """获取DeepSeek模型列表
        
        Returns:
            List[ModelInfo]: DeepSeek模型信息列表
            
        Raises:
            Exception: 当获取模型信息失败时抛出异常
        """
        try:
            # 在实际应用中，这里可能会调用DeepSeek的API来获取最新的模型信息和价格
            # 目前使用静态数据作为示例
            
            models = [
                ModelInfo(
                    brand=self.config.brand_name,
                    name="DeepSeek-V3.1",
                    data_amount=671,
                    window=160000,
                    tokens=TokenInfo(
                        input=4.0,
                        output=12.0,
                        unit=self.default_currency
                    )
                ),
                ModelInfo(
                    brand=self.config.brand_name,
                    name="DeepSeek-V2.5",
                    data_amount=500,
                    window=128000,
                    tokens=TokenInfo(
                        input=3.0,
                        output=10.0,
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
            print(f"DeepSeek plugin: Failed to get models - {e}")
            raise Exception(f"Failed to retrieve DeepSeek models: {e}")
    
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
                    "window_size": model.window
                }
        
        raise ValueError(f"Model {model_name} not found in DeepSeek plugin")
    
    async def cleanup(self):
        """清理插件资源
        
        在插件卸载时调用，用于清理资源
        """
        # 在这里可以添加清理逻辑，例如：
        # - 关闭API连接
        # - 清理缓存
        # - 保存状态等
        print(f"DeepSeek plugin cleanup completed")