"""
AI语义素材匹配器
使用AI理解场景语义，智能匹配最佳素材
V5.6新增
"""

import json
import sys
import os
from typing import Dict, Any, List, Optional

# 导入AI客户端
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_script_generator'))
from ai_client import AIClient


class AISemanticMatcher:
    """AI语义匹配器 - 理解场景内容，不只看关键词"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化AI语义匹配器

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化AI客户端
        self.ai_client = AIClient(self.config['ai'])

    def match_scene_to_materials(
        self,
        visual_options: List[Dict[str, Any]],
        candidate_materials: List[Dict[str, Any]],
        section_name: str = ""
    ) -> Dict[str, Any]:
        """
        使用AI语义理解匹配场景和素材

        Args:
            visual_options: 3个优先级的视觉方案
            candidate_materials: 候选素材列表
            section_name: 章节名称（用于日志）

        Returns:
            匹配结果字典
        """
        if not visual_options or not candidate_materials:
            return self._create_empty_result()

        # 构建AI分析prompt
        prompt = self._build_matching_prompt(visual_options, candidate_materials)

        try:
            # 调用AI分析
            result = self.ai_client.generate_json(prompt)

            # 验证和规范化结果
            return self._normalize_result(result, visual_options, candidate_materials)

        except Exception as e:
            print(f"   ⚠️  AI语义匹配失败: {str(e)}")
            # 降级到简单评分
            return self._fallback_matching(visual_options, candidate_materials)

    def _build_matching_prompt(
        self,
        visual_options: List[Dict[str, Any]],
        materials: List[Dict[str, Any]]
    ) -> str:
        """
        构建AI分析prompt

        Args:
            visual_options: 视觉方案列表
            materials: 候选素材列表

        Returns:
            AI prompt文本
        """
        # 格式化视觉方案
        options_text = ""
        for opt in visual_options:
            priority = opt.get('priority', 0)
            desc = opt.get('description', '')
            keywords = ', '.join(opt.get('keywords', []))
            options_text += f"\nPriority {priority}: {desc}\n   关键词: {keywords}\n"

        # 格式化候选素材（最多10个，避免token过多）
        materials_text = ""
        for i, mat in enumerate(materials[:10], 1):
            mat_id = mat.get('id', mat.get('name', f'material_{i}'))
            mat_name = mat.get('name', mat_id)
            mat_type = mat.get('type', 'unknown')
            mat_desc = mat.get('description', '')
            mat_tags = ', '.join(mat.get('tags', [])[:5])

            # 如果有语义元数据，优先使用
            semantic = mat.get('semantic_metadata', {})
            if semantic:
                scene_desc = semantic.get('scene_description', mat_desc)
                main_objects = ', '.join(semantic.get('main_objects', []))
                materials_text += f"\n{i}. {mat_name} ({mat_type})\n"
                materials_text += f"   场景: {scene_desc}\n"
                materials_text += f"   主要对象: {main_objects}\n"
            else:
                materials_text += f"\n{i}. {mat_name} ({mat_type})\n"
                materials_text += f"   描述: {mat_desc}\n"
                materials_text += f"   标签: {mat_tags}\n"

        # 构建完整prompt
        prompt = f"""你是视频素材语义匹配专家。分析以下场景需求和候选素材，找出最佳匹配。

## 场景需求（按优先级）
{options_text}

## 候选素材
{materials_text}

## 分析任务
1. 理解每个Priority方案的场景内容（不只看关键词，理解场景语义）
2. 评估每个素材与各个Priority方案的语义匹配度
3. 选择最佳匹配：优先匹配Priority 1，如果没有高匹配素材则考虑Priority 2/3
4. 匹配度评分标准：
   - 90-100分：完美匹配，场景主体、动作、视角都一致
   - 70-89分：高度匹配，主要元素一致，部分细节不同
   - 50-69分：中等匹配，有共同元素但场景差异较大
   - 30-49分：低匹配，仅关键词重叠，场景不一致
   - 0-29分：几乎不匹配

## 输出格式（纯JSON，无其他文字）
{{
  "best_match": {{
    "material_index": 1,
    "material_name": "素材名称",
    "matched_priority": 2,
    "semantic_score": 85,
    "reasoning": "详细说明为什么选择这个素材，匹配了哪些元素，缺失了什么"
  }},
  "matched_elements": ["匹配的元素1", "匹配的元素2"],
  "missing_elements": ["缺失的元素1"],
  "alternative_matches": [
    {{
      "material_index": 2,
      "material_name": "备选素材名称",
      "matched_priority": 3,
      "semantic_score": 65,
      "reasoning": "备选原因"
    }}
  ],
  "recommendation": "使用建议（如：推荐使用/建议AI生成/需要手动上传）"
}}

