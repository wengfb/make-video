"""
素材管理器模块
管理图片、视频、音频等素材资源
"""

from .manager import MaterialManager
from .ai_generator import AIImageGenerator
from .recommender import MaterialRecommender

__all__ = ['MaterialManager', 'AIImageGenerator', 'MaterialRecommender']
