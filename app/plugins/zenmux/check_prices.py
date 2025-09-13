#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from plugin import ZenmuxPlugin

async def main():
    plugin = ZenmuxPlugin()
    models = await plugin.get_models()
    
    print("前10个模型的价格信息:")
    for i, model in enumerate(models[:10]):
        if model.providers:
            tokens = model.providers[0].tokens
            print(f"模型{i+1}: {model.name}")
            print(f"  输入价格: ${tokens.input}")
            print(f"  输出价格: ${tokens.output}")
            print(f"  单位: {tokens.unit}")
            print()
        else:
            print(f"模型{i+1}: {model.name} - 无价格信息")

if __name__ == "__main__":
    asyncio.run(main())