"""
历史记录服务
基于TaskManager提供任务历史查询功能
"""
from typing import Dict, Any, List
from datetime import datetime
from web.services.task_manager import get_task_manager


class HistoryService:
    """历史记录服务类"""

    def __init__(self):
        """初始化历史记录服务"""
        self.task_manager = get_task_manager()

    def get_all_history(
        self,
        task_type: str = None,
        status: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取所有任务历史

        Args:
            task_type: 任务类型过滤
            status: 状态过滤
            limit: 返回数量限制

        Returns:
            任务历史列表
        """
        return self.task_manager.list_tasks(
            task_type=task_type,
            status=status,
            limit=limit
        )

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            任务详情
        """
        return self.task_manager.get_task(task_id)

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务记录

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        return self.task_manager.delete_task(task_id)

    def clear_old_tasks(self, keep_recent: int = 100) -> int:
        """
        清理旧任务

        Args:
            keep_recent: 保留最近的任务数量

        Returns:
            清理的任务数量
        """
        return self.task_manager.clear_old_tasks(keep_recent)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取历史统计信息

        Returns:
            统计数据
        """
        all_tasks = self.get_all_history(limit=10000)

        # 按类型统计
        type_counts = {}
        # 按状态统计
        status_counts = {}
        # 完成任务数
        completed_count = 0
        # 失败任务数
        failed_count = 0

        for task in all_tasks:
            # 类型统计
            task_type = task.get("type", "unknown")
            type_counts[task_type] = type_counts.get(task_type, 0) + 1

            # 状态统计
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            # 完成和失败统计
            if status == "completed":
                completed_count += 1
            elif status == "failed":
                failed_count += 1

        return {
            "total_tasks": len(all_tasks),
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "success_rate": completed_count / len(all_tasks) if all_tasks else 0,
            "type_distribution": type_counts,
            "status_distribution": status_counts
        }

    def get_recent_tasks(
        self,
        limit: int = 10,
        task_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取最近的任务

        Args:
            limit: 返回数量
            task_type: 任务类型过滤

        Returns:
            最近任务列表
        """
        return self.task_manager.list_tasks(
            task_type=task_type,
            limit=limit
        )


# 全局单例
_history_service = None


def get_history_service() -> HistoryService:
    """
    获取全局历史记录服务实例

    Returns:
        HistoryService实例
    """
    global _history_service
    if _history_service is None:
        _history_service = HistoryService()
    return _history_service
