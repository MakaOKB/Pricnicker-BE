#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示所有ZenMux模型的完整列表
"""

from plugin import ZenmuxPlugin
import json
import asyncio

async def main():
    """主函数：显示所有模型的完整信息"""
    print("🚀 正在获取完整的ZenMux模型数据...")
    
    # 创建插件实例并获取数据
    plugin = ZenmuxPlugin()
    data = await plugin.get_models()
    
    print(f"\n=== 📊 完整模型列表 ({len(data)} 个) ===")
    
    # 按品牌分组显示
    brands = {}
    for model in data:
        brand = model.brand
        if brand not in brands:
            brands[brand] = []
        brands[brand].append(model)
    
    for brand, models in sorted(brands.items()):
        print(f"\n🏢 {brand} ({len(models)} 个模型):")
        for i, model in enumerate(models, 1):
            provider = model.providers[0] if model.providers else None
            tokens = provider.tokens if provider else None
            
            if tokens:
                input_price = tokens.input
                output_price = tokens.output
                unit = tokens.unit
            else:
                input_price = 'N/A'
                output_price = 'N/A'
                unit = 'USD'
            
            print(f"  {i:2d}. {model.name:30s} | 上下文: {model.window:>8,} | 价格: ${input_price}/${output_price} per {unit}")
    
    # 显示价格统计
    print(f"\n=== 💰 价格统计 ===")
    prices = []
    for model in data:
        if model.providers:
            tokens = model.providers[0].tokens
            if tokens and tokens.input and tokens.output:
                try:
                    prices.append((float(tokens.input), float(tokens.output)))
                except (ValueError, TypeError):
                    pass
    
    if prices:
        input_prices = [p[0] for p in prices]
        output_prices = [p[1] for p in prices]
        
        print(f"输入价格范围: ${min(input_prices):.2f} - ${max(input_prices):.2f}")
        print(f"输出价格范围: ${min(output_prices):.2f} - ${max(output_prices):.2f}")
        print(f"平均输入价格: ${sum(input_prices)/len(input_prices):.2f}")
        print(f"平均输出价格: ${sum(output_prices)/len(output_prices):.2f}")
    
    print(f"\n=== ✅ 数据展示完成 ===")

if __name__ == "__main__":
    asyncio.run(main())