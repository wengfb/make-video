"""
TTS语音服务
封装TTSGenerator，提供Web界面使用的业务逻辑
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from web.utils.module_loader import get_module_loader
from web.services.task_manager import get_task_manager


class TTSService:
    """TTS语音服务类"""

    def __init__(self):
        """初始化TTS服务"""
        self.loader = get_module_loader()

        # 动态加载TTSGenerator和TTSManager
        TTSGenerator = self.loader.load_tts_generator()
        TTSManager = self.loader.load_tts_manager()

        self.generator = TTSGenerator()
        self.manager = TTSManager()

    def generate_speech_async(
        self,
        task_id: str,
        script_path: str,
        output_name: str = None,
        voice: str = "alloy"
    ) -> None:
        """
        异步生成TTS语音（后台任务）

        Args:
            task_id: 任务ID
            script_path: 脚本文件路径
            output_name: 输出名称
            voice: TTS声音
        """
        task_manager = get_task_manager()

        def progress_callback(progress: int, message: str):
            """进度回调函数"""
            task_manager.update_progress(task_id, progress, message)

        try:
            progress_callback(10, "读取脚本文件...")

            # 读取脚本
            with open(script_path, 'r', encoding='utf-8') as f:
                script = json.load(f)

            section_count = len(script.get("sections", []))

            progress_callback(20, f"开始生成 {section_count} 段语音...")

            # 调用TTSGenerator生成语音
            result = self.generator.generate_speech_from_script(
                script_path=script_path,
                output_name=output_name,
                voice=voice
            )

            progress_callback(100, f"成功生成 {result.get('total_sections', 0)} 段语音")

            # 标记任务完成
            task_manager.complete_task(task_id, {
                "metadata_path": result.get("metadata_path"),
                "audio_files": result.get("audio_files", []),
                "total_duration": result.get("total_duration", 0),
                "total_sections": result.get("total_sections", 0),
                "voice": result.get("metadata", {}).get("voice", voice)
            })

        except Exception as e:
            # 任务失败
            error_msg = f"生成TTS失败: {str(e)}"
            progress_callback(0, error_msg)
            task_manager.fail_task(task_id, str(e))

    def list_available_voices(self) -> List[str]:
        """
        列出可用的TTS声音

        Returns:
            声音列表
        """
        try:
            voices = self.generator.list_available_voices()
            return voices
        except Exception as e:
            print(f"获取声音列表失败: {e}")
            # 返回默认声音列表
            return [
                "alloy",
                "echo",
                "fable",
                "onyx",
                "nova",
                "shimmer"
            ]

    def list_all_audio(self) -> List[Dict[str, Any]]:
        """
        列出所有TTS音频文件

        Returns:
            音频文件列表
        """
        try:
            audio_list = self.manager.list_all_audio()
            return audio_list
        except Exception as e:
            print(f"获取音频列表失败: {e}")
            return []

    def get_audio_by_script(self, script_title: str) -> List[Dict[str, Any]]:
        """
        根据脚本标题获取TTS音频

        Args:
            script_title: 脚本标题

        Returns:
            音频文件列表
        """
        try:
            audio_files = self.manager.get_audio_by_script(script_title)
            return audio_files
        except Exception as e:
            print(f"获取音频失败: {e}")
            return []

    def merge_audio_files(
        self,
        audio_paths: List[str],
        output_path: str
    ) -> str:
        """
        合并多个音频文件

        Args:
            audio_paths: 音频文件路径列表
            output_path: 输出文件路径

        Returns:
            合并后的文件路径
        """
        try:
            result_path = self.manager.merge_audio_files(audio_paths, output_path)
            return result_path
        except Exception as e:
            raise Exception(f"合并音频失败: {str(e)}")


# 全局单例
_tts_service = None


def get_tts_service() -> TTSService:
    """
    获取全局TTS服务实例

    Returns:
        TTSService实例
    """
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
