#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定模型查询功能
"""

from plugin import AIHubMixPlugin
import json

def test_specific_models():
    """测试特定模型查询"""
    plugin = AIHubMixPlugin()
    
    # 测试模型列表
    test_models = [
        'gpt-5',
        'claude-opus-4-1-20250805',
        'DeepSeek-V3.1',
        'gemini-2.5-pro',
        'o3'
    ]
    
    print("=== 测试特定模型查询 ===")
    
    for model_name in test_models:
        print(f"\n查询模型: {model_name}")
        model_info = plugin.get_model_by_name(model_name)
        
        if model_info:
            print(f"✅ 找到模型: {model_info.get('name')}")
            print(f"   开发商: {model_info.get('developer')}")
            print(f"   描述: {model_info.get('description', '')[:100]}...")
            print(f"   价格比例: {model_info.get('model_ratio')}")
            print(f"   完成比例: {model_info.get('completion_ratio')}")
            print(f"   上下文长度: {model_info.get('context_length')}")
            print(f"   功能: {model_info.get('features')}")
            print(f"   标签: {model_info.get('tags')}")
        else:
            print(f"❌ 未找到模型: {model_name}")
    
    print("\n=== 测试完成 ===")

def test_price_analysis():
    """测试价格分析"""
    plugin = AIHubMixPlugin()
    models = plugin.get_models()
    
    print("\n=== 价格分析 ===")
    
    # 按价格比例排序
    sorted_models = sorted(models, key=lambda x: x.get('model_ratio', 0))
    
    print("\n最便宜的5个模型:")
    for i, model in enumerate(sorted_models[:5]):
        print(f"{i+1}. {model.get('name')} ({model.get('developer')})")
        print(f"   价格比例: {model.get('model_ratio')}")
        print(f"   完成比例: {model.get('completion_ratio')}")
    
    print("\n最贵的5个模型:")
    for i, model in enumerate(sorted_models[-5:]):
        print(f"{i+1}. {model.get('name')} ({model.get('developer')})")
        print(f"   价格比例: {model.get('model_ratio')}")
        print(f"   完成比例: {model.get('completion_ratio')}")
    
    # 按开发商统计
    developer_count = {}
    for model in models:
        dev = model.get('developer', 'Unknown')
        developer_count[dev] = developer_count.get(dev, 0) + 1
    
    print("\n按开发商统计模型数量:")
    for dev, count in sorted(developer_count.items(), key=lambda x: x[1], reverse=True):
        print(f"{dev}: {count} 个模型")

if __name__ == "__main__":
    test_specific_models()
    test_price_analysis()