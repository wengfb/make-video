"""
主题管理系统
管理主题的收藏、历史记录、评分等
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class TopicManager:
    """主题管理器"""

    def __init__(self, data_dir: str = 'data'):
        """
        初始化主题管理器

        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.topics_file = os.path.join(data_dir, 'topics.json')
        self.favorites_file = os.path.join(data_dir, 'favorites.json')
        self.history_file = os.path.join(data_dir, 'history.json')
        self.stats_file = os.path.join(data_dir, 'stats.json')

        # 初始化数据文件
        self._init_data_files()

    def _init_data_files(self):
        """初始化数据文件"""
        for file_path in [self.topics_file, self.favorites_file,
                          self.history_file, self.stats_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)

    def save_topic(self, topic: Dict[str, Any]) -> str:
        """
        保存主题

        Args:
            topic: 主题字典

        Returns:
            主题ID
        """
        topics = self._load_json(self.topics_file)

        # 检查是否已存在
        topic_id = topic.get('id')
        existing_index = None
        for i, t in enumerate(topics):
            if t.get('id') == topic_id:
                existing_index = i
                break

        # 添加保存时间
        topic['saved_at'] = datetime.now().isoformat()

        if existing_index is not None:
            # 更新现有主题
            topics[existing_index] = topic
        else:
            # 添加新主题
            topics.append(topic)

        self._save_json(self.topics_file, topics)
        return topic_id

    def get_topic(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """
        获取主题详情

        Args:
            topic_id: 主题ID

        Returns:
            主题字典或None
        """
        topics = self._load_json(self.topics_file)
        for topic in topics:
            if topic.get('id') == topic_id:
                return topic
        return None

    def list_topics(
        self,
        field: Optional[str] = None,
        difficulty: Optional[str] = None,
        sort_by: str = 'date',
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        列出主题

        Args:
            field: 筛选领域
            difficulty: 筛选难度
            sort_by: 排序方式 (date/rating/popularity)
            limit: 数量限制

        Returns:
            主题列表
        """
        topics = self._load_json(self.topics_file)

        # 筛选
        if field:
            topics = [t for t in topics if t.get('field') == field]
        if difficulty:
            topics = [t for t in topics if t.get('difficulty') == difficulty]

        # 排序
        if sort_by == 'date':
            topics.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
        elif sort_by == 'rating':
            topics.sort(key=lambda x: x.get('rating', 0), reverse=True)
        elif sort_by == 'popularity':
            topics.sort(key=lambda x: self._get_popularity_score(x), reverse=True)

        # 限制数量
        if limit:
            topics = topics[:limit]

        return topics

    def add_to_favorites(self, topic_id: str, note: Optional[str] = None) -> bool:
        """
        添加到收藏

        Args:
            topic_id: 主题ID
            note: 备注

        Returns:
            是否成功
        """
        favorites = self._load_json(self.favorites_file)

        # 检查是否已收藏
        for fav in favorites:
            if fav.get('topic_id') == topic_id:
                print(f"⚠️  主题已在收藏中")
                return False

        # 添加收藏
        favorite = {
            'topic_id': topic_id,
            'favorited_at': datetime.now().isoformat(),
            'note': note
        }
        favorites.append(favorite)
        self._save_json(self.favorites_file, favorites)

        print(f"⭐ 已添加到收藏")
        return True

    def remove_from_favorites(self, topic_id: str) -> bool:
        """
        从收藏中移除

        Args:
            topic_id: 主题ID

        Returns:
            是否成功
        """
        favorites = self._load_json(self.favorites_file)
        original_count = len(favorites)

        favorites = [f for f in favorites if f.get('topic_id') != topic_id]

        if len(favorites) < original_count:
            self._save_json(self.favorites_file, favorites)
            print(f"🗑️  已从收藏中移除")
            return True
        else:
            print(f"⚠️  主题不在收藏中")
            return False

    def list_favorites(self) -> List[Dict[str, Any]]:
        """
        列出收藏的主题

        Returns:
            主题列表
        """
        favorites = self._load_json(self.favorites_file)
        topics = []

        for fav in favorites:
            topic = self.get_topic(fav.get('topic_id'))
            if topic:
                topic['favorite_note'] = fav.get('note')
                topic['favorited_at'] = fav.get('favorited_at')
                topics.append(topic)

        return topics

    def is_favorite(self, topic_id: str) -> bool:
        """
        检查是否已收藏

        Args:
            topic_id: 主题ID

        Returns:
            是否已收藏
        """
        favorites = self._load_json(self.favorites_file)
        return any(f.get('topic_id') == topic_id for f in favorites)

    def rate_topic(self, topic_id: str, rating: int, comment: Optional[str] = None) -> bool:
        """
        为主题评分

        Args:
            topic_id: 主题ID
            rating: 评分 (1-5)
            comment: 评论

        Returns:
            是否成功
        """
        if not 1 <= rating <= 5:
            print(f"❌ 评分必须在1-5之间")
            return False

        topic = self.get_topic(topic_id)
        if not topic:
            print(f"❌ 主题不存在")
            return False

        topic['rating'] = rating
        topic['rating_comment'] = comment
        topic['rated_at'] = datetime.now().isoformat()

        self.save_topic(topic)
        print(f"⭐ 评分成功: {rating}/5")
        return True

    def add_to_history(self, topic_id: str, action: str, details: Optional[Dict] = None):
        """
        添加历史记录

        Args:
            topic_id: 主题ID
            action: 操作类型 (viewed/generated_script/used)
            details: 详细信息
        """
        history = self._load_json(self.history_file)

        record = {
            'topic_id': topic_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }

        history.append(record)
        self._save_json(self.history_file, history)

    def get_history(self, topic_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取历史记录

        Args:
            topic_id: 主题ID（可选，筛选特定主题）
            limit: 数量限制

        Returns:
            历史记录列表
        """
        history = self._load_json(self.history_file)

        if topic_id:
            history = [h for h in history if h.get('topic_id') == topic_id]

        # 按时间倒序
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return history[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        topics = self._load_json(self.topics_file)
        favorites = self._load_json(self.favorites_file)
        history = self._load_json(self.history_file)

        # 按领域统计
        field_stats = {}
        for topic in topics:
            field = topic.get('field', 'unknown')
            field_stats[field] = field_stats.get(field, 0) + 1

        # 按难度统计
        difficulty_stats = {}
        for topic in topics:
            difficulty = topic.get('difficulty', 'unknown')
            difficulty_stats[difficulty] = difficulty_stats.get(difficulty, 0) + 1

        # 评分统计
        rated_topics = [t for t in topics if 'rating' in t]
        avg_rating = sum(t.get('rating', 0) for t in rated_topics) / len(rated_topics) if rated_topics else 0

        return {
            'total_topics': len(topics),
            'total_favorites': len(favorites),
            'total_history_records': len(history),
            'by_field': field_stats,
            'by_difficulty': difficulty_stats,
            'rated_topics': len(rated_topics),
            'average_rating': round(avg_rating, 2),
            'last_updated': datetime.now().isoformat()
        }

    def search_topics(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索主题

        Args:
            keyword: 关键词

        Returns:
            匹配的主题列表
        """
        topics = self._load_json(self.topics_file)
        keyword_lower = keyword.lower()

        results = []
        for topic in topics:
            # 在标题、描述、关键点中搜索
            title = topic.get('title', '').lower()
            description = topic.get('description', '').lower()
            key_points = ' '.join(topic.get('key_points', [])).lower()

            if (keyword_lower in title or
                keyword_lower in description or
                keyword_lower in key_points):
                results.append(topic)

        return results

    def delete_topic(self, topic_id: str) -> bool:
        """
        删除主题

        Args:
            topic_id: 主题ID

        Returns:
            是否成功
        """
        topics = self._load_json(self.topics_file)
        original_count = len(topics)

        topics = [t for t in topics if t.get('id') != topic_id]

        if len(topics) < original_count:
            self._save_json(self.topics_file, topics)
            # 同时从收藏中移除
            self.remove_from_favorites(topic_id)
            print(f"🗑️  主题已删除")
            return True
        else:
            print(f"⚠️  主题不存在")
            return False

    def _get_popularity_score(self, topic: Dict[str, Any]) -> float:
        """计算主题流行度评分"""
        score = 0.0

        # 基础评分
        popularity = topic.get('estimated_popularity', 'medium')
        popularity_scores = {'low': 1, 'medium': 3, 'high': 5}
        score += popularity_scores.get(popularity, 3)

        # 用户评分
        if 'rating' in topic:
            score += topic['rating']

        # 使用次数（从历史记录中统计）
        history = self.get_history(topic.get('id'))
        score += len(history) * 0.5

        # 是否收藏
        if self.is_favorite(topic.get('id')):
            score += 2

        return score

    def _load_json(self, file_path: str) -> List:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, file_path: str, data: List):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
