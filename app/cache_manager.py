import os
import json
import shutil
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class CacheManager:
    """
    缓存管理器
    负责管理应用的缓存数据，包括读取、写入、清理等功能
    """
    
    def __init__(self, cache_dir: str = "cache", cache_ttl_hours: int = 1):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
            cache_ttl_hours: 缓存生存时间（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_ttl_hours = cache_ttl_hours
        self.models_cache_file = self.cache_dir / "models.json"
        self.providers_cache_file = self.cache_dir / "providers.json"
        self.metadata_file = self.cache_dir / "metadata.json"
        
        # 确保缓存目录存在
        self._ensure_cache_dir()
        
        logger.info(f"缓存管理器初始化完成，缓存目录: {self.cache_dir}，TTL: {cache_ttl_hours}小时")
    
    def _ensure_cache_dir(self) -> None:
        """
        确保缓存目录存在
        """
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"缓存目录已创建或已存在: {self.cache_dir}")
        except Exception as e:
            logger.error(f"创建缓存目录失败: {e}")
            raise
    
    def _get_cache_metadata(self) -> Dict[str, Any]:
        """
        获取缓存元数据
        
        Returns:
            缓存元数据字典
        """
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"读取缓存元数据失败: {e}")
        
        return {}
    
    def _save_cache_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        保存缓存元数据
        
        Args:
            metadata: 要保存的元数据
        """
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.debug("缓存元数据已保存")
        except Exception as e:
            logger.error(f"保存缓存元数据失败: {e}")
    
    def is_cache_valid(self, cache_type: str = "models") -> bool:
        """
        检查缓存是否有效
        
        Args:
            cache_type: 缓存类型 ("models" 或 "providers")
            
        Returns:
            缓存是否有效
        """
        try:
            cache_file = self.models_cache_file if cache_type == "models" else self.providers_cache_file
            
            # 检查缓存文件是否存在
            if not cache_file.exists():
                logger.debug(f"{cache_type}缓存文件不存在")
                return False
            
            # 检查缓存是否为空
            if cache_file.stat().st_size == 0:
                logger.debug(f"{cache_type}缓存文件为空")
                return False
            
            # 检查缓存是否过期
            metadata = self._get_cache_metadata()
            last_update_str = metadata.get(f"{cache_type}_last_update")
            
            if not last_update_str:
                logger.debug(f"{cache_type}缓存没有更新时间记录")
                return False
            
            last_update = datetime.fromisoformat(last_update_str)
            expiry_time = last_update + timedelta(hours=self.cache_ttl_hours)
            
            if datetime.now() > expiry_time:
                logger.debug(f"{cache_type}缓存已过期")
                return False
            
            logger.debug(f"{cache_type}缓存有效")
            return True
            
        except Exception as e:
            logger.error(f"检查{cache_type}缓存有效性失败: {e}")
            return False
    
    def get_cached_data(self, cache_type: str = "models") -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存数据
        
        Args:
            cache_type: 缓存类型 ("models" 或 "providers")
            
        Returns:
            缓存的数据列表，如果缓存无效则返回None
        """
        if not self.is_cache_valid(cache_type):
            return None
        
        try:
            cache_file = self.models_cache_file if cache_type == "models" else self.providers_cache_file
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"从缓存加载{cache_type}数据，共{len(data)}条记录")
            return data
            
        except Exception as e:
            logger.error(f"读取{cache_type}缓存失败: {e}")
            return None
    
    def save_cached_data(self, data: List[Dict[str, Any]], cache_type: str = "models") -> bool:
        """
        保存数据到缓存
        
        Args:
            data: 要缓存的数据
            cache_type: 缓存类型 ("models" 或 "providers")
            
        Returns:
            是否保存成功
        """
        try:
            # 确保缓存目录存在
            self._ensure_cache_dir()
            
            cache_file = self.models_cache_file if cache_type == "models" else self.providers_cache_file
            
            # 保存数据
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # 更新元数据
            metadata = self._get_cache_metadata()
            metadata[f"{cache_type}_last_update"] = datetime.now().isoformat()
            metadata[f"{cache_type}_count"] = len(data)
            self._save_cache_metadata(metadata)
            
            logger.info(f"{cache_type}数据已缓存，共{len(data)}条记录")
            return True
            
        except Exception as e:
            logger.error(f"保存{cache_type}缓存失败: {e}")
            return False
    
    def clear_cache(self, cache_type: Optional[str] = None) -> bool:
        """
        清理缓存
        
        Args:
            cache_type: 要清理的缓存类型，None表示清理所有缓存
            
        Returns:
            是否清理成功
        """
        try:
            if cache_type is None:
                # 清理整个缓存目录
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    logger.info("所有缓存已清理")
                else:
                    logger.info("缓存目录不存在，无需清理")
            else:
                # 清理特定类型的缓存
                cache_file = self.models_cache_file if cache_type == "models" else self.providers_cache_file
                
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"{cache_type}缓存已清理")
                
                # 更新元数据
                metadata = self._get_cache_metadata()
                metadata.pop(f"{cache_type}_last_update", None)
                metadata.pop(f"{cache_type}_count", None)
                self._save_cache_metadata(metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            缓存信息字典
        """
        info = {
            "cache_dir": str(self.cache_dir),
            "cache_ttl_hours": self.cache_ttl_hours,
            "cache_exists": self.cache_dir.exists(),
            "models_cache_valid": self.is_cache_valid("models"),
            "providers_cache_valid": self.is_cache_valid("providers")
        }
        
        # 添加元数据信息
        metadata = self._get_cache_metadata()
        info.update(metadata)
        
        return info
    
    async def start_auto_cleanup(self) -> None:
        """
        启动自动清理任务
        每小时清理一次过期缓存
        """
        logger.info("启动缓存自动清理任务")
        
        while True:
            try:
                await asyncio.sleep(3600)  # 等待1小时
                
                # 检查并清理过期缓存
                if not self.is_cache_valid("models"):
                    self.clear_cache("models")
                    logger.info("自动清理过期的models缓存")
                
                if not self.is_cache_valid("providers"):
                    self.clear_cache("providers")
                    logger.info("自动清理过期的providers缓存")
                    
            except Exception as e:
                logger.error(f"自动清理缓存任务出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续


# 全局缓存管理器实例
cache_manager = CacheManager()