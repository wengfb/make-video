"""
主题生成器核心模块
智能生成视频主题建议
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# 导入AI客户端 - 使用相对导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_script_generator'))
from ai_client import AIClient


class TopicGenerator:
    """智能主题生成器"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化主题生成器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 加载模板
        template_path = 'config/templates.json'
        with open(template_path, 'r', encoding='utf-8') as f:
            self.templates = json.load(f)

        # 初始化AI客户端
        self.ai_client = AIClient(self.config['ai'])

    def generate_topics(
        self,
        field: Optional[str] = None,
        audience: Optional[str] = None,
        count: int = 10,
        style: Optional[str] = None,
        custom_requirements: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        生成主题建议列表（带重试机制）

        Args:
            field: 科学领域（物理、化学、生物等）
            audience: 目标受众（学生、成人等）
            count: 生成主题数量
            style: 视频风格
            custom_requirements: 自定义要求

        Returns:
            主题列表
        """
        import time

        # 构建提示词
        prompt = self._build_topic_prompt(field, audience, count, style, custom_requirements)

        print(f"\n🤖 正在生成主题建议...")
        if field:
            print(f"   领域: {field}")
        if audience:
            print(f"   受众: {self._translate_audience(audience)}")
        print(f"   数量: {count}\n")

        # 业务层重试机制
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # 调用AI生成
                response = self.ai_client.generate_json(prompt)
                topics = response.get('topics', [])

                # 验证数据结构
                if not topics:
                    raise ValueError("AI返回的topics数组为空")

                if not isinstance(topics, list):
                    raise ValueError(f"AI返回的topics不是数组，类型: {type(topics)}")

                # 添加元数据和ID
                for i, topic in enumerate(topics, 1):
                    topic['id'] = self._generate_topic_id()
                    topic['generated_at'] = datetime.now().isoformat()
                    topic['field'] = field or topic.get('field', 'general')
                    topic['target_audience'] = audience or topic.get('target_audience', 'general_public')

                    # 确保必要字段存在
                    topic.setdefault('title', f'主题 {i}')
                    topic.setdefault('description', '')
                    topic.setdefault('difficulty', 'medium')
                    topic.setdefault('estimated_popularity', 'medium')
                    topic.setdefault('key_points', [])
                    topic.setdefault('visual_potential', 'medium')

                return topics

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  生成失败，{2}秒后重试 ({attempt + 1}/{max_retries})...")
                    print(f"   错误: {str(e)}")
                    time.sleep(2)
                else:
                    raise Exception(f"主题生成失败（已重试{max_retries}次）: {str(e)}")

    def generate_trending_topics(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        生成热门/趋势主题（带重试机制）

        Args:
            count: 生成数量

        Returns:
            主题列表
        """
        import time

        prompt = self.templates['prompt_templates']['trending_topics'].format(count=count)

        print(f"\n🔥 正在分析热门趋势，生成主题建议...\n")

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.ai_client.generate_json(prompt)
                topics = response.get('topics', [])

                # 验证数据结构
                if not topics:
                    raise ValueError("AI返回的topics数组为空")

                # 添加元数据
                for topic in topics:
                    topic['id'] = self._generate_topic_id()
                    topic['generated_at'] = datetime.now().isoformat()
                    topic['is_trending'] = True

                return topics

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  生成失败，{2}秒后重试 ({attempt + 1}/{max_retries})...")
                    print(f"   错误: {str(e)}")
                    time.sleep(2)
                else:
                    raise Exception(f"热门主题生成失败（已重试{max_retries}次）: {str(e)}")

    def expand_topic(self, topic_title: str) -> Dict[str, Any]:
        """
        扩展和丰富单个主题的详细信息

        Args:
            topic_title: 主题标题

        Returns:
            详细的主题信息
        """
        prompt = self.templates['prompt_templates']['expand_topic'].format(topic=topic_title)

        print(f"\n📝 正在扩展主题详情: {topic_title}\n")

        try:
            topic_detail = self.ai_client.generate_json(prompt)
            topic_detail['id'] = self._generate_topic_id()
            topic_detail['generated_at'] = datetime.now().isoformat()
            topic_detail['title'] = topic_title

            return topic_detail

        except Exception as e:
            raise Exception(f"主题扩展失败: {str(e)}")

    def analyze_topic_potential(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析主题的潜力（热度、难度、适合度等）

        Args:
            topic: 主题字典

        Returns:
            分析结果
        """
        topic_title = topic.get('title', '')
        topic_desc = topic.get('description', '')

        prompt = self.templates['prompt_templates']['analyze_topic'].format(
            title=topic_title,
            description=topic_desc
        )

        try:
            analysis = self.ai_client.generate_json(prompt)
            return analysis

        except Exception as e:
            # 如果分析失败，返回默认值
            return {
                'popularity_score': 5,
                'difficulty_score': 5,
                'visual_potential_score': 5,
                'audience_appeal': 'medium',
                'pros': [],
                'cons': [],
                'recommendations': []
            }

    def generate_topic_variations(self, base_topic: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        基于一个主题生成变体

        Args:
            base_topic: 基础主题
            count: 生成数量

        Returns:
            主题变体列表
        """
        prompt = self.templates['prompt_templates']['topic_variations'].format(
            topic=base_topic,
            count=count
        )

        print(f"\n🔄 正在生成主题变体: {base_topic}\n")

        try:
            response = self.ai_client.generate_json(prompt)
            variations = response.get('variations', [])

            # 添加元数据
            for variation in variations:
                variation['id'] = self._generate_topic_id()
                variation['generated_at'] = datetime.now().isoformat()
                variation['base_topic'] = base_topic

            return variations

        except Exception as e:
            raise Exception(f"主题变体生成失败: {str(e)}")

    def _build_topic_prompt(
        self,
        field: Optional[str],
        audience: Optional[str],
        count: int,
        style: Optional[str],
        custom_requirements: Optional[str]
    ) -> str:
        """构建主题生成提示词"""
        prompt_template = self.templates['prompt_templates']['topic_generation']

        # 构建参数
        field_desc = field if field else "各个科学领域"
        audience_desc = self._translate_audience(audience) if audience else "普通大众"
        style_desc = style if style else "科普视频"

        prompt = prompt_template.format(
            field=field_desc,
            audience=audience_desc,
            count=count,
            style=style_desc
        )

        if custom_requirements:
            prompt += f"\n\n额外要求：\n{custom_requirements}"

        return prompt

    def _translate_audience(self, audience: str) -> str:
        """翻译受众类型"""
        translations = {
            'general_public': '普通大众',
            'students': '学生群体',
            'children': '儿童观众',
            'teenagers': '青少年',
            'adults': '成年人',
            'professionals': '专业人士',
            'elderly': '老年人'
        }
        return translations.get(audience, audience)

    def _generate_topic_id(self) -> str:
        """生成唯一主题ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"topic_{timestamp}"

    def list_fields(self) -> List[str]:
        """
        列出支持的科学领域

        Returns:
            领域列表
        """
        return [
            "物理学",
            "化学",
            "生物学",
            "天文学",
            "地球科学",
            "数学",
            "计算机科学",
            "医学健康",
            "心理学",
            "环境科学",
            "工程技术",
            "综合科学"
        ]

    def list_audiences(self) -> List[Dict[str, str]]:
        """
        列出支持的受众类型

        Returns:
            受众列表
        """
        return [
            {"id": "children", "name": "儿童（6-12岁）", "description": "简单易懂，趣味性强"},
            {"id": "teenagers", "name": "青少年（13-18岁）", "description": "结合课程，深入浅出"},
            {"id": "adults", "name": "成年人", "description": "知识性与实用性并重"},
            {"id": "general_public", "name": "普通大众", "description": "适合所有年龄段"},
            {"id": "professionals", "name": "专业人士", "description": "深度专业内容"},
        ]
