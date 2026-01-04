"""
视频服务
封装VideoComposer，提供Web界面使用的业务逻辑
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from web.utils.module_loader import get_module_loader
from web.services.task_manager import get_task_manager


class VideoService:
    """视频服务类"""

    def __init__(self):
        """初始化视频服务"""
        self.loader = get_module_loader()

        # 动态加载VideoComposer
        VideoComposer = self.loader.load_video_composer()
        self.composer = VideoComposer()

    def compose_video_async(
        self,
        task_id: str,
        script_path: str,
        auto_select_materials: bool = True,
        material_ids: Optional[List[str]] = None,
        use_tts_audio: bool = False,
        tts_metadata_path: Optional[str] = None,
        subtitle_file: Optional[str] = None,
        video_options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        异步合成视频（后台任务）

        Args:
            task_id: 任务ID
            script_path: 脚本文件路径
            auto_select_materials: 是否自动选择素材
            material_ids: 手动指定的素材ID列表
            use_tts_audio: 是否使用TTS音频
            tts_metadata_path: TTS元数据文件路径
            subtitle_file: 字幕文件路径
            video_options: 视频选项（分辨率、帧率等）
        """
        task_manager = get_task_manager()

        def progress_callback(stage: str, progress: int, message: str):
            """进度回调函数

            Args:
                stage: 当前阶段（recommend_materials, generate_tts, compose等）
                progress: 进度百分比（0-100）
                message: 进度消息
            """
            # 计算总体进度（根据阶段权重）
            stage_weights = {
                "init": 0,
                "recommend_materials": 20,
                "generate_tts": 50,
                "compose": 90,
                "complete": 100
            }

            base_progress = stage_weights.get(stage, 0)
            stage_progress = progress * (stage_weights.get(stage, 100) / 100 - base_progress) / 100

            total_progress = int(base_progress + stage_progress)

            task_manager.update_progress(task_id, total_progress, f"[{stage}] {message}")

        try:
            progress_callback("init", 0, "初始化视频合成...")

            # 准备参数
            params = {
                "script_path": script_path,
                "auto_select_materials": auto_select_materials,
                "use_tts_audio": use_tts_audio,
            }

            if material_ids:
                params["material_map"] = self._build_material_map(material_ids, script_path)

            if tts_metadata_path:
                params["tts_metadata_path"] = tts_metadata_path

            if subtitle_file:
                params["subtitle_file"] = subtitle_file

            if video_options:
                params.update(video_options)

            progress_callback("recommend_materials", 10, "分析脚本章节...")

            # 调用VideoComposer合成视频
            result = self.composer.compose_from_script(
                progress_callback=progress_callback,
                **params
            )

            progress_callback("complete", 100, "视频合成完成")

            # 标记任务完成
            task_manager.complete_task(task_id, {
                "project_folder": result.get("project_folder"),
                "video_path": result.get("video_path"),
                "duration": result.get("duration", 0),
                "resolution": result.get("resolution", "1280x720"),
                "file_size": result.get("file_size", 0)
            })

        except Exception as e:
            # 任务失败
            error_msg = f"合成视频失败: {str(e)}"
            progress_callback("init", 0, error_msg)
            task_manager.fail_task(task_id, str(e))

    def _build_material_map(
        self,
        material_ids: List[str],
        script_path: str
    ) -> Dict[str, List[str]]:
        """
        构建素材映射字典

        Args:
            material_ids: 素材ID列表
            script_path: 脚本路径

        Returns:
            素材映射字典 {section_index: [material_ids]}
        """
        # 读取脚本获取章节数量
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script = json.load(f)

            section_count = len(script.get("sections", []))

            # 简单的轮询分配
            material_map = {}
            for i in range(section_count):
                material_map[str(i)] = [material_ids[i % len(material_ids)]]

            return material_map

        except Exception as e:
            print(f"构建素材映射失败: {e}")
            return {}

    def list_videos(self, videos_dir: str = "output/videos") -> List[Dict[str, Any]]:
        """
        列出所有视频

        Args:
            videos_dir: 视频目录

        Returns:
            视频信息列表
        """
        videos = []
        videos_path = Path(videos_dir)

        if not videos_path.exists():
            return videos

        for video_file in videos_path.glob("*.mp4"):
            try:
                # 获取文件信息
                stat = video_file.stat()

                videos.append({
                    "path": str(video_file),
                    "name": video_file.stem,
                    "file_name": video_file.name,
                    "file_size": stat.st_size,
                    "created_at": stat.st_mtime
                })
            except Exception as e:
                print(f"读取视频 {video_file} 失败: {e}")

        # 按创建时间倒序排序
        videos.sort(key=lambda x: x.get("created_at", 0), reverse=True)

        return videos

    def get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        获取视频详细信息

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息
        """
        try:
            from moviepy.editor import VideoFileClip

            clip = VideoFileClip(video_path)

            info = {
                "path": video_path,
                "name": Path(video_path).stem,
                "duration": clip.duration,
                "fps": clip.fps,
                "size": clip.size,
                "width": clip.w,
                "height": clip.h,
                "has_audio": clip.audio is not None
            }

            clip.close()

            return info

        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return None

    def preview_material_recommendations(
        self,
        script_path: str
    ) -> Dict[str, Any]:
        """
        预览素材推荐（不实际合成）

        Args:
            script_path: 脚本文件路径

        Returns:
            素材推荐结果
        """
        try:
            result = self.composer.preview_material_recommendations(script_path)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def delete_video(self, video_path: str) -> bool:
        """
        删除视频文件

        Args:
            video_path: 视频文件路径

        Returns:
            是否删除成功
        """
        try:
            Path(video_path).unlink()
            return True
        except Exception as e:
            print(f"删除视频失败: {e}")
            return False


# 全局单例
_video_service = None


def get_video_service() -> VideoService:
    """
    获取全局视频服务实例

    Returns:
        VideoService实例
    """
    global _video_service
    if _video_service is None:
        _video_service = VideoService()
    return _video_service
