#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AIHubMix API 端点
"""

import requests
import json

def test_api():
    """
    测试 AIHubMix API 端点
    """
    url = "https://aihubmix.com/call/mdl_info"
    
    # 尝试不同的请求方法和头部
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://aihubmix.com/models',
        'Origin': 'https://aihubmix.com'
    }
    
    print(f"测试 API: {url}")
    
    # 测试 GET 请求
    try:
        print("\n=== 测试 GET 请求 ===")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容长度: {len(response.text)}")
        if response.text:
            print(f"响应内容前500字符: {response.text[:500]}")
            try:
                data = response.json()
                print(f"JSON 数据类型: {type(data)}")
                if isinstance(data, list):
                    print(f"数组长度: {len(data)}")
                    if data:
                        print(f"第一个元素: {data[0]}")
                elif isinstance(data, dict):
                    print(f"字典键: {list(data.keys())}")
            except json.JSONDecodeError:
                print("响应不是有效的 JSON")
    except Exception as e:
        print(f"GET 请求失败: {e}")
    
    # 测试 POST 请求
    try:
        print("\n=== 测试 POST 请求 ===")
        response = requests.post(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容长度: {len(response.text)}")
        if response.text:
            print(f"响应内容前500字符: {response.text[:500]}")
            try:
                data = response.json()
                print(f"JSON 数据类型: {type(data)}")
                if isinstance(data, list):
                    print(f"数组长度: {len(data)}")
                    if data:
                        print(f"第一个元素: {data[0]}")
                elif isinstance(data, dict):
                    print(f"字典键: {list(data.keys())}")
            except json.JSONDecodeError:
                print("响应不是有效的 JSON")
    except Exception as e:
        print(f"POST 请求失败: {e}")
    
    # 测试带 JSON 数据的 POST 请求
    try:
        print("\n=== 测试带 JSON 数据的 POST 请求 ===")
        headers_json = headers.copy()
        headers_json['Content-Type'] = 'application/json'
        response = requests.post(url, headers=headers_json, json={}, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容长度: {len(response.text)}")
        if response.text:
            print(f"响应内容前500字符: {response.text[:500]}")
            try:
                data = response.json()
                print(f"JSON 数据类型: {type(data)}")
                if isinstance(data, list):
                    print(f"数组长度: {len(data)}")
                    if data:
                        print(f"第一个元素: {data[0]}")
                elif isinstance(data, dict):
                    print(f"字典键: {list(data.keys())}")
            except json.JSONDecodeError:
                print("响应不是有效的 JSON")
    except Exception as e:
        print(f"带 JSON 数据的 POST 请求失败: {e}")

if __name__ == "__main__":
    test_api()