from typing import List, Dict, Optional
from .models import ModelInfo
from .plugins.loader import PluginLoader
from .plugins.base import BasePlugin


class ModelService:
    """模型服务管理器
    
    负责管理所有模型服务商的插件，
    并提供统一的接口来获取所有模型信息。
    """
    
    def __init__(self, plugins_dir: str = "app/plugins"):
        """初始化模型服务管理器
        
        Args:
            plugins_dir: 插件目录路径
        """
        self.plugin_loader = PluginLoader(plugins_dir)
        self.plugins: Dict[str, BasePlugin] = {}
        
        # 插件将在首次使用时加载
        self._plugins_loaded = False
    
    async def _load_all_plugins(self):
        """加载所有可用的插件"""
        try:
            plugin_configs = self.plugin_loader.discover_plugins()
            
            for config in plugin_configs:
                if config.enabled:
                    try:
                        success = await self.plugin_loader.load_plugin(config.name)
                        if success:
                            plugin = self.plugin_loader.loaded_plugins.get(config.name)
                            if plugin:
                                self.plugins[config.name] = plugin
                                print(f"Successfully loaded plugin: {config.name}")
                    except Exception as e:
                        print(f"Failed to load plugin {config.name}: {e}")
        
        except Exception as e:
            print(f"Error discovering plugins: {e}")
    
    async def _ensure_plugins_loaded(self):
        """确保插件已加载"""
        if not self._plugins_loaded:
            await self._load_all_plugins()
            self._plugins_loaded = True
    
    async def get_all_models(self) -> List[ModelInfo]:
        """获取所有服务商的模型列表
        
        Returns:
            List[ModelInfo]: 所有模型信息的合并列表
        """
        # 确保插件已加载
        await self._ensure_plugins_loaded()
        
        all_models = []
        
        # 遍历所有插件，获取模型信息
        for plugin_name, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
                
            try:
                models = await plugin.get_models()
                all_models.extend(models)
            except Exception as e:
                # 记录错误但不中断其他插件的执行
                print(f"Error getting models from plugin {plugin_name}: {e}")
                continue
        
        return all_models
    
    async def get_brands(self) -> List[str]:
        """获取所有可用的品牌列表
        
        Returns:
            List[str]: 品牌名称列表
        """
        # 确保插件已加载
        await self._ensure_plugins_loaded()
        
        brands = set()
        
        for plugin_name, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
                
            try:
                models = await plugin.get_models()
                for model in models:
                    brands.add(model.brand)
            except Exception as e:
                print(f"Error getting brands from plugin {plugin_name}: {e}")
                continue
        
        return sorted(list(brands))
    
    async def get_models_by_brand(self, brand: str) -> List[ModelInfo]:
        """根据品牌获取模型列表
        
        Args:
            brand: 品牌名称
            
        Returns:
            List[ModelInfo]: 指定品牌的模型列表
        """
        # 确保插件已加载
        await self._ensure_plugins_loaded()
        
        models = []
        
        for plugin_name, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
                
            try:
                plugin_models = await plugin.get_models()
                models.extend([m for m in plugin_models if m.brand == brand])
            except Exception as e:
                print(f"Error getting models from plugin {plugin_name}: {e}")
                continue
        
        return models
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取指定的插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[BasePlugin]: 插件实例，如果不存在则返回None
        """
        return self.plugins.get(plugin_name)
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功启用
        """
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.enable()
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功禁用
        """
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.disable()
            return True
        return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功重新加载
        """
        try:
            # 卸载现有插件
            if plugin_name in self.plugins:
                await self.plugins[plugin_name].cleanup()
                del self.plugins[plugin_name]
            
            # 重新加载插件
            plugin = self.plugin_loader.load_plugin(plugin_name)
            if plugin:
                self.plugins[plugin_name] = plugin
                return True
        
        except Exception as e:
            print(f"Error reloading plugin {plugin_name}: {e}")
        
        return False
    
    def get_plugin_status(self) -> Dict[str, dict]:
        """获取所有插件的状态信息
        
        Returns:
            Dict[str, dict]: 插件状态信息字典
        """
        status = {}
        
        for plugin_name, plugin in self.plugins.items():
            status[plugin_name] = {
                "name": plugin.config.name,
                "version": plugin.config.version,
                "brand": plugin.config.brand_name,
                "enabled": plugin.enabled,
                "description": plugin.config.description
            }
        
        return status