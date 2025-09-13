#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型接入平台多方比价API启动脚本

使用方法:
    python main.py
    
或者使用uvicorn直接启动:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    # 启动FastAPI应用
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下启用自动重载
        log_level="info"
    )