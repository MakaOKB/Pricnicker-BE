#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AiHubMix插件测试脚本

用于测试AiHubMix插件的基本功能
"""

import asyncio
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# 模拟基础类和模型
@dataclass
class TokenInfo:
    """Token价格信息"""
    input: float
    output: float
    unit: str

@dataclass
class ModelInfo:
    """模型信息"""
    brand: str
    name: str
    data_amount: int
    window: int
    tokens: TokenInfo
    providers: List[str]

class PluginConfig:
    """插件配置类"""
    def __init__(self, name: str, version: str, description: str, author: str, 
                 brand_name: str, enabled: bool, extra_config: Dict[str, Any]):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.brand_name = brand_name
        self.enabled = enabled
        self.extra_config = extra_config

class BasePlugin:
    """基础插件类"""
    def __init__(self, config: PluginConfig):
        self.config = config

# 导入插件类
sys.path.insert(0, str(Path(__file__).parent))
from plugin import AihubmixPlugin

def load_config() -> PluginConfig:
    """加载插件配置"""
    config_path = Path(__file__).parent / "config.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    return PluginConfig(
        name=config_data['name'],
        version=config_data['version'],
        description=config_data['description'],
        author=config_data['author'],
        brand_name=config_data['brand_name'],
        enabled=config_data['enabled'],
        extra_config=config_data['extra_config']
    )

async def test_plugin():
    """测试插件功能"""
    print("AiHubMix插件功能测试")
    print("=" * 50)
    
    try:
        # 加载配置
        print("加载插件配置...")
        config = load_config()
        print(f"配置加载成功: {config.name} v{config.version}")
        
        # 创建插件实例
        print("创建插件实例...")
        plugin = AihubmixPlugin(config)
        print("插件实例创建成功")
        
        # 测试配置验证
        print("\n=== 测试配置验证 ===")
        is_valid = await plugin.validate_config()
        print(f"配置验证结果: {'通过' if is_valid else '失败'}")
        
        # 测试获取模型列表
        print("\n=== 测试获取模型列表 ===")
        models = await plugin.get_models()
        print(f"获取到 {len(models)} 个模型:")
        
        for i, model in enumerate(models[:3], 1):  # 只显示前3个模型
            print(f"  {i}. {model.brand} - {model.name}")
            print(f"     输入价格: ${model.tokens.input}/{model.tokens.unit}")
            print(f"     输出价格: ${model.tokens.output}/{model.tokens.unit}")
            print()
        
        # 测试获取模型价格
        if models:
            print("\n=== 测试获取模型价格 ===")
            test_model = models[0]
            pricing = await plugin.get_model_pricing(test_model.name)
            print(f"模型: {pricing['model_name']}")
            print(f"品牌: {pricing['brand']}")
            print(f"输入价格: ${pricing['input_price']}/{pricing['currency']}")
            print(f"输出价格: ${pricing['output_price']}/{pricing['currency']}")
        
        # 测试获取支持品牌
        print("\n=== 测试获取支持品牌 ===")
        brands = await plugin.get_supported_brands()
        print(f"支持的品牌: {', '.join(brands)}")
        
        # 清理资源
        print("\n=== 清理资源 ===")
        await plugin.cleanup()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(test_plugin())
    sys.exit(exit_code)