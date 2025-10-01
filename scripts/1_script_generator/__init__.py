"""
脚本生成器模块
用于自动生成科普视频脚本
"""

from .generator import ScriptGenerator
from .ai_client import AIClient

__all__ = ['ScriptGenerator', 'AIClient']
