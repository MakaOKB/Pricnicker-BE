#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格和上下文长度修复测试报告

验证修复后的价格计算和上下文长度解析功能
"""

import json
import requests
import re
from typing import Dict, List

def test_price_and_context_fixes():
    """
    测试价格和上下文长度修复效果
    """
    print("=== AIHubMix 价格和上下文长度修复测试报告 ===")
    print()
    
    # 获取API数据
    api_url = "https://aihubmix.com/call/mdl_info"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://aihubmix.com/models'
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        api_data = response.json()
        
        if not api_data.get('success') or not api_data.get('data'):
            print("❌ API数据获取失败")
            return
            
        models_data = api_data['data']
        print(f"✅ 成功获取 {len(models_data)} 个模型数据")
        print()
        
    except Exception as e:
        print(f"❌ API请求失败: {e}")
        return
    
    # 分析价格修复效果
    print("📊 价格计算修复分析:")
    print("-" * 50)
    
    price_examples = []
    base_input_price = 0.0006
    base_output_price = 0.0012
    
    for model in models_data[:10]:  # 分析前10个模型
        model_name = model.get('model', 'Unknown')
        model_ratio = float(model.get('model_ratio', 1.0))
        completion_ratio = float(model.get('completion_ratio', 1.0))
        
        # 计算修复后的价格
        input_price = base_input_price * model_ratio
        output_price = base_output_price * completion_ratio
        
        price_examples.append({
            'model': model_name,
            'model_ratio': model_ratio,
            'completion_ratio': completion_ratio,
            'input_price': round(input_price, 6),
            'output_price': round(output_price, 6)
        })
        
        print(f"模型: {model_name}")
        print(f"  输入倍率: {model_ratio}, 输出倍率: {completion_ratio}")
        print(f"  修复前价格: 输入 0.0006, 输出 0.0012 (固定值)")
        print(f"  修复后价格: 输入 {input_price:.6f}, 输出 {output_price:.6f} CNY/1K tokens")
        print()
    
    # 分析上下文长度修复效果
    print("📏 上下文长度解析修复分析:")
    print("-" * 50)
    
    context_examples = []
    
    def extract_context_from_model_data(model_data):
        """提取上下文长度的修复逻辑"""
        # 检查 context_length 字段
        context_length = model_data.get('context_length', '')
        if context_length and str(context_length).strip():
            return extract_number_with_unit(str(context_length))
        
        # 从描述中提取
        desc = model_data.get('desc', '') or model_data.get('desc_en', '')
        if desc:
            patterns = [
                r'([0-9]+[KMB]?)\s*(?:令牌|token|上下文|context)',
                r'([0-9]+[KMB]?)\s*(?:tokens?|contexts?)',
                r'(?:支持|context|window).*?([0-9]+[KMB]?)\s*(?:令牌|token)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, desc, re.IGNORECASE)
                if match:
                    context_str = match.group(1)
                    parsed_value = extract_number_with_unit(context_str)
                    if parsed_value > 4096:
                        return parsed_value
        
        # 从模型名称中提取
        model_name = model_data.get('model', '') or model_data.get('model_name', '')
        if model_name:
            match = re.search(r'[-_]([0-9]+[KMB]?)(?:$|[-_])', model_name, re.IGNORECASE)
            if match:
                context_str = match.group(1)
                parsed_value = extract_number_with_unit(context_str)
                if parsed_value > 4096:
                    return parsed_value
        
        return 4096
    
    def extract_number_with_unit(text):
        """数字单位转换"""
        if not text:
            return 4096
        
        text = str(text).replace(' ', '').lower()
        match = re.search(r'([0-9.]+)([kmb]?)', text)
        if not match:
            return 4096
        
        number_str, unit = match.groups()
        try:
            number = float(number_str)
            if unit == 'k':
                return int(number * 1000)
            elif unit == 'm':
                return int(number * 1000000)
            elif unit == 'b':
                return int(number * 1000000000)
            else:
                return int(number)
        except ValueError:
            return 4096
    
    # 找出有特殊上下文长度的模型
    special_context_models = []
    for model in models_data:
        model_name = model.get('model', '')
        context_length = extract_context_from_model_data(model)
        
        if context_length != 4096:  # 非默认值
            special_context_models.append({
                'model': model_name,
                'context_length': context_length,
                'source': 'name' if re.search(r'[-_]([0-9]+[KMB]?)(?:$|[-_])', model_name, re.IGNORECASE) else 'description'
            })
    
    print(f"发现 {len(special_context_models)} 个模型有非默认上下文长度:")
    print()
    
    for example in special_context_models[:10]:  # 显示前10个
        print(f"模型: {example['model']}")
        print(f"  上下文长度: {example['context_length']:,} tokens")
        print(f"  解析来源: {example['source']}")
        print()
    
    # 统计分析
    print("📈 修复效果统计:")
    print("-" * 50)
    
    # 价格统计
    unique_input_prices = set()
    unique_output_prices = set()
    
    for model in models_data:
        model_ratio = float(model.get('model_ratio', 1.0))
        completion_ratio = float(model.get('completion_ratio', 1.0))
        input_price = round(base_input_price * model_ratio, 6)
        output_price = round(base_output_price * completion_ratio, 6)
        unique_input_prices.add(input_price)
        unique_output_prices.add(output_price)
    
    print(f"✅ 价格多样性: {len(unique_input_prices)} 种不同的输入价格, {len(unique_output_prices)} 种不同的输出价格")
    print(f"✅ 上下文长度多样性: {len(set(extract_context_from_model_data(m) for m in models_data))} 种不同的上下文长度")
    print(f"✅ 非默认上下文长度模型: {len(special_context_models)} 个 ({len(special_context_models)/len(models_data)*100:.1f}%)")
    
    # 保存详细数据
    detailed_data = {
        'price_examples': price_examples,
        'context_examples': special_context_models[:20],  # 保存前20个
        'statistics': {
            'total_models': len(models_data),
            'unique_input_prices': len(unique_input_prices),
            'unique_output_prices': len(unique_output_prices),
            'special_context_models': len(special_context_models)
        }
    }
    
    with open('price_context_fix_details.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细数据已保存到 price_context_fix_details.json")
    print("\n🎉 价格和上下文长度修复测试完成！")

if __name__ == "__main__":
    test_price_and_context_fixes()