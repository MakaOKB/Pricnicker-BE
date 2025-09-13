from fastapi import APIRouter, HTTPException
from typing import List
from ..models import ModelInfo
from ..services import ModelService

# 创建路由器实例
router = APIRouter()

# 创建模型服务实例
model_service = ModelService()


@router.get("/query/models", response_model=List[ModelInfo])
async def get_models():
    """获取全局模型列表
    
    获取所有已注册模型服务商的模型信息，包括价格、上下文窗口等详细信息。
    
    Returns:
        List[ModelInfo]: 所有模型的信息列表
        
    Raises:
        HTTPException: 当获取模型信息失败时抛出500错误
    """
    try:
        models = await model_service.get_all_models()
        return models
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取模型列表失败: {str(e)}"
        )


@router.get("/query/models/brands")
async def get_available_brands():
    """获取可用的模型服务商品牌列表
    
    Returns:
        dict: 包含所有可用品牌的字典
    """
    try:
        brands = await model_service.get_brands()
        return {
            "brands": brands,
            "count": len(brands)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取品牌列表失败: {str(e)}"
        )


@router.get("/query/models/brand/{brand_name}")
async def get_models_by_brand(brand_name: str):
    """根据品牌名称获取模型列表
    
    Args:
        brand_name: 品牌名称
        
    Returns:
        List[ModelInfo]: 指定品牌的模型列表
    """
    try:
        brand_models = await model_service.get_models_by_brand(brand_name)
        
        if not brand_models:
            raise HTTPException(
                status_code=404,
                detail=f"未找到品牌 '{brand_name}' 的模型"
            )
        
        return brand_models
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取品牌模型失败: {str(e)}"
        )


@router.get("/query/plugins/status")
async def get_plugin_status():
    """获取所有插件的状态信息
    
    Returns:
        dict: 插件状态信息
    """
    try:
        status = model_service.get_plugin_status()
        return {
            "plugins": status,
            "total_count": len(status),
            "enabled_count": sum(1 for p in status.values() if p["enabled"])
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取插件状态失败: {str(e)}"
        )


@router.post("/query/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """启用指定插件
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        dict: 操作结果
    """
    try:
        success = model_service.enable_plugin(plugin_name)
        if success:
            return {"message": f"插件 {plugin_name} 已启用", "success": True}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"插件 '{plugin_name}' 不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"启用插件失败: {str(e)}"
        )


@router.post("/query/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """禁用指定插件
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        dict: 操作结果
    """
    try:
        success = model_service.disable_plugin(plugin_name)
        if success:
            return {"message": f"插件 {plugin_name} 已禁用", "success": True}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"插件 '{plugin_name}' 不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"禁用插件失败: {str(e)}"
        )


@router.post("/query/plugins/{plugin_name}/reload")
async def reload_plugin(plugin_name: str):
    """重新加载指定插件
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        dict: 操作结果
    """
    try:
        success = await model_service.reload_plugin(plugin_name)
        if success:
            return {"message": f"插件 {plugin_name} 已重新加载", "success": True}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"插件 '{plugin_name}' 重新加载失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"重新加载插件失败: {str(e)}"
        )