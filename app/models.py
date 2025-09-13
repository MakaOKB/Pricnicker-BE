from pydantic import BaseModel
from typing import Optional, List


class TokenInfo(BaseModel):
    """代币价格信息模型"""
    input: float  # 输入代币价格
    output: float  # 输出代币价格
    unit: str  # 价格单位


class ModelInfo(BaseModel):
    """模型信息模型"""
    brand: str  # 品牌名称
    name: str  # 模型名称
    data_amount: Optional[int] = None  # 数据量（可为空）
    window: int  # 上下文窗口大小
    tokens: TokenInfo  # 代币价格信息


class ModelsResponse(BaseModel):
    """模型列表响应模型"""
    models: List[ModelInfo]