"""
WebSocket连接管理器
管理WebSocket连接，支持进度推送
"""
from fastapi import WebSocket
from typing import Dict, Set
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket连接管理器
    """

    def __init__(self):
        """初始化连接管理器"""
        # 存储活跃连接: {task_id: set of websockets}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """
        接受新连接

        Args:
            websocket: WebSocket连接
            task_id: 任务ID
        """
        await websocket.accept()

        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()

        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket连接建立: task_id={task_id}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        """
        断开连接

        Args:
            websocket: WebSocket连接
            task_id: 任务ID
        """
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)

            # 如果该任务没有其他连接了，删除key
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

        logger.info(f"WebSocket连接断开: task_id={task_id}")

    async def send_progress(self, task_id: str, progress_data: dict):
        """
        向指定任务的所有连接发送进度

        Args:
            task_id: 任务ID
            progress_data: 进度数据
        """
        if task_id not in self.active_connections:
            return

        # 向所有连接该任务的客户端发送消息
        disconnected = set()
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(progress_data)
            except Exception as e:
                logger.error(f"发送进度失败: {e}")
                disconnected.add(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection, task_id)

    async def broadcast(self, message: dict):
        """
        向所有连接广播消息

        Args:
            message: 消息内容
        """
        for task_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"广播消息失败: {e}")


class ProgressHandler:
    """
    进度推送处理器
    """

    def __init__(self):
        """初始化进度处理器"""
        self.manager = ConnectionManager()

    async def handle_progress_websocket(
        self,
        websocket: WebSocket,
        task_id: str
    ):
        """
        处理进度WebSocket连接

        Args:
            websocket: WebSocket连接
            task_id: 任务ID
        """
        # 接受连接
        await self.manager.connect(websocket, task_id)

        try:
            # 导入task_manager（避免循环导入）
            from web.services.task_manager import get_task_manager
            task_manager = get_task_manager()

            # 持续推送进度直到任务完成
            while True:
                task = task_manager.get_task(task_id)

                if not task:
                    # 任务不存在，发送错误并关闭
                    await websocket.send_json({
                        "error": "任务不存在",
                        "task_id": task_id
                    })
                    break

                # 发送当前进度
                await websocket.send_json({
                    "task_id": task_id,
                    "status": task["status"],
                    "progress": task["progress"],
                    "message": task["message"],
                    "result": task.get("result"),
                    "error": task.get("error"),
                    "created_at": task["created_at"]
                })

                # 检查任务状态
                if task["status"] in ["completed", "failed"]:
                    logger.info(f"任务 {task_id} 已完成，关闭WebSocket")
                    break

                # 等待1秒后再次检查
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"WebSocket处理错误: {e}")
            await websocket.send_json({
                "error": str(e),
                "task_id": task_id
            })

        finally:
            # 清理连接
            self.manager.disconnect(websocket, task_id)
            await websocket.close()


# 全局单例
_progress_handler = None


def get_progress_handler() -> ProgressHandler:
    """
    获取全局进度处理器实例

    Returns:
        ProgressHandler实例
    """
    global _progress_handler
    if _progress_handler is None:
        _progress_handler = ProgressHandler()
    return _progress_handler
