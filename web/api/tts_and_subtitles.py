"""
TTS和字幕API路由
提供语音合成和字幕生成功能
"""
from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from web.services.tts_service import get_tts_service
from web.services.subtitle_service import get_subtitle_service
from web.services.task_manager import get_task_manager


# 创建路由器
tts_router = APIRouter(prefix="/api/tts", tags=["TTS语音"])
subtitle_router = APIRouter(prefix="/api/subtitles", tags=["字幕"])

# ==================== 数据模型 ====================


class GenerateTTSRequest(BaseModel):
    """生成TTS请求"""
    script_path: str = Field(..., description="脚本文件路径")
    output_name: str = Field(None, description="输出名称")
    voice: str = Field("alloy", description="TTS声音")


class GenerateSubtitleRequest(BaseModel):
    """生成字幕请求"""
    script_path: str = Field(..., description="脚本文件路径")
    audio_metadata_path: str = Field(None, description="音频元数据路径")
    output_name: str = Field(None, description="输出名称")
    format: str = Field("srt", description="字幕格式（srt或ass）")


# ==================== TTS API端点 ====================


@tts_router.post("/generate")
async def generate_tts(
    request: GenerateTTSRequest,
    background_tasks: BackgroundTasks
):
    """
    生成TTS语音（异步）

    从脚本生成AI语音旁白
    """
    try:
        task_manager = get_task_manager()

        # 创建任务
        task_id = task_manager.create_task(
            "generate_tts",
            request.dict()
        )

        # 在后台执行生成任务
        tts_service = get_tts_service()
        background_tasks.add_task(
            tts_service.generate_speech_async,
            task_id,
            request.script_path,
            request.output_name,
            request.voice
        )

        return {
            "success": True,
            "message": "TTS生成任务已创建",
            "task_id": task_id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"创建生成任务失败: {str(e)}"
        }


@tts_router.get("/task/{task_id}")
async def get_tts_task_status(task_id: str):
    """获取TTS任务状态"""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        return {"success": False, "error": "任务不存在"}

    return {
        "success": True,
        "task": task
    }


@tts_router.get("/")
async def list_tts_audio(
    limit: int = Query(50, ge=1, le=200, description="返回数量")
):
    """获取TTS音频列表"""
    try:
        tts_service = get_tts_service()
        audio_list = tts_service.list_all_audio()

        # 限制返回数量
        audio_list = audio_list[:limit]

        return {
            "success": True,
            "audio_files": audio_list,
            "count": len(audio_list)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tts_router.get("/voices")
async def list_voices():
    """获取可用的TTS声音列表"""
    try:
        tts_service = get_tts_service()
        voices = tts_service.list_available_voices()

        return {
            "success": True,
            "voices": voices
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tts_router.get("/{script_title}/audio")
async def get_audio_by_script(script_title: str):
    """根据脚本标题获取TTS音频"""
    try:
        tts_service = get_tts_service()
        audio_files = tts_service.get_audio_by_script(script_title)

        return {
            "success": True,
            "audio_files": audio_files
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tts_router.get("/stats/summary")
async def get_tts_statistics():
    """获取TTS统计信息"""
    try:
        tts_service = get_tts_service()
        audio_list = tts_service.list_all_audio()

        total_duration = sum(
            sum(a.get("duration", 0) for a in audios)
            for audios in audio_list
        )

        return {
            "success": True,
            "stats": {
                "total_scripts": len(audio_list),
                "total_duration": total_duration
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== 字幕API端点 ====================


@subtitle_router.post("/generate")
async def generate_subtitle(
    request: GenerateSubtitleRequest,
    background_tasks: BackgroundTasks
):
    """
    生成字幕（异步）

    从脚本生成字幕文件（SRT/ASS格式）
    """
    try:
        task_manager = get_task_manager()

        # 创建任务
        task_id = task_manager.create_task(
            "generate_subtitle",
            request.dict()
        )

        # 在后台执行生成任务
        subtitle_service = get_subtitle_service()
        background_tasks.add_task(
            subtitle_service.generate_subtitle_async,
            task_id,
            request.script_path,
            request.audio_metadata_path,
            request.output_name,
            request.format
        )

        return {
            "success": True,
            "message": "字幕生成任务已创建",
            "task_id": task_id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"创建生成任务失败: {str(e)}"
        }


@subtitle_router.get("/task/{task_id}")
async def get_subtitle_task_status(task_id: str):
    """获取字幕任务状态"""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        return {"success": False, "error": "任务不存在"}

    return {
        "success": True,
        "task": task
    }


@subtitle_router.get("/")
async def list_subtitles(
    limit: int = Query(50, ge=1, le=200, description="返回数量")
):
    """获取字幕文件列表"""
    try:
        subtitle_service = get_subtitle_service()
        subtitles = subtitle_service.list_subtitles()

        # 限制返回数量
        subtitles = subtitles[:limit]

        return {
            "success": True,
            "subtitles": subtitles,
            "count": len(subtitles)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@subtitle_router.get("/{subtitle_path:path}/download")
async def download_subtitle(subtitle_path: str):
    """
    下载字幕文件

    Args:
        subtitle_path: 字幕文件路径（相对于output/subtitles）

    Returns:
        字幕文件
    """
    try:
        # 构建完整路径
        full_path = f"output/subtitles/{subtitle_path}"

        subtitle_path_obj = Path(full_path)
        if not subtitle_path_obj.exists():
            return {
                "success": False,
                "error": "字幕文件不存在"
            }

        # 根据格式确定媒体类型
        media_type = "text/plain"
        if subtitle_path_obj.suffix == ".srt":
            media_type = "text/srt"
        elif subtitle_path_obj.suffix == ".ass":
            media_type = "text/x-ssa"

        return FileResponse(
            path=str(subtitle_path_obj.absolute()),
            media_type=media_type,
            filename=subtitle_path_obj.name
        )

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@subtitle_router.delete("/{subtitle_path:path}")
async def delete_subtitle(subtitle_path: str):
    """删除字幕文件"""
    try:
        subtitle_service = get_subtitle_service()

        # 构建完整路径
        full_path = f"output/subtitles/{subtitle_path}"

        success = subtitle_service.delete_subtitle(full_path)

        if success:
            return {
                "success": True,
                "message": "字幕删除成功"
            }
        else:
            return {
                "success": False,
                "error": "字幕不存在或删除失败"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@subtitle_router.get("/stats/summary")
async def get_subtitle_statistics():
    """获取字幕统计信息"""
    try:
        subtitle_service = get_subtitle_service()
        subtitles = subtitle_service.list_subtitles()

        # 按格式统计
        format_counts = {}
        for sub in subtitles:
            fmt = sub.get("format", "unknown")
            format_counts[fmt] = format_counts.get(fmt, 0) + 1

        return {
            "success": True,
            "stats": {
                "total_subtitles": len(subtitles),
                "format_distribution": format_counts
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
