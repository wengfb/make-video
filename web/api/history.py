"""
历史记录API路由
提供任务历史查询和管理功能
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional
from web.services.history_service import get_history_service


# 创建路由器
router = APIRouter(prefix="/api/history", tags=["历史记录"])

# ==================== API端点 ====================


@router.get("/")
async def list_history(
    task_type: Optional[str] = Query(None, description="任务类型"),
    status: Optional[str] = Query(None, description="任务状态"),
    limit: int = Query(100, ge=1, le=500, description="返回数量")
):
    """
    获取任务历史列表

    支持按类型和状态筛选
    """
    try:
        history_service = get_history_service()
        tasks = history_service.get_all_history(
            task_type=task_type,
            status=status,
            limit=limit
        )

        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/recent")
async def get_recent_tasks(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    task_type: Optional[str] = Query(None, description="任务类型")
):
    """
    获取最近的任务

    用于首页仪表盘显示
    """
    try:
        history_service = get_history_service()
        tasks = history_service.get_recent_tasks(
            limit=limit,
            task_type=task_type
        )

        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/{task_id}")
async def get_task_details(task_id: str):
    """
    获取任务详情

    Args:
        task_id: 任务ID

    Returns:
        任务详情
    """
    try:
        history_service = get_history_service()
        task = history_service.get_task(task_id)

        if not task:
            return {
                "success": False,
                "error": "任务不存在"
            }

        return {
            "success": True,
            "task": task
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务记录

    Args:
        task_id: 任务ID

    Returns:
        删除结果
    """
    try:
        history_service = get_history_service()
        success = history_service.delete_task(task_id)

        if success:
            return {
                "success": True,
                "message": "任务记录删除成功"
            }
        else:
            return {
                "success": False,
                "error": "任务不存在或删除失败"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/clear")
async def clear_old_tasks(
    keep_recent: int = Query(100, ge=10, le=1000, description="保留最近任务数量")
):
    """
    清理旧任务记录

    Args:
        keep_recent: 保留最近的任务数量

    Returns:
        清理结果
    """
    try:
        history_service = get_history_service()
        deleted_count = history_service.clear_old_tasks(keep_recent)

        return {
            "success": True,
            "message": f"已清理 {deleted_count} 条旧任务记录",
            "deleted_count": deleted_count
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/stats/summary")
async def get_statistics():
    """
    获取历史统计信息

    Returns:
        统计数据
    """
    try:
        history_service = get_history_service()
        stats = history_service.get_statistics()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
