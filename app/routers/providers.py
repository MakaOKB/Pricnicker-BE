from fastapi import APIRouter, HTTPException
from typing import List
from ..models import ModelInfo, ProviderInfo
from ..services import ModelService

# 创建提供商路由器实例
router = APIRouter()

# 创建模型服务实例
model_service = ModelService()


@router.get("/providers", response_model=List[ProviderInfo], summary="获取所有提供商信息")
async def get_all_providers():
    """
    获取所有已注册的AI模型服务提供商信息
    """
    try:
        providers = await model_service.get_all_providers()
        return providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提供商信息失败: {str(e)}")


@router.get("/providers/{provider_name}", response_model=ProviderInfo, summary="获取指定提供商信息")
async def get_provider_info(provider_name: str):
    """
    根据提供商名称获取详细的提供商信息
    """
    try:
        provider = await model_service.get_provider_by_name(provider_name)
        if not provider:
            raise HTTPException(status_code=404, detail=f"提供商 '{provider_name}' 不存在")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提供商信息失败: {str(e)}")


@router.get("/providers/{provider_name}/models", response_model=List[ModelInfo], summary="获取提供商的模型列表")
async def get_models_by_provider(provider_name: str):
    """
    根据指定的提供商名称获取该提供商支持的所有模型信息
    """
    try:
        models = await model_service.get_models_by_provider(provider_name)
        if not models:
            raise HTTPException(status_code=404, detail=f"提供商 '{provider_name}' 不存在或没有可用模型")
        return models
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提供商模型失败: {str(e)}")


@router.get("/models/{model_name}/providers", response_model=List[ProviderInfo], summary="获取支持指定模型的提供商列表")
async def get_providers_for_model(model_name: str):
    """
    根据模型名称获取所有支持该模型的服务提供商信息，按推荐程度排序
    """
    try:
        providers = await model_service.get_providers_for_model(model_name)
        if not providers:
            raise HTTPException(status_code=404, detail=f"模型 '{model_name}' 不存在或没有可用提供商")
        return providers
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型提供商失败: {str(e)}")