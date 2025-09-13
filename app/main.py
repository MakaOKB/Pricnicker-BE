import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import query, providers
from .cache_manager import cache_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时清理缓存并启动自动清理任务
    """
    # 启动时清理所有缓存
    logger.info("应用启动：清理所有缓存")
    cache_manager.clear_cache()
    
    # 启动自动清理任务
    cleanup_task = asyncio.create_task(cache_manager.start_auto_cleanup())
    logger.info("缓存自动清理任务已启动")
    
    yield
    
    # 应用关闭时取消清理任务
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("缓存自动清理任务已停止")

# 创建FastAPI应用实例
app = FastAPI(
    title="大模型接入平台多方比价API",
    description="提供多个模型服务商的价格比较和模型信息查询服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS中间件
# 根据环境变量配置允许的源
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    # 生产环境：严格的域名限制
    ALLOWED_ORIGINS = [
        "https://api.pc.msaos.tech",
        "https://pc.msaos.tech",
        "https://www.pc.msaos.tech",
        "https://llm.msaos.tech"
    ]
else:
    # 开发环境：包含本地开发域名
    ALLOWED_ORIGINS = [
        "https://api.pc.msaos.tech",
        "https://pc.msaos.tech",
        "https://www.pc.msaos.tech",
        "https://llm.msaos.tech",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite 默认端口
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173"
    ]

# 支持通过环境变量添加额外的允许源
EXTRA_ORIGINS = os.getenv("CORS_EXTRA_ORIGINS", "")
if EXTRA_ORIGINS:
    ALLOWED_ORIGINS.extend([origin.strip() for origin in EXTRA_ORIGINS.split(",") if origin.strip()])

logger.info(f"CORS配置 - 环境: {ENVIRONMENT}, 允许的源: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-API-Key",
        "Cache-Control",
        "Pragma"
    ],
    expose_headers=[
        "X-Total-Count",
        "X-Page-Count",
        "X-Cache-Status",
        "X-Response-Time"
    ],
    max_age=86400,  # 预检请求缓存时间（24小时）
)

# 注册路由
app.include_router(query.router, prefix="/v1/query", tags=["v1/query"])
app.include_router(providers.router, prefix="/v1", tags=["v1/providers"])


@app.get("/")
async def root():
    """根路径健康检查接口
    
    Returns:
        dict: 包含服务状态信息的字典
    """
    return {
        "message": "大模型接入平台多方比价API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查接口
    
    Returns:
        dict: 服务健康状态
    """
    return {"status": "healthy"}


@app.get("/v1/clearcache")
async def clear_cache():
    """清理缓存接口
    
    无论携带什么参数都直接删除缓存文件夹
    
    Returns:
        dict: 清理结果
    """
    try:
        success = cache_manager.clear_cache()
        if success:
            logger.info("通过API手动清理缓存成功")
            return {
                "status": "success",
                "message": "缓存已清理",
                "timestamp": cache_manager._get_cache_metadata().get("last_clear", "unknown")
            }
        else:
            return {
                "status": "error",
                "message": "缓存清理失败"
            }
    except Exception as e:
        logger.error(f"清理缓存API出错: {e}")
        return {
            "status": "error",
            "message": f"清理缓存时发生错误: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)