from pydantic import BaseModel
from typing import Optional, List


class TokenInfo(BaseModel):
    """代币价格信息模型"""
    input: float  # 输入代币价格
    output: float  # 输出代币价格
    unit: str  # 价格单位，枚举值：CNY, USD


class ProviderInfo(BaseModel):
    """服务提供商信息模型"""
    name: str  # 提供商标识名称
    display_name: str  # 提供商显示名称
    api_website: str  # 提供商官方网站地址
    full_name: str  # 模型完整名称，格式为提供商/模型名
    tokens: TokenInfo  # 该提供商的价格信息


class ModelInfo(BaseModel):
    """模型信息模型"""
    brand: str  # 品牌名称
    name: str  # 模型名称
    data_amount: Optional[int] = None  # 训练数据量（可为空）
    window: int  # 上下文窗口大小
    providers: List[ProviderInfo]  # 可用的服务提供商列表
    recommended_provider: Optional[str] = None  # 推荐的服务提供商名称


class BrandsResponse(BaseModel):
    """品牌列表响应模型"""
    brands: List[str]  # 品牌名称列表
    count: int  # 品牌总数


class ErrorResponse(BaseModel):
    """错误响应模型"""
    detail: str  # 错误详情