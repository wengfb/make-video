"""
智能素材推荐系统
根据脚本内容智能推荐合适的素材
"""

import json
from typing import Dict, Any, List, Optional
import sys
import os

# 导入AI客户端
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_script_generator'))
from ai_client import AIClient


class MaterialRecommender:
    """素材推荐器"""

    def __init__(self, material_manager, config_path: str = 'config/settings.json'):
        """
        初始化推荐器

        Args:
            material_manager: 素材管理器实例
            config_path: 配置文件路径
        """
        self.material_manager = material_manager

        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 加载模板
        template_path = 'config/templates.json'
        with open(template_path, 'r', encoding='utf-8') as f:
            self.templates = json.load(f)

        # 初始化AI客户端
        self.ai_client = AIClient(self.config['ai'])

    def recommend_for_script_section(
        self,
        script_section: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        为脚本章节推荐素材

        Args:
            script_section: 脚本章节数据
            limit: 推荐数量

        Returns:
            推荐素材列表
        """
        # 提取关键信息
        narration = script_section.get('narration', '')
        visual_notes = script_section.get('visual_notes', '')

        # 分析需要的素材类型
        material_requirements = self._analyze_requirements(narration, visual_notes)

        print(f"\n🔍 分析素材需求...")
        print(f"   章节: {script_section.get('section_name', 'N/A')}")

        recommendations = []

        # 基于关键词搜索现有素材
        keywords = material_requirements.get('keywords', [])
        for keyword in keywords:
            materials = self.material_manager.search_materials(keyword)
            recommendations.extend(materials)

        # 基于标签搜索
        tags = material_requirements.get('tags', [])
        if tags:
            materials = self.material_manager.list_materials(tags=tags)
            recommendations.extend(materials)

        # 去重并评分排序
        unique_materials = self._deduplicate_and_score(
            recommendations,
            material_requirements
        )

        return unique_materials[:limit]

    def recommend_for_full_script(
        self,
        script: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        为整个脚本推荐素材

        Args:
            script: 完整脚本数据

        Returns:
            按章节组织的推荐素材字典
        """
        recommendations = {}

        sections = script.get('sections', [])
        for section in sections:
            section_name = section.get('section_name', '')
            recommended = self.recommend_for_script_section(section, limit=3)
            recommendations[section_name] = recommended

        return recommendations

    def suggest_missing_materials(
        self,
        script: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        建议需要添加的素材

        Args:
            script: 脚本数据

        Returns:
            建议列表
        """
        suggestions = []

        sections = script.get('sections', [])
        for section in sections:
            section_name = section.get('section_name', '')
            visual_notes = section.get('visual_notes', '')

            # 检查是否有匹配的素材
            recommended = self.recommend_for_script_section(section, limit=1)

            if not recommended and visual_notes:
                # 没有合适素材，建议添加
                suggestions.append({
                    'section': section_name,
                    'visual_requirement': visual_notes,
                    'suggestion_type': 'missing',
                    'action': '建议使用AI生成或手动添加素材'
                })

        return suggestions

    def analyze_material_coverage(
        self,
        script: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析素材库对脚本的覆盖度

        Args:
            script: 脚本数据

        Returns:
            覆盖度分析结果
        """
        total_sections = len(script.get('sections', []))
        covered_sections = 0
        partially_covered = 0

        coverage_details = []

        for section in script.get('sections', []):
            section_name = section.get('section_name', '')
            recommended = self.recommend_for_script_section(section, limit=3)

            if len(recommended) >= 3:
                covered_sections += 1
                status = 'full'
            elif len(recommended) > 0:
                partially_covered += 1
                status = 'partial'
            else:
                status = 'none'

            coverage_details.append({
                'section': section_name,
                'status': status,
                'available_materials': len(recommended)
            })

        coverage_rate = (covered_sections / total_sections * 100) if total_sections > 0 else 0

        return {
            'total_sections': total_sections,
            'fully_covered': covered_sections,
            'partially_covered': partially_covered,
            'not_covered': total_sections - covered_sections - partially_covered,
            'coverage_rate': round(coverage_rate, 2),
            'details': coverage_details
        }

    def _analyze_requirements(
        self,
        narration: str,
        visual_notes: str
    ) -> Dict[str, Any]:
        """
        分析素材需求

        Args:
            narration: 旁白文本
            visual_notes: 视觉提示

        Returns:
            需求分析结果
        """
        # 使用AI分析（可选，也可以用简单的关键词提取）
        try:
            prompt = f"""
分析以下视频内容需要什么类型的素材：

旁白: {narration[:200]}
视觉提示: {visual_notes}

请以JSON格式输出:
{{
  "material_types": ["image", "video", "animation"],
  "keywords": ["关键词1", "关键词2"],
  "tags": ["标签1", "标签2"],
  "description": "素材需求描述"
}}
"""
            result = self.ai_client.generate_json(prompt)
            return result

        except:
            # 降级到简单关键词提取
            keywords = self._extract_keywords(narration + ' ' + visual_notes)
            return {
                'material_types': ['image'],
                'keywords': keywords,
                'tags': keywords,
                'description': visual_notes or narration[:100]
            }

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        简单的关键词提取

        Args:
            text: 文本
            max_keywords: 最大关键词数

        Returns:
            关键词列表
        """
        # 简化处理：按空格分词，过滤常用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没', '看', '好', '自己', '这'}

        words = text.split()
        keywords = []

        for word in words:
            if len(word) >= 2 and word not in stop_words and word not in keywords:
                keywords.append(word)
                if len(keywords) >= max_keywords:
                    break

        return keywords

    def _deduplicate_and_score(
        self,
        materials: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        去重并评分排序

        Args:
            materials: 素材列表
            requirements: 需求分析结果

        Returns:
            去重排序后的素材列表
        """
        # 去重
        seen_ids = set()
        unique_materials = []

        for material in materials:
            mat_id = material.get('id')
            if mat_id not in seen_ids:
                seen_ids.add(mat_id)

                # 计算匹配分数
                score = self._calculate_match_score(material, requirements)
                material['match_score'] = score

                unique_materials.append(material)

        # 按匹配分数排序
        unique_materials.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        return unique_materials

    def _calculate_match_score(
        self,
        material: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> float:
        """
        计算素材与需求的匹配分数

        Args:
            material: 素材数据
            requirements: 需求数据

        Returns:
            匹配分数 (0-100)
        """
        score = 0.0

        # 类型匹配
        required_types = requirements.get('material_types', [])
        if material.get('type') in required_types:
            score += 30

        # 标签匹配
        material_tags = set(material.get('tags', []))
        required_tags = set(requirements.get('tags', []))
        tag_overlap = len(material_tags & required_tags)
        if tag_overlap > 0:
            score += min(tag_overlap * 10, 30)

        # 关键词匹配
        material_text = (material.get('name', '') + ' ' +
                        material.get('description', '') + ' ' +
                        ' '.join(material.get('tags', []))).lower()

        keywords = requirements.get('keywords', [])
        keyword_matches = sum(1 for kw in keywords if kw.lower() in material_text)
        if keyword_matches > 0:
            score += min(keyword_matches * 10, 30)

        # 评分加成
        rating = material.get('rating')
        if rating:
            score += rating * 2

        # 使用次数（适度加成，避免总是推荐相同素材）
        used_count = material.get('used_count', 0)
        if used_count > 0:
            score += min(used_count, 10)

        return min(score, 100)
