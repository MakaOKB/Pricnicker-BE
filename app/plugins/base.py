from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..models import ModelInfo


class PluginConfig(BaseModel):
    """插件配置模型
    
    定义插件的基本配置信息和元数据
    """
    name: str  # 插件名称
    version: str  # 插件版本
    description: str  # 插件描述
    author: str  # 插件作者
    brand_name: str  # 服务商品牌名称
    enabled: bool = True  # 是否启用插件
    api_key_required: bool = False  # 是否需要API密钥
    base_url: Optional[str] = None  # API基础URL
    timeout: int = 30  # 请求超时时间（秒）
    rate_limit: Optional[int] = None  # 速率限制（每分钟请求数）
    extra_config: Dict[str, Any] = {}  # 额外配置参数


class BasePlugin(ABC):
    """插件基类
    
    所有模型提供商插件都应该继承此基类，
    并实现相应的抽象方法来提供模型信息和服务。
    """
    
    def __init__(self, config: PluginConfig):
        """初始化插件
        
        Args:
            config: 插件配置对象
        """
        self.config = config
        self.enabled = config.enabled
    
    @abstractmethod
    async def get_models(self) -> List[ModelInfo]:
        """获取该服务商的模型列表
        
        Returns:
            List[ModelInfo]: 模型信息列表
            
        Raises:
            Exception: 当获取模型信息失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """验证插件配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        pass
    
    async def initialize(self) -> bool:
        """初始化插件
        
        在插件加载时调用，用于执行必要的初始化操作
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            return await self.validate_config()
        except Exception as e:
            print(f"Plugin {self.config.name} initialization failed: {e}")
            return False
    
    async def cleanup(self):
        """清理插件资源
        
        在插件卸载时调用，用于清理资源
        """
        pass
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """获取插件信息
        
        Returns:
            Dict[str, Any]: 插件基本信息
        """
        return {
            "name": self.config.name,
            "version": self.config.version,
            "description": self.config.description,
            "author": self.config.author,
            "brand_name": self.config.brand_name,
            "enabled": self.enabled
        }
    
    def enable(self):
        """启用插件"""
        self.enabled = True
        self.config.enabled = True
    
    def disable(self):
        """禁用插件"""
        self.enabled = False
        self.config.enabled = False