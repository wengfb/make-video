"""
主题API路由
提供主题生成、查询、管理等功能
"""
from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from web.services.topic_service import get_topic_service
from web.services.task_manager import get_task_manager
from web.websocket.progress_handler import get_progress_handler


# 创建路由器
router = APIRouter(prefix="/api/topics", tags=["主题"])

# ==================== 数据模型 ====================


class GenerateTopicsRequest(BaseModel):
    """生成主题请求"""
    field: str = Field("", description="科学领域（如：physics, chemistry, biology）")
    audience: str = Field("general_public", description="目标受众")
    count: int = Field(10, ge=1, le=50, description="生成数量（1-50）")
    style: str = Field("educational", description="风格")
    custom_requirements: str = Field("", description="自定义要求")


class SaveTopicRequest(BaseModel):
    """保存主题请求"""
    id: str = Field(..., description="主题ID")
    title: str = Field(..., description="主题标题")
    description: str = Field(..., description="主题描述")
    field: str = Field(..., description="领域")
    target_audience: str = Field(..., description="目标受众")
    difficulty: str = Field(..., description="难度")
    key_points: List[str] = Field(default_factory=list, description="关键要点")
    estimated_popularity: str = Field("medium", description="预估流行度")
    visual_potential: str = Field("medium", description="视觉潜力")


class TopicResponse(BaseModel):
    """主题响应"""
    success: bool
    message: str
    data: Optional[dict] = None
    task_id: Optional[str] = None


# ==================== API端点 ====================


@router.post("/generate", response_model=TopicResponse)
async def generate_topics(
    request: GenerateTopicsRequest,
    background_tasks: BackgroundTasks
):
    """
    生成主题（异步）

    创建后台任务生成主题，立即返回task_id。
    客户端应通过WebSocket获取实时进度。

    Returns:
        任务ID
    """
    try:
        task_manager = get_task_manager()

        # 创建任务
        task_id = task_manager.create_task(
            "generate_topics",
            request.dict()
        )

        # 在后台执行生成任务
        topic_service = get_topic_service()
        background_tasks.add_task(
            topic_service.generate_topics_async,
            task_id,
            request.field,
            request.audience,
            request.count,
            request.style,
            request.custom_requirements
        )

        return TopicResponse(
            success=True,
            message="主题生成任务已创建",
            task_id=task_id
        )

    except Exception as e:
        return TopicResponse(
            success=False,
            message=f"创建生成任务失败: {str(e)}"
        )


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
async def list_topics(
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    field: Optional[str] = Query(None, description="领域过滤")
):
    """
    获取主题列表

    支持筛选
    """
    try:
        topic_service = get_topic_service()
        topics = topic_service.list_topics(
            limit=limit,
            field=field
        )

        return {
            "success": True,
            "topics": topics,
            "count": len(topics)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/{topic_id}")
async def get_topic(topic_id: str):
    """
    获取主题详情

    Args:
        topic_id: 主题ID

    Returns:
        主题详情
    """
    try:
        topic_service = get_topic_service()
        topic = topic_service.get_topic(topic_id)

        if not topic:
            return {
                "success": False,
                "error": "主题不存在"
            }

        return {
            "success": True,
            "topic": topic
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/save")
async def save_topic(request: SaveTopicRequest):
    """
    保存主题

    Args:
        request: 主题数据

    Returns:
        保存结果
    """
    try:
        topic_service = get_topic_service()
        topic_id = topic_service.save_topic(request.dict())

        return {
            "success": True,
            "message": "主题保存成功",
            "topic_id": topic_id
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/{topic_id}")
async def delete_topic(topic_id: str):
    """
    删除主题

    Args:
        topic_id: 主题ID

    Returns:
        删除结果
    """
    try:
        topic_service = get_topic_service()
        success = topic_service.delete_topic(topic_id)

        if success:
            return {
                "success": True,
                "message": "主题删除成功"
            }
        else:
            return {
                "success": False,
                "error": "主题不存在或删除失败"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/{topic_id}/favorite")
async def add_to_favorites(topic_id: str):
    """
    添加到收藏

    Args:
        topic_id: 主题ID

    Returns:
        操作结果
    """
    try:
        topic_service = get_topic_service()
        success = topic_service.add_to_favorites(topic_id)

        if success:
            return {
                "success": True,
                "message": "已添加到收藏"
            }
        else:
            return {
                "success": False,
                "error": "主题不存在或操作失败"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/search/{keyword}")
async def search_topics(
    keyword: str,
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    搜索主题

    Args:
        keyword: 搜索关键词
        limit: 返回数量

    Returns:
        搜索结果
    """
    try:
        topic_service = get_topic_service()
        topics = topic_service.search_topics(keyword, limit=limit)

        return {
            "success": True,
            "topics": topics,
            "count": len(topics)
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
        topic_service = get_topic_service()
        stats = topic_service.get_statistics()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
