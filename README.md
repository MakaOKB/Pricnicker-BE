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
│   ├── plugins/             # 模型服务商插件
│   │   ├── __init__.py
│   │   ├── base.py          # 插件基类
│   │   ├── loader.py        # 插件加载器
│   │   ├── aihubmix/        # AIHubMix插件
│   │   │   ├── __init__.py
│   │   │   ├── config.json  # 插件配置
│   │   │   └── plugin.py    # 插件实现
│   │   └── zenmux/          # ZenMux插件
│   │       ├── __init__.py
│   │       ├── config.json  # 插件配置
│   │       └── plugin.py    # 插件实现
│   └── routers/             # API路由
│       ├── __init__.py
│       ├── providers.py     # 服务商相关路由
│       └── query.py         # 查询相关路由
├── main.py                  # 启动脚本
├── requirements.txt         # 项目依赖
└── README.md               # 项目说明
```

## 功能特性

- 🚀 基于FastAPI的高性能异步API
- 🔌 可扩展的模型服务商插件架构
- 💰 统一的价格比较接口
- 📊 支持多种模型信息查询
- 🛡️ 完整的错误处理和异常管理
- 📖 自动生成的API文档

## 环境要求

- Python 3.8+
- pip 或 conda 包管理器
- 网络连接（用于获取模型数据）

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd pricnicker-backend
```

### 2. 创建虚拟环境（推荐）

```bash
# 使用 venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 使用 conda
conda create -n pricnicker python=3.9
conda activate pricnicker
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务

```bash
# 开发模式（推荐）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用启动脚本
python main.py
```

### 5. 验证服务

启动服务后，访问以下地址验证服务正常运行：

- 健康检查: http://localhost:8000/health
- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc
- 模型列表: http://localhost:8000/v1/query/models

## 生产部署

### 使用 Docker 部署

1. 创建 Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. 构建和运行：

```bash
docker build -t pricnicker-backend .
docker run -d -p 8000:8000 --name pricnicker pricnicker-backend
```

### 使用 Gunicorn 部署

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 环境变量配置

可以通过环境变量配置服务：

```bash
# 设置端口
export PORT=8000

# 设置日志级别
export LOG_LEVEL=INFO

# 设置CORS允许的域名
export ALLOWED_ORIGINS="http://localhost:3000,https://yourdomain.com"
```

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
    "brand": "Z.AI",
    "name": "GLM 4.5 Air (Z.AI)",
    "data_amount": null,
    "window": 128000,
    "providers": [
      {
        "name": "zenmux",
        "display_name": "ZenMux",
        "api_website": "https://zenmux.ai",
        "tokens": {
          "input": 0.14,
          "output": 0.56,
          "unit": "CNY"
        }
      }
    ],
    "recommended_provider": "zenmux"
  },
  {
    "brand": "OpenAI",
    "name": "GPT-4o (OpenAI)",
    "data_amount": null,
    "window": 128000,
    "providers": [
      {
        "name": "aihubmix",
        "display_name": "AIHubMix",
        "api_website": "https://aihubmix.com",
        "tokens": {
          "input": 35.0,
          "output": 105.0,
          "unit": "CNY"
        }
      }
    ],
    "recommended_provider": "aihubmix"
  }
]
```

### 其他接口

- `GET /v1/query/models/brands` - 获取可用品牌列表
- `GET /v1/query/models/brand/{brand_name}` - 根据品牌获取模型列表
- `GET /health` - 健康检查

## 扩展新的模型服务商

### 1. 创建插件目录结构

在`app/plugins/`目录下创建新的插件目录：

```
app/plugins/yourprovider/
├── __init__.py
├── config.json
└── plugin.py
```

### 2. 创建插件配置文件

在`config.json`中定义插件配置：

```json
{
  "name": "yourprovider",
  "version": "1.0.0",
  "brand_name": "YourProvider",
  "description": "YourProvider模型服务商插件",
  "author": "Your Name",
  "enabled": true,
  "extra_config": {
    "base_url": "https://api.yourprovider.com",
    "models_url": "https://api.yourprovider.com/models",
    "timeout": 30,
    "user_agent": "Mozilla/5.0 (compatible; PricnickerBot/1.0)",
    "default_currency": "CNY"
  }
}
```

### 3. 创建插件类

继承`BasePlugin`基类，实现必要的方法：

