"""
AI语义分析器
根据章节内容分析语义特征，为智能动效提供决策依据
"""

import sys
import os
from typing import Dict, Any, List, Optional

# 导入AI客户端
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_script_generator'))
from ai_client import AIClient


class SemanticAnalyzer:
    """章节语义分析器"""

    def __init__(self, ai_client: Optional[AIClient] = None, use_ai: bool = True):
        """
        初始化语义分析器

        Args:
            ai_client: AI客户端实例（可选）
            use_ai: 是否使用AI增强分析
        """
        self.ai_client = ai_client
        self.use_ai = use_ai and ai_client is not None

        # 章节类型特征库
        self.section_profiles = {
            'hook': {
                'emotion': 'excitement',      # 兴奋
                'energy': 'high',             # 高能量
                'pace': 'fast',               # 快节奏
                'visual_style': 'dynamic',    # 动态
                'base_energy': 9.0
            },
            'introduction': {
                'emotion': 'curiosity',
                'energy': 'medium',
                'pace': 'moderate',
                'visual_style': 'smooth',
                'base_energy': 6.0
            },
            'background': {
                'emotion': 'calm',
                'energy': 'low',
                'pace': 'slow',
                'visual_style': 'educational',
                'base_energy': 4.0
            },
            'main_content': {
                'emotion': 'focus',
                'energy': 'medium-high',
                'pace': 'varied',
                'visual_style': 'explanatory',
                'base_energy': 7.0
            },
            'application': {
                'emotion': 'inspired',
                'energy': 'medium',
                'pace': 'moderate',
                'visual_style': 'practical',
                'base_energy': 6.5
            },
            'summary': {
                'emotion': 'satisfied',
                'energy': 'medium-low',
                'pace': 'slow',
                'visual_style': 'conclusive',
                'base_energy': 5.0
            },
            'cta': {
                'emotion': 'motivated',
                'energy': 'high',
                'pace': 'fast',
                'visual_style': 'engaging',
                'base_energy': 8.5
            }
        }

        # 高能量关键词
        self.high_energy_keywords = [
            '惊人', '震撼', '突破', '发现', '革命', '颠覆',
            '神奇', '不可思议', '揭秘', '爆炸', '飞速', '惊艳',
            '巨大', '重大', '关键', '核心', '重要', '必须'
        ]

        # 平静关键词
        self.calm_keywords = [
            '基础', '了解', '认识', '理解', '简单', '基本',
            '平稳', '逐步', '缓慢', '稳定', '慢慢', '渐渐',
            '轻松', '容易', '温和'
        ]

    def analyze_section(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析章节语义特征

        Args:
            section: 脚本章节字典

        Returns:
            分析结果字典，包含：
            - section_type: 章节类型
            - emotion: 情绪
            - energy_level: 能量等级(0-10)
            - pace: 节奏
            - content_keywords: 内容关键词
            - visual_intensity: 视觉强度
            - base_profile: 基础特征
        """
        section_name = section.get('section_name', '')
        narration = section.get('narration', '')
        visual_notes = section.get('visual_notes', '')

        # 1. 识别章节类型
        section_type = self._identify_section_type(section)

        # 2. 提取关键词
        keywords = self._extract_semantic_keywords(narration)

        # 3. AI情感分析（可选）
        emotion_analysis = None
        if self.use_ai:
            emotion_analysis = self._ai_emotion_analysis(narration)

        # 4. 计算能量等级
        energy_level = self._calculate_energy_level(
            section_type,
            emotion_analysis,
            keywords
        )

        # 5. 获取基础特征
        profile = self.section_profiles.get(section_type, {})

        return {
            'section_type': section_type,
            'emotion': profile.get('emotion', 'neutral'),
            'energy_level': energy_level,
            'pace': profile.get('pace', 'moderate'),
            'content_keywords': keywords,
            'visual_intensity': self._map_energy_to_intensity(energy_level),
            'base_profile': profile
        }

    def _identify_section_type(self, section: Dict[str, Any]) -> str:
        """
        识别章节类型

        优先级：
        1. section字段（如果存在）
        2. 通过章节名称匹配
        3. 默认为main_content
        """
        # 优先使用section字段
        if 'section' in section:
            return section['section']

        # 通过名称匹配
        name = section.get('section_name', '').lower()

        type_keywords = {
            'hook': ['开场', '钩子', 'hook', '引子', '吸引'],
            'introduction': ['介绍', '导入', 'intro', '引言', '前言'],
            'background': ['背景', '基础', 'background', '基本', '前置'],
            'main_content': ['核心', '主要', '正文', 'main', '内容', '讲解'],
            'application': ['应用', '实践', 'application', '应用', '实际'],
            'summary': ['总结', '回顾', 'summary', '结论', '小结'],
            'cta': ['行动', '号召', 'cta', '互动', '关注']
        }

        for section_type, keywords in type_keywords.items():
            if any(kw in name for kw in keywords):
                return section_type

        return 'main_content'  # 默认

    def _extract_semantic_keywords(self, text: str) -> List[str]:
        """
        提取语义关键词

        Args:
            text: 文本内容

        Returns:
            关键词列表
        """
        found_keywords = []

        # 检查高能量词汇
        for word in self.high_energy_keywords:
            if word in text:
                found_keywords.append(('high', word))

        # 检查平静词汇
        for word in self.calm_keywords:
            if word in text:
                found_keywords.append(('calm', word))

        return found_keywords[:5]

    def _ai_emotion_analysis(self, text: str) -> Optional[Dict[str, Any]]:
        """
        AI情感分析（增强版）

        Args:
            text: 文本内容

        Returns:
            情感分析结果或None
        """
        if not self.ai_client:
            return None

        try:
            prompt = f"""分析以下文本的情感和能量特征，仅输出JSON：

文本: {text[:200]}

输出格式:
{{
    "emotion": "excitement/curiosity/calm/focus/inspired/satisfied",
    "intensity": 7.5,
    "keywords": ["惊人", "突破"],
    "visual_mood": "dynamic/smooth/static"
}}"""

            result = self.ai_client.generate_json(prompt)
            return result
        except Exception as e:
            print(f"   ⚠️  AI情感分析失败: {str(e)}")
            return None

    def _calculate_energy_level(
        self,
        section_type: str,
        emotion_analysis: Optional[Dict],
        keywords: List[tuple]
    ) -> float:
        """
        计算章节能量等级（0-10）

        综合考虑：
        1. 章节类型基础能量
        2. AI情感分析强度
        3. 关键词加成

        Args:
            section_type: 章节类型
            emotion_analysis: AI情感分析结果
            keywords: 关键词列表

        Returns:
            能量等级(0-10)
        """
        # 1. 基础能量
        profile = self.section_profiles.get(section_type, {})
        energy = profile.get('base_energy', 5.0)

        # 2. AI情感强度调整（如果可用）
        if emotion_analysis and 'intensity' in emotion_analysis:
            ai_intensity = emotion_analysis['intensity']
            energy = (energy + ai_intensity) / 2

        # 3. 关键词调整
        high_energy_count = sum(1 for (type, word) in keywords if type == 'high')
        calm_count = sum(1 for (type, word) in keywords if type == 'calm')

        energy += high_energy_count * 0.5
        energy -= calm_count * 0.3

        # 限制在0-10范围
        return max(0, min(10, round(energy, 1)))

    def _map_energy_to_intensity(self, energy: float) -> str:
        """
        映射能量等级到视觉强度

        Args:
            energy: 能量等级

        Returns:
            视觉强度 (low/medium/high)
        """
        if energy >= 7.5:
            return 'high'
        elif energy >= 5.0:
            return 'medium'
        else:
            return 'low'

    def analyze_all_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量分析所有章节

        Args:
            sections: 章节列表

        Returns:
            分析结果列表
        """
        analyses = []
        for i, section in enumerate(sections, 1):
            print(f"   分析章节 {i}/{len(sections)}: {section.get('section_name', 'N/A')}")
            analysis = self.analyze_section(section)
            analyses.append(analysis)

        return analyses


# 测试代码
if __name__ == "__main__":
    # 创建测试章节
    test_sections = [
        {
            "section": "hook",
            "section_name": "开场钩子",
            "narration": "你知道吗？量子力学颠覆了我们对现实的认知！这个发现震撼了整个物理学界。"
        },
        {
            "section": "introduction",
            "section_name": "主题介绍",
            "narration": "今天我们来了解量子世界的神奇现象，探索微观世界的奥秘。"
        },
        {
            "section": "background",
            "section_name": "背景知识",
            "narration": "首先，我们需要简单了解经典物理学的基础概念和局限性。"
        }
    ]

    # 测试（不使用AI）
    analyzer = SemanticAnalyzer(use_ai=False)

    print("🧠 语义分析测试\n")
    print("=" * 60)

    for section in test_sections:
        result = analyzer.analyze_section(section)
        print(f"\n章节: {section['section_name']}")
        print(f"  类型: {result['section_type']}")
        print(f"  能量: {result['energy_level']}/10")
        print(f"  情绪: {result['emotion']}")
        print(f"  节奏: {result['pace']}")
        print(f"  强度: {result['visual_intensity']}")
        if result['content_keywords']:
            print(f"  关键词: {[kw[1] for kw in result['content_keywords']]}")

    print("\n" + "=" * 60)
