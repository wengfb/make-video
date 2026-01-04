"""
脚本API路由
提供脚本生成、查询、管理等功能
"""
from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from web.services.script_service import get_script_service
from web.services.topic_service import get_topic_service
from web.services.task_manager import get_task_manager


# 创建路由器
router = APIRouter(prefix="/api/scripts", tags=["脚本"])

# ==================== 数据模型 ====================


class GenerateScriptRequest(BaseModel):
    """生成脚本请求"""
    topic: str = Field(..., description="主题（主题ID或主题标题）")
    template_name: str = Field("popular_science", description="模板名称")
    duration: str = Field("3-5min", description="视频时长")
    audience: str = Field("general_public", description="目标受众")
    custom_requirements: str = Field("", description="自定义要求")


class GenerateFromTopicRequest(BaseModel):
    """从主题生成脚本请求"""
    topic_id: str = Field(..., description="主题ID")
    template_name: str = Field("popular_science", description="模板名称")
    custom_requirements: str = Field("", description="自定义要求")


class SaveScriptRequest(BaseModel):
    """保存脚本请求"""
    script: dict = Field(..., description="脚本数据")
    filename: str = Field(None, description="文件名（可选）")


# ==================== API端点 ====================


@router.post("/generate")
async def generate_script(
    request: GenerateScriptRequest,
    background_tasks: BackgroundTasks
):
    """
    生成脚本（异步）

    从主题字符串生成视频脚本
    """
    try:
        task_manager = get_task_manager()

        # 创建任务
        task_id = task_manager.create_task(
            "generate_script",
            request.dict()
        )

        # 在后台执行生成任务
        script_service = get_script_service()
        background_tasks.add_task(
            script_service.generate_script_async,
            task_id,
            request.topic,
            request.template_name,
            request.duration,
            request.audience,
            request.custom_requirements
        )

        return {
            "success": True,
            "message": "脚本生成任务已创建",
            "task_id": task_id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"创建生成任务失败: {str(e)}"
        }


@router.post("/generate-from-topic")
async def generate_from_topic(
    request: GenerateFromTopicRequest,
    background_tasks: BackgroundTasks
):
    """
    从主题字典生成脚本（异步）

    使用已保存的主题数据生成脚本
    """
    try:
        # 获取主题数据
        topic_service = get_topic_service()
        topic = topic_service.get_topic(request.topic_id)

        if not topic:
            return {
                "success": False,
                "error": "主题不存在"
            }

        task_manager = get_task_manager()

        # 创建任务
        task_id = task_manager.create_task(
            "generate_script_from_topic",
            {
                "topic_id": request.topic_id,
                "template_name": request.template_name
            }
        )

        # 在后台执行生成任务
        script_service = get_script_service()
        background_tasks.add_task(
            script_service.generate_from_topic_async,
            task_id,
            topic,
            request.template_name,
            request.custom_requirements
        )

        return {
            "success": True,
            "message": "脚本生成任务已创建",
            "task_id": task_id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"创建生成任务失败: {str(e)}"
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
async def list_scripts(
    limit: int = Query(50, ge=1, le=200, description="返回数量")
):
    """
    获取脚本列表

    Returns:
        脚本列表
    """
    try:
        script_service = get_script_service()
        scripts = script_service.list_scripts()

        # 限制返回数量
        scripts = scripts[:limit]

        return {
            "success": True,
            "scripts": scripts,
            "count": len(scripts)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/templates/list")
async def list_templates():
    """
    获取可用的脚本模板列表

    Returns:
        模板列表
    """
    try:
        script_service = get_script_service()
        templates = script_service.list_templates()

        return {
            "success": True,
            "templates": templates
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
        script_service = get_script_service()
        scripts = script_service.list_scripts()

        total_duration = sum(s.get("duration", 0) for s in scripts)
        avg_duration = total_duration / len(scripts) if scripts else 0

        # 按模板统计
        template_counts = {}
        for script in scripts:
            template = script.get("template", "unknown")
            template_counts[template] = template_counts.get(template, 0) + 1

        return {
            "success": True,
            "stats": {
                "total_scripts": len(scripts),
                "total_duration": total_duration,
                "average_duration": avg_duration,
                "template_distribution": template_counts
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/{script_path:path}")
async def get_script(script_path: str):
    """
    获取脚本详情

    Args:
        script_path: 脚本文件路径（相对于output/scripts）

    Returns:
        脚本详情
    """
    try:
        script_service = get_script_service()

        # 构建完整路径
        full_path = f"output/scripts/{script_path}"

        script = script_service.get_script(full_path)

        if not script:
            return {
                "success": False,
                "error": "脚本不存在"
            }

        return {
            "success": True,
            "script": script
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/save")
async def save_script(request: SaveScriptRequest):
    """
    保存脚本

    Args:
        request: 保存请求

    Returns:
        保存结果
    """
    try:
        script_service = get_script_service()
        script_path = script_service.save_script(
            request.script,
            request.filename
        )

        return {
            "success": True,
            "message": "脚本保存成功",
            "script_path": script_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/{script_path:path}")
async def delete_script(script_path: str):
    """
    删除脚本

    Args:
        script_path: 脚本文件路径

    Returns:
        删除结果
    """
    try:
        script_service = get_script_service()

        # 构建完整路径
        full_path = f"output/scripts/{script_path}"

        success = script_service.delete_script(full_path)

        if success:
            return {
                "success": True,
                "message": "脚本删除成功"
            }
        else:
            return {
                "success": False,
                "error": "脚本不存在或删除失败"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/templates/list")
async def list_templates():
    """
    获取可用的脚本模板列表

    Returns:
        模板列表
    """
    try:
        script_service = get_script_service()
        templates = script_service.list_templates()

        return {
            "success": True,
            "templates": templates
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
        script_service = get_script_service()
        scripts = script_service.list_scripts()

        total_duration = sum(s.get("duration", 0) for s in scripts)
        avg_duration = total_duration / len(scripts) if scripts else 0

        # 按模板统计
        template_counts = {}
        for script in scripts:
            template = script.get("template", "unknown")
            template_counts[template] = template_counts.get(template, 0) + 1

        return {
            "success": True,
            "stats": {
                "total_scripts": len(scripts),
                "total_duration": total_duration,
                "average_duration": avg_duration,
                "template_distribution": template_counts
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