请只返回JSON，确保格式正确。"""

        return prompt

    def _normalize_result(
        self,
        ai_result: Dict[str, Any],
        visual_options: List[Dict[str, Any]],
        materials: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        规范化AI返回结果

        Args:
            ai_result: AI返回的原始结果
            visual_options: 视觉方案
            materials: 素材列表

        Returns:
            规范化的结果
        """
        best_match = ai_result.get('best_match', {})
        material_index = best_match.get('material_index', 1) - 1  # 转为0索引

        # 确保索引有效
        if 0 <= material_index < len(materials):
            selected_material = materials[material_index]
        else:
            # 索引无效，使用第一个素材
            selected_material = materials[0] if materials else None
            material_index = 0

        # 构建标准化结果
        result = {
            'best_material': selected_material,
            'selected_priority': best_match.get('matched_priority', 3),
            'semantic_score': best_match.get('semantic_score', 50),
            'matched_elements': ai_result.get('matched_elements', []),
            'missing_elements': ai_result.get('missing_elements', []),
            'reasoning': best_match.get('reasoning', ''),
            'recommendation': ai_result.get('recommendation', ''),
            'alternative_matches': []
        }

        # 处理备选素材
        alternatives = ai_result.get('alternative_matches', [])
        for alt in alternatives[:2]:  # 最多保留2个备选
            alt_index = alt.get('material_index', 0) - 1
            if 0 <= alt_index < len(materials):
                result['alternative_matches'].append({
                    'material': materials[alt_index],
                    'priority': alt.get('matched_priority', 3),
                    'score': alt.get('semantic_score', 40),
                    'reasoning': alt.get('reasoning', '')
                })

        return result

    def _fallback_matching(
        self,
        visual_options: List[Dict[str, Any]],
        materials: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        降级匹配逻辑（AI失败时使用简单评分）

        Args:
            visual_options: 视觉方案
            materials: 素材列表

        Returns:
            匹配结果
        """
        print("   ⚠️  使用降级匹配算法（关键词匹配）")

        # 提取所有关键词（优先级加权）
        all_keywords = []
        for opt in visual_options:
            priority = opt.get('priority', 3)
            keywords = opt.get('keywords', [])
            weight = 4 - priority  # Priority 1权重3，Priority 2权重2，Priority 3权重1
            all_keywords.extend([(kw.lower(), weight) for kw in keywords])

        # 计算每个素材的评分
        scored_materials = []
        for mat in materials:
            score = 0
            mat_text = (
                mat.get('name', '') + ' ' +
                mat.get('description', '') + ' ' +
                ' '.join(mat.get('tags', []))
            ).lower()

            # 关键词匹配
            for keyword, weight in all_keywords:
                if keyword in mat_text:
                    score += 10 * weight

            # 类型加分
            if mat.get('type') == 'video':
                score += 15

            scored_materials.append((mat, score))

        # 排序
        scored_materials.sort(key=lambda x: x[1], reverse=True)

        if scored_materials:
            best_material, best_score = scored_materials[0]
            return {
                'best_material': best_material,
                'selected_priority': 3,  # 降级匹配默认Priority 3
                'semantic_score': min(best_score, 70),  # 降级最高70分
                'matched_elements': [],
                'missing_elements': [],
                'reasoning': '使用关键词匹配（AI分析失败）',
                'recommendation': '建议手动确认素材是否合适',
                'alternative_matches': []
            }
        else:
            return self._create_empty_result()

    def _create_empty_result(self) -> Dict[str, Any]:
        """创建空结果"""
        return {
            'best_material': None,
            'selected_priority': 3,
            'semantic_score': 0,
            'matched_elements': [],
            'missing_elements': [],
            'reasoning': '无合适素材',
            'recommendation': '建议AI生成或手动上传素材',
            'alternative_matches': []
        }

    def quick_score_material(
        self,
        material: Dict[str, Any],
        scene_description: str
    ) -> int:
        """
        快速评估单个素材与场景的匹配度（不使用AI，用于大批量筛选）

        Args:
            material: 素材数据
            scene_description: 场景描述

        Returns:
            匹配分数（0-100）
        """
        score = 0

        # 提取关键词
        scene_keywords = scene_description.lower().split()

        # 素材文本
        mat_text = (
            material.get('name', '') + ' ' +
            material.get('description', '') + ' ' +
            ' '.join(material.get('tags', []))
        ).lower()

        # 关键词匹配
        matched_count = sum(1 for kw in scene_keywords if kw in mat_text)
        score += min(matched_count * 8, 40)

        # 类型匹配
        if material.get('type') == 'video':
            score += 20
        elif material.get('type') == 'image':
            score += 10

        # 质量加分
        if material.get('source') in ['pexels', 'unsplash']:
            score += 10

        return min(score, 100)
