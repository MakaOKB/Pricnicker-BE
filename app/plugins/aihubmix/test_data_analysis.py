#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析测试脚本

分析从 AIHubMix API 获取的模型数据，展示详细的统计信息
"""

import json
import logging
import requests
from collections import Counter, defaultdict
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_api_data() -> Optional[List[Dict]]:
    """
    从 API 获取模型数据
    
    Returns:
        Optional[List[Dict]]: 模型数据列表，失败时返回None
    """
    api_url = "https://aihubmix.com/call/mdl_info"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://aihubmix.com/models',
        'Origin': 'https://aihubmix.com'
    }
    
    try:
        logger.info(f"正在请求 API: {api_url}")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"API 请求失败，状态码: {response.status_code}")
            return None
        
        data = response.json()
        if not data.get('success', False):
            logger.error("API 返回失败状态")
            return None
        
        models_data = data.get('data', [])
        logger.info(f"成功从 API 获取到 {len(models_data)} 个模型数据")
        return models_data
        
    except Exception as e:
        logger.error(f"获取 API 数据失败: {e}")
        return None

def analyze_data_structure(models_data: List[Dict]) -> None:
    """
    分析数据结构
    
    Args:
        models_data: 模型数据列表
    """
    print("\n=== 数据结构分析 ===")
    
    if not models_data:
        print("❌ 没有数据可分析")
        return
    
    # 分析第一个模型的字段结构
    sample_model = models_data[0]
    print(f"📊 数据字段结构（基于第一个模型）:")
    for key, value in sample_model.items():
        value_type = type(value).__name__
        value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
        print(f"  • {key}: {value_type} = {value_preview}")
    
    # 统计所有字段出现频率
    all_fields = Counter()
    for model in models_data:
        all_fields.update(model.keys())
    
    print(f"\n📈 字段出现频率统计:")
    for field, count in all_fields.most_common():
        percentage = (count / len(models_data)) * 100
        print(f"  • {field}: {count}/{len(models_data)} ({percentage:.1f}%)")

def analyze_brands_and_models(models_data: List[Dict]) -> None:
    """
    分析品牌和模型分布
    
    Args:
        models_data: 模型数据列表
    """
    print("\n=== 品牌和模型分析 ===")
    
    # 统计品牌分布
    brand_counter = Counter()
    model_names = []
    
    for model in models_data:
        developer = model.get('developer', 'Unknown')
        model_name = model.get('model', '') or model.get('model_name', '')
        
        brand_counter[developer] += 1
        if model_name:
            model_names.append(model_name)
    
    print(f"🏢 品牌分布（前10名）:")
    for brand, count in brand_counter.most_common(10):
        percentage = (count / len(models_data)) * 100
        print(f"  • {brand}: {count} 个模型 ({percentage:.1f}%)")
    
    print(f"\n📝 模型名称示例（前10个）:")
    for i, name in enumerate(model_names[:10], 1):
        print(f"  {i}. {name}")
    
    print(f"\n📊 总计: {len(brand_counter)} 个品牌, {len(model_names)} 个模型")

def analyze_pricing_data(models_data: List[Dict]) -> None:
    """
    分析价格数据
    
    Args:
        models_data: 模型数据列表
    """
    print("\n=== 价格数据分析 ===")
    
    ratios = []
    completion_ratios = []
    
    for model in models_data:
        model_ratio = model.get('model_ratio', 0)
        completion_ratio = model.get('completion_ratio', 0)
        
        if model_ratio and model_ratio > 0:
            ratios.append(float(model_ratio))
        
        if completion_ratio and completion_ratio > 0:
            completion_ratios.append(float(completion_ratio))
    
    if ratios:
        print(f"💰 模型价格比例统计:")
        print(f"  • 有价格数据的模型: {len(ratios)}/{len(models_data)} ({len(ratios)/len(models_data)*100:.1f}%)")
        print(f"  • 最低价格比例: {min(ratios):.6f}")
        print(f"  • 最高价格比例: {max(ratios):.6f}")
        print(f"  • 平均价格比例: {sum(ratios)/len(ratios):.6f}")
        
        # 价格区间分布
        price_ranges = {
            '超低价 (≤0.001)': len([r for r in ratios if r <= 0.001]),
            '低价 (0.001-0.01)': len([r for r in ratios if 0.001 < r <= 0.01]),
            '中价 (0.01-0.1)': len([r for r in ratios if 0.01 < r <= 0.1]),
            '高价 (>0.1)': len([r for r in ratios if r > 0.1])
        }
        
        print(f"\n📊 价格区间分布:")
        for range_name, count in price_ranges.items():
            if count > 0:
                percentage = (count / len(ratios)) * 100
                print(f"  • {range_name}: {count} 个模型 ({percentage:.1f}%)")
    else:
        print("❌ 没有找到有效的价格数据")

def analyze_descriptions(models_data: List[Dict]) -> None:
    """
    分析模型描述信息
    
    Args:
        models_data: 模型数据列表
    """
    print("\n=== 描述信息分析 ===")
    
    descriptions = []
    context_info = []
    
    for model in models_data:
        desc = model.get('desc', '')
        if desc:
            descriptions.append(desc)
            
            # 提取上下文长度信息
            import re
            context_match = re.search(r'([0-9]+[KMB]?)\s*(?:令牌|token|上下文|context)', desc, re.IGNORECASE)
            if context_match:
                context_info.append(context_match.group(1))
    
    print(f"📝 描述信息统计:")
    print(f"  • 有描述的模型: {len(descriptions)}/{len(models_data)} ({len(descriptions)/len(models_data)*100:.1f}%)")
    
    if descriptions:
        avg_length = sum(len(desc) for desc in descriptions) / len(descriptions)
        print(f"  • 平均描述长度: {avg_length:.0f} 字符")
        
        # 显示几个描述示例
        print(f"\n📄 描述示例:")
        for i, desc in enumerate(descriptions[:3], 1):
            preview = desc[:100] + "..." if len(desc) > 100 else desc
            print(f"  {i}. {preview}")
    
    if context_info:
        print(f"\n🔍 上下文长度信息:")
        context_counter = Counter(context_info)
        for context, count in context_counter.most_common(5):
            print(f"  • {context}: {count} 个模型")

def save_sample_data(models_data: List[Dict]) -> None:
    """
    保存样本数据到文件
    
    Args:
        models_data: 模型数据列表
    """
    print("\n=== 保存样本数据 ===")
    
    # 保存前5个模型的完整数据
    sample_data = models_data[:5]
    
    try:
        with open('sample_models.json', 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存前5个模型的样本数据到 sample_models.json")
    except Exception as e:
        print(f"❌ 保存样本数据失败: {e}")

def main():
    """
    主函数：执行完整的数据分析
    """
    print("🚀 开始 AIHubMix 数据分析测试")
    print("=" * 50)
    
    # 获取数据
    models_data = fetch_api_data()
    if not models_data:
        print("❌ 无法获取数据，测试终止")
        return
    
    print(f"✅ 成功获取 {len(models_data)} 个模型数据")
    
    # 执行各项分析
    analyze_data_structure(models_data)
    analyze_brands_and_models(models_data)
    analyze_pricing_data(models_data)
    analyze_descriptions(models_data)
    save_sample_data(models_data)
    
    print("\n" + "=" * 50)
    print("🎉 数据分析测试完成！")

if __name__ == "__main__":
    main()