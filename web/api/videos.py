"""
视频API路由
提供视频合成、查询、管理等功能
"""
from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from web.services.video_service import get_video_service
from web.services.script_service import get_script_service
from web.services.task_manager import get_task_manager


# 创建路由器
router = APIRouter(prefix="/api/videos", tags=["视频"])

# ==================== 数据模型 ====================


class ComposeVideoRequest(BaseModel):
    """合成视频请求"""
    script_path: str = Field(..., description="脚本文件路径")
    auto_select_materials: bool = Field(True, description="是否自动选择素材")
    material_ids: Optional[List[str]] = Field(None, description="手动指定的素材ID列表")
    use_tts_audio: bool = Field(False, description="是否使用TTS音频")
    tts_metadata_path: Optional[str] = Field(None, description="TTS元数据文件路径")
    subtitle_file: Optional[str] = Field(None, description="字幕文件路径")
    resolution: Optional[str] = Field("1280x720", description="分辨率")
    fps: Optional[int] = Field(24, description="帧率")


class PreviewMaterialsRequest(BaseModel):
    """预览素材推荐请求"""
    script_path: str = Field(..., description="脚本文件路径")


# ==================== API端点 ====================


@router.post("/compose")
async def compose_video(
    request: ComposeVideoRequest,
    background_tasks: BackgroundTasks
):
    """
    合成视频（异步）

    从脚本合成视频，支持自动素材推荐、TTS语音、字幕等
    """
    try:
        task_manager = get_task_manager()

        # 创建任务
        task_id = task_manager.create_task(
            "compose_video",
            request.dict()
        )

        # 准备视频选项
        video_options = {}
        if request.resolution:
            video_options["resolution"] = request.resolution
        if request.fps:
            video_options["fps"] = request.fps

        # 在后台执行合成任务
        video_service = get_video_service()
        background_tasks.add_task(
            video_service.compose_video_async,
            task_id,
            request.script_path,
            request.auto_select_materials,
            request.material_ids,
            request.use_tts_audio,
            request.tts_metadata_path,
            request.subtitle_file,
            video_options
        )

        return {
            "success": True,
            "message": "视频合成任务已创建",
            "task_id": task_id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"创建合成任务失败: {str(e)}"
        }


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态信息
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        return {"success": False, "error": "任务不存在"}

    return {
        "success": True,
        "task": task
    }


@router.get("/")
async def list_videos(
    limit: int = Query(50, ge=1, le=200, description="返回数量")
):
    """
    获取视频列表

    Returns:
        视频列表
    """
    try:
        video_service = get_video_service()
        videos = video_service.list_videos()

        # 限制返回数量
        videos = videos[:limit]

        # 格式化文件大小
        for video in videos:
            video["file_size_formatted"] = format_file_size(video.get("file_size", 0))

        return {
            "success": True,
            "videos": videos,
            "count": len(videos)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/{video_path:path}/info")
async def get_video_info(video_path: str):
    """
    获取视频详细信息

    Args:
        video_path: 视频文件路径（相对于output/videos）

    Returns:
        视频详情
    """
    try:
        video_service = get_video_service()

        # 构建完整路径
        full_path = f"output/videos/{video_path}"

        info = video_service.get_video_info(full_path)

        if not info:
            return {
                "success": False,
                "error": "视频不存在或无法读取"
            }

        return {
            "success": True,
            "info": info
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/{video_path:path}/download")
async def download_video(video_path: str):
    """
    下载视频

    Args:
        video_path: 视频文件路径

    Returns:
        视频文件
    """
    try:
        # 构建完整路径
        full_path = f"output/videos/{video_path}"

        video_path_obj = Path(full_path)
        if not video_path_obj.exists():
            return {
                "success": False,
                "error": "视频文件不存在"
            }

        return FileResponse(
            path=str(video_path_obj.absolute()),
            media_type="video/mp4",
            filename=video_path_obj.name
        )

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/{video_path:path}")
async def delete_video(video_path: str):
    """
    删除视频

    Args:
        video_path: 视频文件路径

    Returns:
        删除结果
    """
    try:
        video_service = get_video_service()

        # 构建完整路径
        full_path = f"output/videos/{video_path}"

        success = video_service.delete_video(full_path)

        if success:
            return {
                "success": True,
                "message": "视频删除成功"
            }
        else:
            return {
                "success": False,
                "error": "视频不存在或删除失败"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/preview-materials")
async def preview_materials(request: PreviewMaterialsRequest):
    """
    预览素材推荐

    返回将为脚本各章节推荐的素材，不实际合成视频

    Returns:
        素材推荐结果
    """
    try:
        video_service = get_video_service()
        result = video_service.preview_material_recommendations(request.script_path)

        return {
            "success": True,
            "preview": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/scripts/list")
async def list_available_scripts():
    """
    获取可用的脚本列表

    Returns:
        脚本列表（用于视频合成）
    """
    try:
        script_service = get_script_service()
        scripts = script_service.list_scripts()

        return {
            "success": True,
            "scripts": scripts
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/stats/summary")
async def get_statistics():
    """
    获取统计信息

    Returns:
        统计数据
    """
    try:
        video_service = get_video_service()
        videos = video_service.list_videos()

        total_size = sum(v.get("file_size", 0) for v in videos)

        return {
            "success": True,
            "stats": {
                "total_videos": len(videos),
                "total_size": total_size,
                "total_size_formatted": format_file_size(total_size),
                "average_size": total_size / len(videos) if videos else 0
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def format_file_size(bytes_size: int) -> str:
    """
    格式化文件大小

    Args:
        bytes_size: 字节数

    Returns:
        格式化后的大小
    """
    if bytes_size == 0:
        return "0 B"

    k = 1024
    sizes = ["B", "KB", "MB", "GB"]
    i = 0

    while bytes_size >= k and i < len(sizes) - 1:
        bytes_size /= k
        i += 1

    return f"{bytes_size:.2f} {sizes[i]}"
