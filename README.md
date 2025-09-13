# 大模型接入平台多方比价API

一个基于FastAPI的大模型服务商价格比较平台，支持多个模型提供商的接入和统一的价格查询API。

## 项目结构

```
pricnicker-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI主应用
│   ├── models.py            # Pydantic数据模型
│   ├── services.py          # 业务逻辑服务
│   ├── handlers/            # 模型服务商Handler
│   │   ├── __init__.py
│   │   ├── base.py          # Handler基类
│   │   ├── deepseek_handler.py    # DeepSeek Handler
│   │   └── anthropic_handler.py   # Anthropic Handler
│   └── routers/             # API路由
│       ├── __init__.py
│       └── query.py         # 查询相关路由
├── main.py                  # 启动脚本
├── requirements.txt         # 项目依赖
└── README.md               # 项目说明
```

## 功能特性

- 🚀 基于FastAPI的高性能异步API
- 🔌 可扩展的模型服务商Handler架构
- 💰 统一的价格比较接口
- 📊 支持多种模型信息查询
- 🛡️ 完整的错误处理和异常管理
- 📖 自动生成的API文档

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 方式1: 使用启动脚本
python main.py

# 方式2: 使用uvicorn直接启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API接口

### 获取全局模型列表

```http
GET /v1/query/models
```

返回所有已注册模型服务商的模型信息。

**响应示例:**

```json
[
  {
    "brand": "DeepSeek",
    "name": "DeepSeek-V3.1",
    "data_amount": 671,
    "window": 160000,
    "tokens": {
      "input": 4,
      "output": 12,
      "unit": "CNY"
    }
  },
  {
    "brand": "Anthropic",
    "name": "Claude-4-Sonnet",
    "data_amount": null,
    "window": 1000000,
    "tokens": {
      "input": 3.3,
      "output": 16,
      "unit": "CNY"
    }
  }
]
```

### 其他接口

- `GET /v1/query/models/brands` - 获取可用品牌列表
- `GET /v1/query/models/brand/{brand_name}` - 根据品牌获取模型列表
- `GET /health` - 健康检查

## 扩展新的模型服务商

### 1. 创建Handler类

继承`BaseModelHandler`基类，实现`get_models`方法：

```python
from app.handlers.base import BaseModelHandler
from app.models import ModelInfo, TokenInfo
from typing import List

class YourProviderHandler(BaseModelHandler):
    def __init__(self):
        super().__init__("YourProvider")
    
    async def get_models(self) -> List[ModelInfo]:
        # 实现获取模型信息的逻辑
        return [
            ModelInfo(
                brand="YourProvider",
                name="YourModel-1.0",
                data_amount=1000,
                window=200000,
                tokens=TokenInfo(
                    input=5,
                    output=15,
                    unit="CNY"
                )
            )
        ]
```

### 2. 注册Handler

在`app/services.py`的`ModelService`类中添加新的Handler：

```python
from .handlers.your_provider_handler import YourProviderHandler

class ModelService:
    def __init__(self):
        self.handlers = [
            DeepSeekHandler(),
            AnthropicHandler(),
            YourProviderHandler(),  # 添加新的Handler
        ]
```

## 开发说明

- 所有Handler都应该继承`BaseModelHandler`基类
- 模型信息使用Pydantic模型进行数据验证
- 支持异步操作，提高并发性能
- 错误处理统一使用HTTPException
- 遵循RESTful API设计规范

## 许可证

MIT License