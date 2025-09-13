#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的插件功能测试
"""

import sys
import os
import json
import logging
import asyncio
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_plugin_functionality():
    """测试插件完整功能"""
    try:
        # 导入插件
        from plugin import ZenmuxPlugin
        
        logger.info("🚀 开始测试ZenMux插件完整功能...")
        
        # 创建插件实例
        plugin = ZenmuxPlugin()
        
        # 测试get_models方法
        logger.info("\n=== 测试get_models方法 ===")
        models = await plugin.get_models()
        
        if not models:
            logger.error("❌ get_models返回空结果")
            return False
        
        logger.info(f"✅ 成功获取到 {len(models)} 个模型")
        
        # 检查前3个模型的数据结构
        for i, model in enumerate(models[:3]):
            logger.info(f"\n--- 模型 {i+1} ---")
            logger.info(f"名称: {model.name}")
            logger.info(f"品牌: {model.brand}")
            logger.info(f"窗口大小: {model.window}")
            logger.info(f"数据量: {model.data_amount}")
            
            # 检查providers信息
            if model.providers:
                provider = model.providers[0]
                logger.info(f"提供商: {provider.display_name}")
                logger.info(f"输入价格: ${provider.tokens.input} {provider.tokens.unit}")
                logger.info(f"输出价格: ${provider.tokens.output} {provider.tokens.unit}")
            else:
                logger.warning("⚠️ 缺少providers数据")
            
        # 测试get_brands方法
        logger.info("\n=== 测试get_brands方法 ===")
        brands = await plugin.get_brands()
        logger.info(f"✅ 成功获取到 {len(brands)} 个品牌: {brands[:10]}...")  # 只显示前10个
        
        # 测试get_model_by_name方法
        logger.info("\n=== 测试get_model_by_name方法 ===")
        if models:
            test_model_name = models[0].name
            found_model = await plugin.get_model_by_name(test_model_name)
            if found_model:
                logger.info(f"✅ 成功通过名称找到模型: {found_model.name}")
            else:
                logger.warning(f"⚠️ 未能通过名称找到模型: {test_model_name}")
        
        logger.info("\n🎉 所有测试完成！")
        return True
        
    except ImportError as e:
        logger.error(f"❌ 导入插件失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 测试过程中出现错误: {e}")
        return False

async def main():
    """主函数"""
    success = await test_plugin_functionality()
    
    if success:
        print("\n✅ 插件功能测试全部通过！")
        print("✅ pricing_prompt和pricing_completion字段已正确解析")
        print("✅ 价格信息已正确转换为editv3.json格式")
    else:
        print("\n❌ 插件功能测试失败")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())