import os
import sys
import json
import importlib.util
from typing import List, Dict, Optional, Type
from pathlib import Path
from .base import BasePlugin, PluginConfig
from ..models import ModelInfo


class PluginLoader:
    """插件加载器
    
    负责动态加载和管理模型提供商插件
    """
    
    def __init__(self, plugins_dir: str = "app/plugins"):
        """初始化插件加载器
        
        Args:
            plugins_dir: 插件目录路径
        """
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, PluginConfig] = {}
    
    def discover_plugins(self) -> List[PluginConfig]:
        """发现可用的插件
        
        Returns:
            List[PluginConfig]: 插件配置对象列表
        """
        plugin_configs = []
        
        if not self.plugins_dir.exists():
            return plugin_configs
        
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                # 检查是否包含必要的文件
                config_file = item / "config.json"
                plugin_file = item / "plugin.py"
                
                if config_file.exists() and plugin_file.exists():
                    config = self.load_plugin_config(item.name)
                    if config:
                        plugin_configs.append(config)
        
        return plugin_configs
    
    def load_plugin_config(self, plugin_name: str) -> Optional[PluginConfig]:
        """加载插件配置
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[PluginConfig]: 插件配置对象，加载失败返回None
        """
        try:
            config_path = self.plugins_dir / plugin_name / "config.json"
            
            if not config_path.exists():
                print(f"Config file not found for plugin: {plugin_name}")
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return PluginConfig(**config_data)
        
        except Exception as e:
            print(f"Failed to load config for plugin {plugin_name}: {e}")
            return None
    
    def load_plugin_class(self, plugin_name: str) -> Optional[Type[BasePlugin]]:
        """动态加载插件类
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Type[BasePlugin]]: 插件类，加载失败返回None
        """
        try:
            plugin_path = self.plugins_dir / plugin_name / "plugin.py"
            
            if not plugin_path.exists():
                print(f"Plugin file not found: {plugin_path}")
                return None
            
            # 动态导入模块
            module_name = f"app.plugins.{plugin_name}.plugin"
            spec = importlib.util.spec_from_file_location(
                module_name, plugin_path
            )
            
            if spec is None or spec.loader is None:
                print(f"Failed to create spec for plugin: {plugin_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # 设置模块的包路径以支持相对导入
            module.__package__ = f"app.plugins.{plugin_name}"
            
            # 将模块添加到sys.modules中
            sys.modules[module_name] = module
            
            spec.loader.exec_module(module)
            
            # 查找插件类（约定：类名为 {PluginName}Plugin）
            plugin_class_name = f"{plugin_name.title()}Plugin"
            
            if hasattr(module, plugin_class_name):
                plugin_class = getattr(module, plugin_class_name)
                
                # 验证是否继承自BasePlugin
                if issubclass(plugin_class, BasePlugin):
                    return plugin_class
                else:
                    print(f"Plugin class {plugin_class_name} does not inherit from BasePlugin")
            else:
                print(f"Plugin class {plugin_class_name} not found in {plugin_name}")
            
            return None
        
        except Exception as e:
            print(f"Failed to load plugin class {plugin_name}: {e}")
            return None
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """加载单个插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 加载是否成功
        """
        try:
            # 加载配置
            config = self.load_plugin_config(plugin_name)
            if config is None:
                return False
            
            # 检查插件是否启用
            if not config.enabled:
                print(f"Plugin {plugin_name} is disabled")
                return False
            
            # 加载插件类
            plugin_class = self.load_plugin_class(plugin_name)
            if plugin_class is None:
                return False
            
            # 创建插件实例
            plugin_instance = plugin_class(config)
            
            # 初始化插件
            if await plugin_instance.initialize():
                self.loaded_plugins[plugin_name] = plugin_instance
                self.plugin_configs[plugin_name] = config
                print(f"Successfully loaded plugin: {plugin_name}")
                return True
            else:
                print(f"Failed to initialize plugin: {plugin_name}")
                return False
        
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    async def load_all_plugins(self) -> Dict[str, bool]:
        """加载所有可用插件
        
        Returns:
            Dict[str, bool]: 插件名称到加载结果的映射
        """
        results = {}
        plugin_configs = self.discover_plugins()
        
        plugin_names = [config.name for config in plugin_configs]
        print(f"Discovered {len(plugin_names)} plugins: {plugin_names}")
        
        for plugin_name in plugin_names:
            results[plugin_name] = await self.load_plugin(plugin_name)
        
        print(f"Successfully loaded {sum(results.values())} out of {len(plugin_names)} plugins")
        return results
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        try:
            if plugin_name in self.loaded_plugins:
                plugin = self.loaded_plugins[plugin_name]
                await plugin.cleanup()
                del self.loaded_plugins[plugin_name]
                del self.plugin_configs[plugin_name]
                print(f"Successfully unloaded plugin: {plugin_name}")
                return True
            else:
                print(f"Plugin {plugin_name} is not loaded")
                return False
        
        except Exception as e:
            print(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def get_loaded_plugins(self) -> Dict[str, BasePlugin]:
        """获取已加载的插件
        
        Returns:
            Dict[str, BasePlugin]: 已加载的插件字典
        """
        return self.loaded_plugins.copy()
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict]:
        """获取插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Dict]: 插件信息，未找到返回None
        """
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name].get_plugin_info()
        return None
    
    async def get_all_models(self) -> List[ModelInfo]:
        """获取所有插件的模型列表
        
        Returns:
            List[ModelInfo]: 所有模型信息的合并列表
        """
        all_models = []
        
        for plugin_name, plugin in self.loaded_plugins.items():
            try:
                if plugin.enabled:
                    models = await plugin.get_models()
                    all_models.extend(models)
            except Exception as e:
                print(f"Error getting models from plugin {plugin_name}: {e}")
                continue
        
        return all_models