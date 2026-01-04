"""
任务管理器
用于管理后台任务，支持进度追踪和状态管理
适合小规模应用（2-5人），使用内存存储
"""
import uuid
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """任务模型"""

    def __init__(
        self,
        task_type: str,
        params: Dict[str, Any],
        task_id: Optional[str] = None
    ):
        """
        初始化任务

        Args:
            task_type: 任务类型（如 generate_topics, generate_script）
            params: 任务参数
            task_id: 任务ID（可选，自动生成）
        """
        self.id = task_id or f"{task_type}_{uuid.uuid4().hex[:8]}"
        self.type = task_type
        self.params = params
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.message = "任务已创建"
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type,
            "params": self.params,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class TaskManager:
    """
    任务管理器
    使用内存存储任务状态（适合小规模应用）
    """

    def __init__(self):
        """初始化任务管理器"""
        self.tasks: Dict[str, Task] = {}

    def create_task(
        self,
        task_type: str,
        params: Dict[str, Any]
    ) -> str:
        """
        创建新任务

        Args:
            task_type: 任务类型
            params: 任务参数

        Returns:
            任务ID
        """
        task = Task(task_type, params)
        self.tasks[task.id] = task
        return task.id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，如果任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None

    def update_progress(
        self,
        task_id: str,
        progress: int,
        message: str
    ) -> bool:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度百分比（0-100）
            message: 进度消息

        Returns:
            是否更新成功
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.progress = max(0, min(100, progress))
        task.message = message

        # 如果任务还在pending状态，更新为running
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

        return True

    def complete_task(
        self,
        task_id: str,
        result: Any
    ) -> bool:
        """
        完成任务

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            是否完成成功
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.result = result
        task.message = "任务完成"
        task.completed_at = datetime.now()

        return True

    def fail_task(
        self,
        task_id: str,
        error: str
    ) -> bool:
        """
        标记任务失败

        Args:
            task_id: 任务ID
            error: 错误信息

        Returns:
            是否标记成功
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.FAILED
        task.error = error
        task.message = f"任务失败: {error}"
        task.completed_at = datetime.now()

        return True

    def list_tasks(
        self,
        task_type: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> list:
        """
        列出任务

        Args:
            task_type: 过滤任务类型（可选）
            status: 过滤任务状态（可选）
            limit: 最大返回数量

        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())

        # 过滤
        if task_type:
            tasks = [t for t in tasks if t.type == task_type]
        if status:
            tasks = [t for t in tasks if t.status == status]

        # 按创建时间倒序排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # 限制数量
        tasks = tasks[:limit]

        return [task.to_dict() for task in tasks]

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def clear_old_tasks(self, keep_recent: int = 100) -> int:
        """
        清理旧任务（保留最近的N个）

        Args:
            keep_recent: 保留最近的任务数量

        Returns:
            清理的任务数量
        """
        # 按创建时间排序
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )

        # 保留最近的任务
        to_keep = sorted_tasks[:keep_recent]
        to_delete = sorted_tasks[keep_recent:]

        # 删除旧任务
        for task in to_delete:
            del self.tasks[task.id]

        return len(to_delete)


# 全局单例
_task_manager = None


def get_task_manager() -> TaskManager:
    """
    获取全局任务管理器实例

    Returns:
        TaskManager实例
    """
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
