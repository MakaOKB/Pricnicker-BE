from abc import ABC, abstractmethod
from typing import List
from ..models import ModelInfo


class BaseModelHandler(ABC):
    """模型服务商Handler基类
    
    所有模型服务商的Handler都应该继承此基类，
    并实现get_models方法来获取该服务商的模型列表。
    """
    
    def __init__(self, brand_name: str):
        """初始化Handler
        
        Args:
            brand_name: 服务商品牌名称
        """
        self.brand_name = brand_name
    
    @abstractmethod
    async def get_models(self) -> List[ModelInfo]:
        """获取该服务商的模型列表
        
        Returns:
            List[ModelInfo]: 模型信息列表
        """
        pass
    
    @abstractmethod
    def get_brand_name(self) -> str:
        """获取服务商品牌名称
        
        Returns:
            str: 品牌名称
        """
        return self.brand_name