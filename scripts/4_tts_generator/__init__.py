"""
TTS (Text-to-Speech) 语音合成模块
用于将脚本文字转换为语音
"""

from .generator import TTSGenerator
from .manager import TTSManager

__all__ = ['TTSGenerator', 'TTSManager']
