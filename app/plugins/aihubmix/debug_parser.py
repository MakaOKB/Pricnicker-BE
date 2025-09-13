#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试解析器 - 分析 aihubmix.com API 端点
"""

import requests
import json
import re
from urllib.parse import urljoin

def find_api_endpoints():
    """查找可能的API端点"""
    base_url = "https://aihubmix.com"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://aihubmix.com/models',
    })
    
    # 常见的API端点模式
    api_patterns = [
        '/api/models',
        '/api/v1/models', 
        '/api/v2/models',
        '/models/list',
        '/models/all',
        '/models.json',
        '/data/models',
        '/data/models.json',
        '/static/data/models.json',
        '/config/models.json'
    ]
    
    print("=== 尝试常见API端点 ===")
    for pattern in api_patterns:
        url = urljoin(base_url, pattern)
        try:
            print(f"尝试: {url}")
            response = session.get(url, timeout=10)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"  内容类型: {content_type}")
                
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"  JSON数据长度: {len(str(data))}")
                        print(f"  数据预览: {str(data)[:200]}...")
                        
                        # 保存找到的数据
                        with open(f'api_data_{pattern.replace("/", "_")}.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"  数据已保存")
                        
                    except json.JSONDecodeError:
                        print(f"  响应不是有效的JSON")
                else:
                    print(f"  内容长度: {len(response.text)}")
                    
        except Exception as e:
            print(f"  错误: {e}")
        print()

def analyze_js_files():
    """分析JavaScript文件中的API调用"""
    base_url = "https://aihubmix.com"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    
    # 获取主页面
    response = session.get(f"{base_url}/models")
    html_content = response.text
    
    # 提取所有JavaScript文件URL
    js_urls = re.findall(r'src="([^"]*\.js)"', html_content)
    
    print(f"=== 分析 {len(js_urls)} 个JavaScript文件 ===")
    
    api_patterns = [
        r'/api/[^"\s]+',
        r'"(/[^"]*models[^"]*?)"',
        r'fetch\(["\']([^"\')]+)["\']',
        r'axios\.[get|post]+\(["\']([^"\')]+)["\']',
        r'request\(["\']([^"\')]+)["\']'
    ]
    
    found_apis = set()
    
    for js_url in js_urls[:10]:  # 只分析前10个文件
        if not js_url.startswith('http'):
            js_url = urljoin(base_url, js_url)
        
        try:
            print(f"\n分析: {js_url}")
            js_response = session.get(js_url, timeout=10)
            
            if js_response.status_code == 200:
                js_content = js_response.text
                print(f"  文件大小: {len(js_content)} 字符")
                
                # 查找API模式
                for pattern in api_patterns:
                    matches = re.findall(pattern, js_content)
                    for match in matches:
                        if 'model' in match.lower() or 'api' in match.lower():
                            found_apis.add(match)
                            print(f"  找到API: {match}")
                
        except Exception as e:
            print(f"  错误: {e}")
    
    print(f"\n=== 发现的API端点 ===")
    for api in sorted(found_apis):
        print(f"  {api}")
    
    return found_apis

def test_graphql_endpoint():
    """测试GraphQL端点"""
    base_url = "https://aihubmix.com"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': 'https://aihubmix.com/models',
    })
    
    graphql_endpoints = [
        '/graphql',
        '/api/graphql',
        '/query'
    ]
    
    # 简单的GraphQL查询
    query = {
        "query": "{ models { name brand inputPrice outputPrice } }"
    }
    
    print("=== 测试GraphQL端点 ===")
    for endpoint in graphql_endpoints:
        url = urljoin(base_url, endpoint)
        try:
            print(f"尝试GraphQL: {url}")
            response = session.post(url, json=query, timeout=10)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  响应: {str(data)[:200]}...")
                except:
                    print(f"  响应不是JSON")
                    
        except Exception as e:
            print(f"  错误: {e}")
        print()

def check_common_paths():
    """检查常见的数据路径"""
    base_url = "https://aihubmix.com"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
    })
    
    paths = [
        '/sitemap.xml',
        '/robots.txt',
        '/.well-known/security.txt',
        '/manifest.json',
        '/config.json',
        '/data.json'
    ]
    
    print("=== 检查常见路径 ===")
    for path in paths:
        url = urljoin(base_url, path)
        try:
            print(f"检查: {url}")
            response = session.get(url, timeout=10)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"  内容类型: {content_type}")
                print(f"  内容长度: {len(response.text)}")
                
                if len(response.text) < 1000:
                    print(f"  内容预览: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"  错误: {e}")
        print()

if __name__ == "__main__":
    print("开始分析 AiHubMix API...\n")
    
    # 1. 尝试常见API端点
    find_api_endpoints()
    
    # 2. 分析JavaScript文件
    analyze_js_files()
    
    # 3. 测试GraphQL
    test_graphql_endpoint()
    
    # 4. 检查常见路径
    check_common_paths()
    
    print("\n分析完成！")