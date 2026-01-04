"""
字幕服务
封装SubtitleGenerator，提供Web界面使用的业务逻辑
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from web.utils.module_loader import get_module_loader
from web.services.task_manager import get_task_manager


class SubtitleService:
    """字幕服务类"""

    def __init__(self):
        """初始化字幕服务"""
        self.loader = get_module_loader()

        # 动态加载SubtitleGenerator
        SubtitleGenerator = self.loader.load_subtitle_generator()

        self.generator = SubtitleGenerator()

    def generate_subtitle_async(
        self,
        task_id: str,
        script_path: str,
        audio_metadata_path: str = None,
        output_name: str = None,
        format: str = "srt"
    ) -> None:
        """
        异步生成字幕（后台任务）

        Args:
            task_id: 任务ID
            script_path: 脚本文件路径
            audio_metadata_path: 音频元数据文件路径（用于时间轴对齐）
            output_name: 输出名称
            format: 字幕格式（srt或ass）
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

            progress_callback(20, f"生成 {section_count} 个章节的字幕...")

            # 调用SubtitleGenerator生成字幕
            result = self.generator.generate_from_script(
                script_path=script_path,
                audio_metadata_path=audio_metadata_path,
                output_name=output_name,
                format=format
            )

            progress_callback(100, f"字幕生成完成 ({format.upper()}格式)")

            # 标记任务完成
            task_manager.complete_task(task_id, {
                "subtitle_path": result.get("subtitle_path"),
                "format": result.get("format", format),
                "section_count": section_count
            })

        except Exception as e:
            # 任务失败
            error_msg = f"生成字幕失败: {str(e)}"
            progress_callback(0, error_msg)
            task_manager.fail_task(task_id, str(e))

    def list_subtitles(self, subtitles_dir: str = "output/subtitles") -> List[Dict[str, Any]]:
        """
        列出所有字幕文件

        Args:
            subtitles_dir: 字幕目录

        Returns:
            字幕文件列表
        """
        subtitles = []
        subtitles_path = Path(subtitles_dir)

        if not subtitles_path.exists():
            return subtitles

        for subtitle_file in subtitles_path.glob("*"):
            try:
                # 获取文件信息
                stat = subtitle_file.stat()

                subtitles.append({
                    "path": str(subtitle_file),
                    "name": subtitle_file.stem,
                    "file_name": subtitle_file.name,
                    "format": subtitle_file.suffix[1:],  # 去掉点号
                    "file_size": stat.st_size,
                    "created_at": stat.st_mtime
                })
            except Exception as e:
                print(f"读取字幕文件 {subtitle_file} 失败: {e}")

        # 按创建时间倒序排序
        subtitles.sort(key=lambda x: x.get("created_at", 0), reverse=True)

        return subtitles

    def delete_subtitle(self, subtitle_path: str) -> bool:
        """
        删除字幕文件

        Args:
            subtitle_path: 字幕文件路径

        Returns:
            是否删除成功
        """
        try:
            Path(subtitle_path).unlink()
            return True
        except Exception as e:
            print(f"删除字幕失败: {e}")
            return False


# 全局单例
_subtitle_service = None


def get_subtitle_service() -> SubtitleService:
    """
    获取全局字幕服务实例

    Returns:
        SubtitleService实例
    """
    global _subtitle_service
    if _subtitle_service is None:
        _subtitle_service = SubtitleService()
    return _subtitle_service
