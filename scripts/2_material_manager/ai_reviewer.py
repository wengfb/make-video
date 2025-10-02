"""
AI素材审核器（V5.5新增）
使用AI评估素材是否符合脚本需求，确保素材质量
"""

import json
from typing import Dict, Any, List, Optional
import sys
import os

# 导入AI客户端
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_script_generator'))
from ai_client import AIClient


class MaterialReviewerAI:
    """AI素材审核器"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化AI审核器

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.ai_client = AIClient(self.config['ai'])

        # 审核配置
        self.review_config = self.config.get('smart_material_selection', {})
        self.min_acceptable_score = self.review_config.get('ai_review_threshold', 70.0)
        self.enable_ai_review = self.review_config.get('enable_ai_review', True)

    def review_materials(
        self,
        materials: List[Dict[str, Any]],
        script_section: Dict[str, Any],
        min_acceptable_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        AI审核素材是否符合脚本需求

        Args:
            materials: 候选素材列表
            script_section: 脚本章节
            min_acceptable_score: 最低可接受分数（可选，默认使用配置）

        Returns:
            {
                'approved': [合格素材列表],
                'rejected': [不合格素材列表],
                'best_material': 最佳素材,
                'need_generation': bool,  # 是否需要生成新素材
                'generation_prompt': str,  # 生成素材的提示词
                'review_summary': str      # 审核总结
            }
        """
        if not self.enable_ai_review:
            # AI审核未启用，返回所有素材为合格
            return {
                'approved': materials,
                'rejected': [],
                'best_material': materials[0] if materials else None,
                'need_generation': False,
                'generation_prompt': '',
                'review_summary': 'AI审核未启用，使用所有素材'
            }

        if not materials:
            # 没有素材，需要生成
            return self._generate_empty_review(script_section)

        if min_acceptable_score is None:
            min_acceptable_score = self.min_acceptable_score

        # 执行AI审核
        print(f"\n   🤖 AI审核素材 (最低分数: {min_acceptable_score}分)...")

        try:
            review_result = self._perform_ai_review(materials, script_section)
        except Exception as e:
            print(f"   ⚠️  AI审核失败: {str(e)}，降级到基础匹配")
            return self._fallback_review(materials)

        # 处理审核结果
        approved = []
        rejected = []
        best_material = None
        best_score = 0

        for review in review_result.get('reviews', []):
            idx = review.get('material_index', -1)
            if idx < 0 or idx >= len(materials):
                continue

            material = materials[idx].copy()
            score = review.get('score', 0)
            is_acceptable = review.get('is_acceptable', False)
            reason = review.get('reason', '未提供原因')

            # 添加AI审核信息
            material['ai_review_score'] = score
            material['ai_review_reason'] = reason
            material['ai_review_issues'] = review.get('issues', [])

            if is_acceptable and score >= min_acceptable_score:
                approved.append(material)
                if score > best_score:
                    best_score = score
                    best_material = material
            else:
                rejected.append(material)

        # 判断是否需要生成新素材
        need_generation = review_result.get('need_custom_generation', False)
        generation_prompt = review_result.get('generation_requirements', '')

        # 打印审核结果
        print(f"   📊 审核结果: {len(approved)}个合格, {len(rejected)}个不合格")
        if best_material:
            print(f"   ⭐ 最佳素材: {best_material.get('name', 'N/A')} (评分: {best_score}分)")
            print(f"   ✨ 理由: {best_material.get('ai_review_reason', 'N/A')}")

        if need_generation:
            print(f"   ⚠️  现有素材不符合要求，建议AI生成")

        return {
            'approved': approved,
            'rejected': rejected,
            'best_material': best_material,
            'need_generation': need_generation,
            'generation_prompt': generation_prompt,
            'review_summary': review_result.get('summary', '')
        }

    def _perform_ai_review(
        self,
        materials: List[Dict[str, Any]],
        script_section: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行AI审核

        Args:
            materials: 候选素材列表
            script_section: 脚本章节

        Returns:
            AI审核结果
        """
        narration = script_section.get('narration', '')
        visual_notes = script_section.get('visual_notes', '')
        section_name = script_section.get('section_name', '未命名章节')

        # 格式化素材信息
        materials_info = self._format_materials_for_review(materials[:5])  # 只审核前5个

        # AI审核prompt
        review_prompt = f"""
作为视频素材审核专家，评估以下素材是否适合这个科普视频场景。

## 场景信息
章节: {section_name}
旁白: {narration[:200]}
视觉要求: {visual_notes}

## 待审核素材
{materials_info}

## 评分标准
1. **内容相关性** (40分): 素材内容是否展示旁白描述的主题
   - 完全匹配: 35-40分
   - 部分匹配: 20-34分
   - 不匹配: 0-19分

2. **视觉质量** (30分): 清晰度、美观度、专业性
   - 高清、专业: 25-30分
   - 中等: 15-24分
   - 低质量: 0-14分

3. **场景匹配** (20分): 是否符合科普视频风格
   - 完全符合: 16-20分
   - 基本符合: 10-15分
   - 不符合: 0-9分

4. **实用性** (10分): 时长、格式等是否适合使用
   - 完全适合: 8-10分
   - 基本适合: 5-7分
   - 不适合: 0-4分

## 输出格式
请以JSON格式输出（严格遵守格式）:
{{
  "reviews": [
    {{
      "material_index": 0,
      "score": 85,
      "is_acceptable": true,
      "reason": "素材展示黑洞吸积盘效果，符合旁白描述的时空扭曲主题",
      "issues": []
    }},
    {{
      "material_index": 1,
      "score": 55,
      "is_acceptable": false,
      "reason": "仅展示普通星空，缺少黑洞特征",
      "issues": ["内容相关性不足", "缺少核心元素"]
    }}
  ],
  "best_material_index": 0,
  "need_custom_generation": false,
  "generation_requirements": "",
  "summary": "找到1个高质量素材，建议使用第1个"
}}

## 重要规则
- 如果**所有**素材得分 < 60分，设置 need_custom_generation=true
- generation_requirements 应描述需要生成什么样的素材
- is_acceptable=true 的条件：score >= 70 且无严重问题
- 优先选择视频素材（如果有）

请开始审核:
"""

        # 调用AI
        result = self.ai_client.generate_json(review_prompt)
        return result

    def _format_materials_for_review(self, materials: List[Dict[str, Any]]) -> str:
        """
        格式化素材信息供AI审核

        Args:
            materials: 素材列表

        Returns:
            格式化的素材信息字符串
        """
        formatted = []

        for i, m in enumerate(materials):
            material_type = m.get('type', 'unknown')
            name = m.get('name', 'N/A')
            tags = m.get('tags', [])
            description = m.get('description', 'N/A')
            source = m.get('source', 'local')
            match_score = m.get('match_score', 0)

            formatted.append(f"""
素材 {i+1}:
- 名称: {name}
- 类型: {material_type}
- 来源: {source}
- 标签: {', '.join(tags[:8])}
- 描述: {description}
- 初步匹配度: {match_score:.0f}%
""")

        return '\n'.join(formatted)

    def _generate_empty_review(self, script_section: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成空审核结果（当没有素材时）

        Args:
            script_section: 脚本章节

        Returns:
            审核结果
        """
        visual_notes = script_section.get('visual_notes', '')
        narration = script_section.get('narration', '')[:100]

        generation_prompt = f"""
请生成符合以下需求的科普视频素材:

场景描述: {visual_notes}
旁白内容: {narration}

风格要求:
- 科普教育风格
- 清晰、简洁、专业
- 适合视频使用
"""

        return {
            'approved': [],
            'rejected': [],
            'best_material': None,
            'need_generation': True,
            'generation_prompt': generation_prompt,
            'review_summary': '未找到合适素材，需要AI生成'
        }

    def _fallback_review(self, materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        降级审核（当AI审核失败时）

        简单地使用初步匹配分数

        Args:
            materials: 素材列表

        Returns:
            审核结果
        """
        # 按匹配分数排序
        sorted_materials = sorted(
            materials,
            key=lambda x: x.get('match_score', 0),
            reverse=True
        )

        # 分数>60的为合格
        approved = [m for m in sorted_materials if m.get('match_score', 0) > 60]
        rejected = [m for m in sorted_materials if m.get('match_score', 0) <= 60]

        return {
            'approved': approved,
            'rejected': rejected,
            'best_material': sorted_materials[0] if sorted_materials else None,
            'need_generation': len(approved) == 0,
            'generation_prompt': '',
            'review_summary': '降级审核：使用初步匹配分数'
        }


# 测试代码
if __name__ == "__main__":
    # 测试AI审核器
    reviewer = MaterialReviewerAI()

    # 模拟素材和脚本
    test_materials = [
        {
            'name': 'pexels_video_4990248',
            'type': 'video',
            'tags': ['black', 'hole', 'space', 'astronomy'],
            'description': 'Black hole animation in space',
            'source': 'pexels',
            'match_score': 85
        },
        {
            'name': 'pexels_photo_9668535',
            'type': 'image',
            'tags': ['space', 'stars', 'galaxy'],
            'description': 'Space stars background',
            'source': 'pexels',
            'match_score': 65
        }
    ]

    test_section = {
        'section_name': '开场钩子',
        'narration': '想象一下，如果你站在一个黑洞附近，时间会变慢...',
        'visual_notes': '展示一个壮观的黑洞动画，光线被吸入'
    }

    result = reviewer.review_materials(test_materials, test_section)

    print("\n=== 测试结果 ===")
    print(f"合格素材: {len(result['approved'])}")
    print(f"需要生成: {result['need_generation']}")
    if result['best_material']:
        print(f"最佳素材: {result['best_material']['name']}")
        print(f"AI评分: {result['best_material'].get('ai_review_score', 'N/A')}")
