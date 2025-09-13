from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import query

# 创建FastAPI应用实例
app = FastAPI(
    title="大模型接入平台多方比价API",
    description="提供多个模型服务商的价格比较和模型信息查询服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(query.router, prefix="/v1", tags=["v1/query"])


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)