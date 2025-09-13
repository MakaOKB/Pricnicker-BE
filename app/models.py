from pydantic import BaseModel
from typing import Optional, List


class TokenInfo(BaseModel):
    """代币价格信息模型"""
    input: float  # 输入代币价格
    output: float  # 输出代币价格
    unit: str  # 价格单位


class ProviderInfo(BaseModel):
    """服务提供商信息模型"""
    name: str  # 提供商标识名称
    display_name: str  # 提供商显示名称
    api_endpoint: str  # API端点地址
    reliability_score: float  # 可靠性评分 (0-10)
    response_time_ms: int  # 平均响应时间(毫秒)
    uptime_percentage: float  # 正常运行时间百分比
    region: str  # 服务区域
    support_streaming: bool  # 是否支持流式响应


class ModelInfo(BaseModel):
    """模型信息模型"""
    brand: str  # 品牌名称
    name: str  # 模型名称
    data_amount: Optional[int] = None  # 数据量（可为空）
    window: int  # 上下文窗口大小
    tokens: TokenInfo  # 代币价格信息
    providers: List['ProviderInfo']  # 可用的服务提供商列表
    recommended_provider: Optional[str] = None  # 推荐的提供商名称


class BrandsResponse(BaseModel):
    """品牌列表响应模型"""
    brands: List[str]  # 品牌名称列表
    count: int  # 品牌总数


class ErrorResponse(BaseModel):
    """错误响应模型"""
    detail: str  # 错误详情