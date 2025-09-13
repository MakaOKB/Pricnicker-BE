from typing import List
from .base import BaseModelHandler
from ..models import ModelInfo, TokenInfo


class AnthropicHandler(BaseModelHandler):
    """Anthropic模型服务商Handler
    
    提供Anthropic Claude系列模型的信息和价格数据
    """
    
    def __init__(self):
        super().__init__("Anthropic")
    
    async def get_models(self) -> List[ModelInfo]:
        """获取Anthropic模型列表
        
        Returns:
            List[ModelInfo]: Anthropic模型信息列表
        """
        models = [
            ModelInfo(
                brand="Anthropic",
                name="Claude-4-Sonnet",
                data_amount=None,
                window=1000000,
                tokens=TokenInfo(
                    input=3.3,
                    output=16,
                    unit="CNY"
                )
            ),
            ModelInfo(
                brand="Anthropic",
                name="Claude-3.5-Sonnet",
                data_amount=None,
                window=200000,
                tokens=TokenInfo(
                    input=2.5,
                    output=12,
                    unit="CNY"
                )
            )
        ]
        return models
    
    def get_brand_name(self) -> str:
        """获取品牌名称
        
        Returns:
            str: 品牌名称
        """
        return self.brand_name