```python
import requests
from typing import List, Dict, Optional
from ..base import BasePlugin, PluginConfig
from ...models import ModelInfo, TokenInfo, ProviderInfo

class YourproviderPlugin(BasePlugin):
    """YourProvider模型服务商插件"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.base_url = self.plugin_config.get('base_url')
        self.models_url = self.plugin_config.get('models_url')
        self.timeout = self.plugin_config.get('timeout', 30)
        self.user_agent = self.plugin_config.get('user_agent')
    
    async def initialize(self) -> bool:
        """初始化插件，验证配置"""
        try:
            # 验证必需配置
            if not self.base_url or not self.models_url:
                self.logger.error("缺少必需的URL配置")
                return False
            
            # 测试API连接
            response = requests.get(
                self.base_url, 
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent}
            )
            
            if response.status_code == 200:
                self.logger.info("插件初始化成功")
                return True
            else:
                self.logger.error(f"API连接失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"插件初始化失败: {e}")
            return False
    
    async def get_models(self) -> List[ModelInfo]:
        """获取模型列表"""
        try:
            # 调用API获取模型数据
            response = requests.get(
                self.models_url,
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent}
            )
            
            if response.status_code != 200:
                self.logger.error(f"获取模型数据失败: {response.status_code}")
                return []
            
            api_data = response.json()
            return self._convert_to_model_info(api_data)
            
        except Exception as e:
            self.logger.error(f"获取模型数据异常: {e}")
            return []
    
    def _convert_to_model_info(self, api_data: List[Dict]) -> List[ModelInfo]:
        """将API数据转换为ModelInfo格式"""
        models = []
        
        for model_data in api_data:
            try:
                # 创建TokenInfo对象
                token_info = TokenInfo(
                    input=float(model_data.get('input_price', 0.0)),
                    output=float(model_data.get('output_price', 0.0)),
                    unit=model_data.get('currency', 'CNY')
                )
                
                # 创建ProviderInfo对象
                provider_info = ProviderInfo(
                    name='yourprovider',
                    display_name='YourProvider',
                    api_website=self.base_url,
                    tokens=token_info
                )
                
                # 创建ModelInfo对象
                model_info = ModelInfo(
                    brand=model_data.get('brand', 'YourProvider'),
                    name=model_data.get('name', 'Unknown'),
                    data_amount=model_data.get('data_amount'),
                    window=model_data.get('context_window', 4096),
                    providers=[provider_info],
                    recommended_provider='yourprovider'
                )
                
                models.append(model_info)
                
            except Exception as e:
                self.logger.warning(f"转换模型数据失败: {e}")
                continue
        
        return models
    
    def get_plugin_info(self) -> Dict:
        """获取插件信息"""
        return {
            'name': self.config.name,
            'version': self.config.version,
            'description': self.config.description,
            'author': self.config.author,
            'enabled': self.enabled,
            'status': 'active' if self.enabled else 'inactive'
        }
```

### 4. 插件自动加载

插件会被系统自动发现和加载，无需手动注册。系统会扫描`app/plugins/`目录下的所有插件并自动加载。

## 开发说明

- 所有插件都应该继承`BasePlugin`基类
- 插件采用配置文件+实现文件的分离设计
- 支持插件的动态加载、启用、禁用和重新加载
- 模型信息使用Pydantic模型进行数据验证
- 支持异步操作，提高并发性能
- 错误处理统一使用HTTPException
- 遵循RESTful API设计规范

## 故障排除

### 常见问题

**Q: 服务启动失败，提示端口被占用**

A: 检查端口是否被其他进程占用：
```bash
# macOS/Linux
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

**Q: 插件加载失败**

A: 检查插件配置和实现：
1. 确认插件目录结构正确
2. 检查`config.json`格式是否正确
3. 确认插件类名与配置文件中的`PluginClass`一致
4. 查看日志文件获取详细错误信息

**Q: API返回空数据**

A: 可能的原因：
1. 插件未正确加载或初始化失败
2. 外部API连接超时或失败
3. 数据转换过程中出现错误

检查方法：
```bash
# 查看服务日志
tail -f zenmux_plugin.log

# 测试插件加载
python3 -c "from app.plugins.loader import PluginLoader; loader = PluginLoader(); print(loader.get_loaded_plugins())"
```

**Q: 跨域请求被阻止**

A: 在生产环境中配置CORS：
```python
# 在 app/main.py 中添加
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 性能优化

1. **启用缓存**: 对模型数据进行缓存，减少API调用频率
2. **连接池**: 使用连接池管理HTTP请求
3. **异步处理**: 利用异步特性并发获取多个插件数据
4. **数据压缩**: 启用gzip压缩减少传输数据量

### 监控和日志

- 查看应用日志: `tail -f app.log`
- 查看插件日志: `tail -f zenmux_plugin.log`
- 监控API性能: 使用`/health`端点进行健康检查
- 查看API文档: 访问`/docs`获取完整API文档

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

MIT License