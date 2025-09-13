# 生产环境部署指南

## 环境配置

### 1. 环境变量设置

复制 `.env.example` 文件为 `.env` 并根据实际环境配置：

```bash
cp .env.example .env
```

### 2. 生产环境配置

在生产环境中，请设置以下环境变量：

```bash
# 设置为生产环境
export ENVIRONMENT=production

# 如需添加额外的允许源
export CORS_EXTRA_ORIGINS="https://admin.pc.msaos.tech,https://dashboard.pc.msaos.tech"

# 设置日志级别
export LOG_LEVEL=WARNING
```

## CORS 配置说明

### 当前配置的允许源

**生产环境** (`ENVIRONMENT=production`)：
- `https://api.pc.msaos.tech`
- `https://pc.msaos.tech`
- `https://www.pc.msaos.tech`
- `https://llm.msaos.tech` (前端应用)

**开发环境** (`ENVIRONMENT=development`)：
- 包含生产环境的所有域名
- `http://localhost:3000`
- `http://localhost:8080`
- `http://localhost:5173` (Vite 默认端口)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:8080`
- `http://127.0.0.1:5173`

### 动态添加允许源

通过 `CORS_EXTRA_ORIGINS` 环境变量可以动态添加额外的允许源：

```bash
# 单个域名
export CORS_EXTRA_ORIGINS="https://new-frontend.example.com"

# 多个域名（用逗号分隔）
export CORS_EXTRA_ORIGINS="https://admin.pc.msaos.tech,https://mobile.pc.msaos.tech"
```

## 安全特性

### 1. 严格的域名限制
- 生产环境只允许预定义的安全域名
- 不使用通配符 `*`，避免安全风险

### 2. 限制的 HTTP 方法
- 只允许必要的 HTTP 方法：`GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`, `HEAD`

### 3. 受控的请求头
- 只允许必要的请求头，包括认证和内容类型相关头部

### 4. 预检请求缓存
- 设置 24 小时的预检请求缓存，减少不必要的 OPTIONS 请求

## 启动命令

### 开发环境
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 生产环境
```bash
# 设置环境变量
export ENVIRONMENT=production

# 启动应用
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Docker 部署示例

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 设置生产环境
ENV ENVIRONMENT=production
ENV LOG_LEVEL=WARNING

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - CORS_EXTRA_ORIGINS=https://admin.pc.msaos.tech
      - LOG_LEVEL=WARNING
    restart: unless-stopped
```

## 监控和日志

应用启动时会输出当前的 CORS 配置信息：

```
INFO:app.main:CORS配置 - 环境: production, 允许的源: ['https://api.pc.msaos.tech', 'https://pc.msaos.tech', 'https://www.pc.msaos.tech']
```

请确保在生产环境中监控这些日志，确认 CORS 配置正确。