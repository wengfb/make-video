"""
主题服务
封装TopicGenerator，提供Web界面使用的业务逻辑
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from web.utils.module_loader import get_module_loader
from web.services.task_manager import get_task_manager


class TopicService:
    """主题服务类"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化主题服务

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.loader = get_module_loader()

        # 动态加载TopicGenerator和TopicManager
        TopicGenerator = self.loader.load_topic_generator()
        TopicManager = self.loader.load_topic_manager()

        # TopicGenerator不需要参数，使用默认配置
        self.generator = TopicGenerator()
        # TopicManager需要data_dir参数
        self.manager = TopicManager(data_dir=data_dir)

    def generate_topics_async(
        self,
        task_id: str,
        field: str = "",
        audience: str = "general_public",
        count: int = 10,
        style: str = "educational",
        custom_requirements: str = ""
    ) -> None:
        """
        异步生成主题（后台任务）

        Args:
            task_id: 任务ID
            field: 科学领域
            audience: 目标受众
            difficulty: 难度级别
            count: 生成数量
            style: 风格
            custom_requirements: 自定义要求
        """
        task_manager = get_task_manager()

        def progress_callback(progress: int, message: str):
            """进度回调函数"""
            task_manager.update_progress(task_id, progress, message)

        try:
            # 开始生成
            progress_callback(5, "初始化AI客户端...")

            # 准备参数
            params = {
                "field": field if field else None,
                "audience": audience,
                "count": count,
                "style": style,
                "custom_requirements": custom_requirements if custom_requirements else None
            }

            progress_callback(10, "构建提示词...")

            # 调用TopicGenerator生成主题
            topics = self.generator.generate_topics(**params)

            progress_callback(90, f"成功生成 {len(topics)} 个主题")

            # 保存到数据库
            saved_topics = []
            for topic in topics:
                try:
                    # 保存主题到data/topics.json
                    saved_topic_id = self.manager.save_topic(topic)
                    topic['saved'] = True
                    topic['saved_id'] = saved_topic_id
                    saved_topics.append(topic)
                except Exception as e:
                    topic['saved'] = False
                    topic['save_error'] = str(e)
                    saved_topics.append(topic)

            progress_callback(100, f"完成！已生成 {len(topics)} 个主题")

            # 标记任务完成
            task_manager.complete_task(task_id, {
                "topics": saved_topics,
                "total": len(topics),
                "saved_count": sum(1 for t in saved_topics if t.get('saved', False))
            })

        except Exception as e:
            # 任务失败
            error_msg = f"生成主题失败: {str(e)}"
            progress_callback(0, error_msg)
            task_manager.fail_task(task_id, str(e))

    def get_topic(self, topic_id: str) -> Dict[str, Any]:
        """
        获取主题详情

        Args:
            topic_id: 主题ID

        Returns:
            主题信息
        """
        return self.manager.get_topic(topic_id)

    def list_topics(
        self,
        limit: int = 50,
        field: str = None,
        difficulty: str = None
    ) -> List[Dict[str, Any]]:
        """
        列出主题

        Args:
            limit: 返回数量
            field: 领域过滤
            difficulty: 难度过滤

        Returns:
            主题列表
        """
        return self.manager.list_topics(
            field=field,
            difficulty=difficulty,
            limit=limit
        )

    def search_topics(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索主题

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            搜索结果
        """
        return self.manager.search_topics(keyword, limit=limit)

    def save_topic(self, topic: Dict[str, Any]) -> str:
        """
        保存主题

        Args:
            topic: 主题数据

        Returns:
            主题ID
        """
        return self.manager.save_topic(topic)

    def delete_topic(self, topic_id: str) -> bool:
        """
        删除主题

        Args:
            topic_id: 主题ID

        Returns:
            是否删除成功
        """
        return self.manager.delete_topic(topic_id)

    def add_to_favorites(self, topic_id: str) -> bool:
        """
        添加到收藏

        Args:
            topic_id: 主题ID

        Returns:
            是否添加成功
        """
        return self.manager.add_to_favorites(topic_id)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        return self.manager.get_statistics()


# 全局单例
_topic_service = None


def get_topic_service() -> TopicService:
    """
    获取全局主题服务实例

    Returns:
        TopicService实例
    """
    global _topic_service
    if _topic_service is None:
        _topic_service = TopicService()
    return _topic_service
