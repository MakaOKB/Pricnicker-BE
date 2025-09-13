from typing import List
from .base import BaseModelHandler
from ..models import ModelInfo, TokenInfo


class DeepSeekHandler(BaseModelHandler):
    """DeepSeek模型服务商Handler
    
    提供DeepSeek系列模型的信息和价格数据
    """
    
    def __init__(self):
        super().__init__("DeepSeek")
    
    async def get_models(self) -> List[ModelInfo]:
        """获取DeepSeek模型列表
        
        Returns:
            List[ModelInfo]: DeepSeek模型信息列表
        """
        models = [
            ModelInfo(
                brand="DeepSeek",
                name="DeepSeek-V3.1",
                data_amount=671,
                window=160000,
                tokens=TokenInfo(
                    input=4.0,
                    output=12.0,
                    unit="CNY"
                )
            ),
            ModelInfo(
                brand="DeepSeek",
                name="DeepSeek-V2.5",
                data_amount=500,
                window=128000,
                tokens=TokenInfo(
                    input=3.0,
                    output=10.0,
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