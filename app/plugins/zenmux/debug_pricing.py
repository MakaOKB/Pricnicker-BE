#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
from plugin import ZenmuxPlugin

async def main():
    print("=== 调试价格问题 ===")
    
    plugin = ZenmuxPlugin()
    
    # 1. 检查原始API数据
    print("\n1. 检查原始API数据:")
    raw_data = plugin._get_models_from_api()
    if raw_data:
        print(f"获取到 {len(raw_data)} 个原始模型")
        for i, model in enumerate(raw_data[:5]):
            print(f"  模型{i+1}: {model.get('name')}")
            print(f"    pricing_prompt: {model.get('pricing_prompt')}")
            print(f"    pricing_completion: {model.get('pricing_completion')}")
    
    # 2. 检查转换后的数据
    print("\n2. 检查转换后的数据:")
    models = await plugin.get_models()
    if models:
        print(f"转换后得到 {len(models)} 个模型")
        for i, model in enumerate(models[:5]):
            print(f"  模型{i+1}: {model.name}")
            if model.providers:
                tokens = model.providers[0].tokens
                print(f"    input: {tokens.input}")
                print(f"    output: {tokens.output}")
                print(f"    unit: {tokens.unit}")
    
    # 3. 检查是否有对象重用问题
    print("\n3. 检查对象重用问题:")
    models2 = await plugin.get_models()
    if models and models2:
        print("比较两次调用的结果:")
        for i in range(min(3, len(models), len(models2))):
            m1 = models[i]
            m2 = models2[i]
            t1 = m1.providers[0].tokens if m1.providers else None
            t2 = m2.providers[0].tokens if m2.providers else None
            
            print(f"  模型{i+1}: {m1.name}")
            if t1 and t2:
                print(f"    第一次: input={t1.input}, output={t1.output}")
                print(f"    第二次: input={t2.input}, output={t2.output}")
                print(f"    是否相同对象: {t1 is t2}")
                print(f"    值是否相等: input={t1.input == t2.input}, output={t1.output == t2.output}")
    
    # 4. 检查TokenInfo对象的创建
    print("\n4. 检查TokenInfo对象创建:")
    if raw_data:
        from plugin import TokenInfo
        for i, model_data in enumerate(raw_data[:3]):
            input_price = float(model_data.get('pricing_prompt', 0.0))
            output_price = float(model_data.get('pricing_completion', 0.0))
            
            token_info = TokenInfo(
                input=input_price,
                output=output_price,
                unit='USD'
            )
            
            print(f"  模型{i+1}: {model_data.get('name')}")
            print(f"    原始数据: prompt={model_data.get('pricing_prompt')}, completion={model_data.get('pricing_completion')}")
            print(f"    转换后: input={input_price}, output={output_price}")
            print(f"    TokenInfo: input={token_info.input}, output={token_info.output}")
            print(f"    对象ID: {id(token_info)}")

if __name__ == "__main__":
    asyncio.run(main())