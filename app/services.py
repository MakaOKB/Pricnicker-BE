from typing import List, Dict, Optional, Tuple
from .models import ModelInfo, ProviderInfo
from .plugins.loader import PluginLoader
from .plugins.base import BasePlugin
import difflib
from collections import defaultdict


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
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """计算两个模型名称的相似度
        
        Args:
            name1: 第一个模型名称
            name2: 第二个模型名称
            
        Returns:
            float: 相似度百分比 (0-100)
        """
        # 使用 difflib.SequenceMatcher 计算相似度
        matcher = difflib.SequenceMatcher(None, name1.lower(), name2.lower())
        return matcher.ratio() * 100
    
    def _merge_similar_models(self, models: List[ModelInfo], similarity_threshold: float = 75.0) -> List[ModelInfo]:
        """合并相似的模型
        
        Args:
            models: 原始模型列表
            similarity_threshold: 相似度阈值（默认75%）
            
        Returns:
            List[ModelInfo]: 合并后的模型列表
        """
        if not models:
            return models
        
        # 按模型名称分组，相似的模型会被分到同一组
        model_groups = defaultdict(list)
        processed_indices = set()
        
        for i, model in enumerate(models):
            if i in processed_indices:
                continue
                
            # 创建新组，以当前模型为基准
            group_key = model.name
            model_groups[group_key].append(model)
            processed_indices.add(i)
            
            # 查找相似的模型
            for j, other_model in enumerate(models[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                    
                similarity = self._calculate_similarity(model.name, other_model.name)
                if similarity >= similarity_threshold:
                    # 使用靠后出现的模型名称作为标准名称
                    if j > i:  # other_model 出现在后面
                        # 更新组键为靠后的模型名称
                        if group_key != other_model.name:
                            # 将现有模型移动到新的组键下
                            model_groups[other_model.name].extend(model_groups[group_key])
                            del model_groups[group_key]
                            group_key = other_model.name
                    
                    model_groups[group_key].append(other_model)
                    processed_indices.add(j)
        
        # 合并每组中的模型数据
        merged_models = []
        for standard_name, group_models in model_groups.items():
            if not group_models:
                continue
                
            # 使用标准名称（靠后出现的）作为合并后的模型名称
            merged_model = self._merge_model_group(standard_name, group_models)
            merged_models.append(merged_model)
        
        return merged_models
    
    def _merge_model_group(self, standard_name: str, models: List[ModelInfo]) -> ModelInfo:
        """合并一组相似的模型
        
        Args:
            standard_name: 标准模型名称
            models: 要合并的模型列表
            
        Returns:
            ModelInfo: 合并后的模型信息
        """
        if not models:
            raise ValueError("模型列表不能为空")
        
        if len(models) == 1:
            # 只有一个模型，直接返回但使用标准名称
            model = models[0]
            model.name = standard_name
            return model
        
        # 合并多个模型的数据
        # 使用第一个模型作为基础
        base_model = models[0]
        
        # 收集所有提供商信息 - 保持每个模型的每个提供商独立
        all_providers = []
        provider_keys = set()  # 使用更复杂的键来区分同一提供商的不同报价
        
        for model_idx, model in enumerate(models):
            if hasattr(model, 'providers') and model.providers:
                for provider in model.providers:
                    # 创建唯一键：提供商名称 + 模型索引 + 价格信息
                    price_key = f"{provider.tokens.input}_{provider.tokens.output}_{provider.tokens.unit}"
                    unique_key = f"{provider.name}_{model_idx}_{price_key}"
                    
                    if unique_key not in provider_keys:
                        # 创建新的提供商信息，包含原始模型名称信息
                        from .models import TokenInfo
                        provider_tokens = TokenInfo(
                            input=provider.tokens.input,
                            output=provider.tokens.output,
                            unit=provider.tokens.unit
                        )
                        
                        provider_info = ProviderInfo(
                            name=provider.name,
                            display_name=f"{provider.display_name} ({model.name})",  # 在显示名称中包含原始模型名
                            api_website=provider.api_website,
                            full_name=f"{provider.name}/{model.name.lower().replace(' ', '-')}",
                            tokens=provider_tokens
                        )
                        all_providers.append(provider_info)
                        provider_keys.add(unique_key)
            
            # 如果模型有推荐提供商信息，也要保留
            if hasattr(model, 'recommended_provider') and model.recommended_provider:
                unique_key = f"{model.recommended_provider}_{model_idx}_recommended"
                if unique_key not in provider_keys:
                    # 创建一个基本的提供商信息
                    from .models import TokenInfo
                    
                    # 如果模型有直接的价格信息，使用它们
                    input_price = getattr(model, 'input_price', 0.0) if hasattr(model, 'input_price') else 0.0
                    output_price = getattr(model, 'output_price', 0.0) if hasattr(model, 'output_price') else 0.0
                    
                    default_tokens = TokenInfo(input=input_price, output=output_price, unit='USD')
                    provider_info = ProviderInfo(
                        name=model.recommended_provider,
                        display_name=f"{model.recommended_provider} ({model.name})",
                        api_website='',
                        full_name=f"{model.recommended_provider}/{model.name.lower().replace(' ', '-')}",
                        tokens=default_tokens
                    )
                    all_providers.append(provider_info)
                    provider_keys.add(unique_key)
        
        # 选择最大的上下文窗口（兼容不同字段名）
        windows = []
        for model in models:
            if hasattr(model, 'window'):
                windows.append(model.window)
            elif hasattr(model, 'context_window'):
                windows.append(model.context_window)
            else:
                windows.append(4096)  # 默认值
        max_window = max(windows) if windows else 4096
        
        # 选择最新的品牌信息（通常靠后的更准确）
        brand = models[-1].brand
        
        # 合并数据量信息（取最大值）
        data_amounts = [getattr(model, 'data_amount', None) for model in models if getattr(model, 'data_amount', None) is not None]
        max_data_amount = max(data_amounts) if data_amounts else None
        
        # 注意：现在每个模型的提供商信息都已经独立保存，不需要创建默认提供商
        
        # 创建合并后的模型
        merged_model = ModelInfo(
            name=standard_name,
            brand=brand,
            data_amount=max_data_amount,
            window=max_window,
            providers=all_providers,
            recommended_provider=models[-1].recommended_provider if hasattr(models[-1], 'recommended_provider') else None
        )
        
        # 保留原模型的额外字段（除了价格相关字段，因为价格信息现在通过providers管理）
        if hasattr(models[-1], 'context_window'):
            merged_model.context_window = max_window
        if hasattr(models[-1], 'description'):
            merged_model.description = getattr(models[-1], 'description', '')
        if hasattr(models[-1], 'extra_info'):
            merged_model.extra_info = getattr(models[-1], 'extra_info', {})
        
        return merged_model
    
    async def get_all_models(self, enable_fuzzy_matching: bool = True) -> List[ModelInfo]:
        """获取所有服务商的模型列表
        
        Args:
            enable_fuzzy_matching: 是否启用模糊匹配功能（默认启用）
        
        Returns:
            List[ModelInfo]: 所有模型信息的合并列表（包含提供商信息）
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
                # 直接使用插件返回的模型信息，不覆盖价格数据
                for model in models:
                    model.recommended_provider = plugin_name
                
                all_models.extend(models)
            except Exception as e:
                # 记录错误但不中断其他插件的执行
                print(f"Error getting models from plugin {plugin_name}: {e}")
                continue
        
        # 应用模糊匹配逻辑
        if enable_fuzzy_matching and all_models:
            print(f"应用模糊匹配前: {len(all_models)} 个模型")
            all_models = self._merge_similar_models(all_models)
            print(f"应用模糊匹配后: {len(all_models)} 个模型")
        
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
    
    async def get_all_providers(self) -> List[ProviderInfo]:
        """获取所有服务提供商信息
        
        Returns:
            List[ProviderInfo]: 所有提供商的信息列表
        """
        await self._ensure_plugins_loaded()
        
        providers = []
        for plugin_name, plugin in self.plugins.items():
            if plugin.enabled:
                try:
                    # 从插件配置中读取提供商信息
                    config_path = self.plugin_loader.plugins_dir / plugin_name / "config.json"
                    if config_path.exists():
                        import json
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        if 'provider_info' in config:
                            provider_data = config['provider_info']
                            # 从配置中获取tokens信息
                            from .models import TokenInfo
                            tokens_data = provider_data.get('tokens', {'input': 0.0, 'output': 0.0, 'unit': 'CNY'})
                            tokens = TokenInfo(
                                input=tokens_data.get('input', 0.0),
                                output=tokens_data.get('output', 0.0),
                                unit=tokens_data.get('unit', 'CNY')
                            )
                            provider_info = ProviderInfo(
                                name=plugin_name,
                                display_name=provider_data.get('display_name', config.get('brand_name', plugin_name)),
                                api_website=provider_data.get('api_website', config.get('base_url', '')),
                                full_name=f"{plugin_name}/default",
                                tokens=tokens
                            )
                            providers.append(provider_info)
                        else:
                            # 如果没有provider_info配置，使用默认值
                            from .models import TokenInfo
                            default_tokens = TokenInfo(input=0.0, output=0.0, unit='CNY')
                            provider_info = ProviderInfo(
                                name=plugin_name,
                                display_name=plugin.config.brand_name,
                                api_website=getattr(plugin.config, 'base_url', ''),
                                full_name=f"{plugin_name}/default",
                                tokens=default_tokens
                            )
                            providers.append(provider_info)
                    else:
                        # 配置文件不存在时使用默认值
                        from .models import TokenInfo
                        default_tokens = TokenInfo(input=0.0, output=0.0, unit='CNY')
                        provider_info = ProviderInfo(
                            name=plugin_name,
                            display_name=plugin.config.brand_name,
                            api_website=getattr(plugin.config, 'base_url', ''),
                            full_name=f"{plugin_name}/default",
                            tokens=default_tokens
                        )
                        providers.append(provider_info)
                except Exception as e:
                    print(f"Error loading provider info for {plugin_name}: {e}")
                    continue
        
        return providers
    
    async def get_provider_by_name(self, provider_name: str) -> Optional[ProviderInfo]:
        """根据名称获取提供商信息
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            Optional[ProviderInfo]: 提供商信息，如果不存在则返回None
        """
        await self._ensure_plugins_loaded()
        
        plugin = self.plugins.get(provider_name)
        if not plugin or not plugin.enabled:
            return None
        
        # 尝试从插件的实际模型数据中获取价格信息
        try:
            models = await plugin.get_models()
            if models and len(models) > 0:
                # 使用第一个模型的价格信息作为提供商的默认价格
                first_model = models[0]
                if first_model.providers and len(first_model.providers) > 0:
                    provider_info = first_model.providers[0]
                    return ProviderInfo(
                        name=provider_name,
                        display_name=provider_info.display_name,
                        api_website=provider_info.api_website,
                        full_name=f"{provider_name}/default",
                        tokens=provider_info.tokens
                    )
        except Exception as e:
            print(f"Error getting models from plugin {provider_name}: {e}")
        
        # 尝试从配置文件读取提供商信息作为备选
        try:
            config_path = self.plugin_loader.plugins_dir / provider_name / "config.json"
            if config_path.exists():
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'provider_info' in config:
                    provider_data = config['provider_info']
                    from .models import TokenInfo
                    tokens_data = provider_data.get('tokens', {'input': 0.0, 'output': 0.0, 'unit': 'CNY'})
                    tokens = TokenInfo(
                        input=tokens_data.get('input', 0.0),
                        output=tokens_data.get('output', 0.0),
                        unit=tokens_data.get('unit', 'CNY')
                    )
                    return ProviderInfo(
                        name=provider_name,
                        display_name=provider_data.get('display_name', plugin.config.brand_name),
                        api_website=provider_data.get('api_website') or provider_data.get('website', getattr(plugin.config, 'base_url', 'https://example.com')),
                        full_name=f"{provider_name}/default",
                        tokens=tokens
                    )
        except Exception as e:
            print(f"Error loading provider config for {provider_name}: {e}")
        
        # 使用默认值
        from .models import TokenInfo
        default_tokens = TokenInfo(input=0.0, output=0.0, unit='CNY')
        return ProviderInfo(
            name=provider_name,
            display_name=plugin.config.brand_name,
            api_website=getattr(plugin.config, 'base_url', 'https://example.com'),
            full_name=f"{provider_name}/default",
            tokens=default_tokens
        )
    
    async def get_models_by_provider(self, provider_name: str) -> List[ModelInfo]:
        """根据提供商获取模型列表
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            List[ModelInfo]: 该提供商支持的模型列表
        """
        await self._ensure_plugins_loaded()
        
        plugin = self.plugins.get(provider_name)
        if not plugin or not plugin.enabled:
            return []
            
        try:
            models = await plugin.get_models()
            # 为每个模型添加提供商信息
            provider_info = await self.get_provider_by_name(provider_name)
            if provider_info:
                for model in models:
                    model.providers = [provider_info]
            return models
        except Exception as e:
            print(f"Error getting models from provider {provider_name}: {e}")
            return []
    
    async def get_providers_for_model(self, model_name: str) -> List[ProviderInfo]:
        """获取支持指定模型的提供商列表
        
        Args:
            model_name: 模型名称
            
        Returns:
            List[ProviderInfo]: 支持该模型的提供商列表（按推荐程度排序）
        """
        await self._ensure_plugins_loaded()
        
        providers = []
        for plugin_name, plugin in self.plugins.items():
            if plugin.enabled:
                try:
                    models = await plugin.get_models()
                    # 检查该插件是否支持指定模型
                    for model in models:
                        if model.name == model_name:
                            provider_info = await self.get_provider_by_name(plugin_name)
                            if provider_info:
                                providers.append(provider_info)
                            break
                except Exception as e:
                    print(f"Error checking models from provider {plugin_name}: {e}")
        
        # 返回提供商列表
        return providers