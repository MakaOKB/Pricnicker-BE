#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示ZenMux插件获取到的模型数据详情
"""

from plugin import ZenMuxPlugin

def main():
    """主函数：显示模型数据详情"""
    print("🚀 正在获取ZenMux模型数据...")
    
    # 创建插件实例并获取数据
    plugin = ZenMuxPlugin()
    data = plugin.get_models()
    
    print(f"\n=== 📊 获取到的模型数据概览 ===")
    print(f"总模型数量: {len(data)} 个")
    
    # 统计品牌
    brands = set(model['brand'] for model in data)
    print(f"涉及品牌: {', '.join(sorted(brands))} ({len(brands)}个)")
    
    print(f"\n=== 📋 前10个模型详情 ===")
    for i, model in enumerate(data[:10], 1):
        print(f"{i:2d}. {model['brand']:12s} - {model['name']:25s} (上下文: {model['window']})")
    
    if len(data) > 10:
        print(f"    ... 还有 {len(data) - 10} 个模型")
    
    # 显示价格信息示例
    if data:
        print(f"\n=== 💰 价格信息示例 ===")
        example = data[0]
        print(f"模型名称: {example['name']}")
        print(f"品牌: {example['brand']}")
        print(f"上下文窗口: {example['window']}")
        
        if example['providers']:
            provider = example['providers'][0]
            print(f"提供商: {provider['name']}")
            print(f"显示名称: {provider['display_name']}")
            print(f"API网站: {provider['api_website']}")
            
            tokens = provider['tokens']
            print(f"输入价格: ${tokens['input']} / {tokens['unit']}")
            print(f"输出价格: ${tokens['output']} / {tokens['unit']}")
    
    print(f"\n=== ✅ 数据获取完成 ===")

if __name__ == "__main__":
    main()