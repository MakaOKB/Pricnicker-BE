from fastapi import APIRouter, HTTPException
from typing import List
from ..models import ModelInfo, ProviderInfo, BrandsResponse
from ..services import ModelService

# 创建路由器实例
router = APIRouter()

# 创建模型服务实例
model_service = ModelService()


@router.get("/models", response_model=List[ModelInfo], summary="获取所有模型信息")
async def get_models():
    """
    获取所有已注册模型服务商的模型信息，包括价格、上下文窗口等详细信息
    """
    try:
        models = await model_service.get_all_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/models/brands", response_model=BrandsResponse, summary="获取可用的模型品牌列表")
async def get_available_brands():
    """
    获取可用的模型服务商品牌列表
    """
    try:
        brands = await model_service.get_brands()
        return BrandsResponse(brands=brands, count=len(brands))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌列表失败: {str(e)}")


@router.get("/models/brand/{brand_name}", summary="根据品牌获取模型列表")
async def get_models_by_brand(brand_name: str):
    """
    根据品牌名称获取模型列表
    """
    try:
        brand_models = await model_service.get_models_by_brand(brand_name)
        if not brand_models:
            raise HTTPException(status_code=404, detail=f"未找到品牌 '{brand_name}' 的模型")
        return brand_models
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌模型失败: {str(e)}")