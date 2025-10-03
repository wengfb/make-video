"""
智能素材推荐系统
根据脚本内容智能推荐合适的素材
V5.1 新增: 四级智能获取策略 (本地 → Pexels → Unsplash → DALL-E)
"""

import json
from typing import Dict, Any, List, Optional
import sys
import os

# 导入AI客户端
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_script_generator'))
from ai_client import AIClient

# 导入外部素材获取器
try:
    from pexels_fetcher import PexelsFetcher
    PEXELS_AVAILABLE = True
except ImportError:
    PEXELS_AVAILABLE = False
    print("⚠️  Pexels模块未加载")

try:
    from unsplash_fetcher import UnsplashFetcher
    UNSPLASH_AVAILABLE = True
except ImportError:
    UNSPLASH_AVAILABLE = False
    print("⚠️  Unsplash模块未加载")


class MaterialRecommender:
    """素材推荐器 (智能四级获取)"""

    def __init__(self, material_manager, config_path: str = 'config/settings.json'):
        """
        初始化推荐器

        Args:
            material_manager: 素材管理器实例
            config_path: 配置文件路径
        """
        self.material_manager = material_manager
        self.config_path = config_path

        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 加载模板
        template_path = 'config/templates.json'
        with open(template_path, 'r', encoding='utf-8') as f:
            self.templates = json.load(f)

        # 初始化AI客户端
        self.ai_client = AIClient(self.config['ai'])

        # 初始化外部素材获取器
        self.pexels_fetcher = PexelsFetcher(config_path) if PEXELS_AVAILABLE else None
        self.unsplash_fetcher = UnsplashFetcher(config_path) if UNSPLASH_AVAILABLE else None

        # V5.5: 初始化AI审核器和生成器（延迟加载）
        self._ai_reviewer = None
        self._ai_generator = None

        # V5.6: 初始化AI语义匹配器（延迟加载）
        self._ai_semantic_matcher = None

        # 智能获取配置
        self.smart_fetch_config = self.config.get('smart_material_fetch', {
            'enable': True,
            'auto_download': True,
            'prefer_videos': True,
            'min_local_results': 3
        })

    @property
    def ai_reviewer(self):
        """延迟加载AI审核器"""
        if self._ai_reviewer is None:
            try:
                from ai_reviewer import MaterialReviewerAI
                self._ai_reviewer = MaterialReviewerAI(self.config_path)
            except Exception as e:
                print(f"   ⚠️  AI审核器加载失败: {str(e)}")
                self._ai_reviewer = None
        return self._ai_reviewer

    @property
    def ai_generator(self):
        """延迟加载AI生成器"""
        if self._ai_generator is None:
            try:
                from ai_content_generator import AIContentGenerator
                self._ai_generator = AIContentGenerator(self.config_path)
            except Exception as e:
                print(f"   ⚠️  AI生成器加载失败: {str(e)}")
                self._ai_generator = None
        return self._ai_generator

    @property
    def ai_semantic_matcher(self):
        """延迟加载AI语义匹配器（V5.6）"""
        if self._ai_semantic_matcher is None:
            try:
                from ai_semantic_matcher import AISemanticMatcher
                self._ai_semantic_matcher = AISemanticMatcher(self.config_path)
            except Exception as e:
                print(f"   ⚠️  AI语义匹配器加载失败: {str(e)}")
                self._ai_semantic_matcher = None
        return self._ai_semantic_matcher

    def recommend_for_script_section(
        self,
        script_section: Dict[str, Any],
        limit: int = 5,
        enable_smart_fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """
        为脚本章节推荐素材 (智能四级获取)
        V5.6: 支持visual_options多层次场景匹配

        Args:
            script_section: 脚本章节数据
            limit: 推荐数量
            enable_smart_fetch: 是否启用智能获取 (从外部API)

        Returns:
            推荐素材列表
        """
        section_name = script_section.get('section_name', 'N/A')
        print(f"\n🔍 分析素材需求...")
        print(f"   章节: {section_name}")

        # V5.6: 检查是否有visual_options（新格式）
        visual_options = script_section.get('visual_options', [])
        if visual_options:
            # 使用新的多层次场景匹配
            return self._recommend_with_visual_options(
                script_section,
                visual_options,
                limit,
                enable_smart_fetch
            )

        # 降级到旧版匹配逻辑（兼容旧脚本）
        # 提取关键信息
        narration = script_section.get('narration', '')
        visual_notes = script_section.get('visual_notes', '')

        # 分析需要的素材类型
        material_requirements = self._analyze_requirements(narration, visual_notes)

        recommendations = []

        # 🔹 第一级: 本地素材库搜索
        print("   📁 [1/4] 搜索本地素材库...")
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

        print(f"       ✓ 找到 {len(unique_materials)} 个本地素材")

        # 🔹 智能获取策略 (如果本地素材不足)
        min_required = self.smart_fetch_config.get('min_local_results', 3)

        if enable_smart_fetch and self.smart_fetch_config.get('enable', True) and len(unique_materials) < min_required:
            print(f"       ⚠️  本地素材不足 (需要{min_required}个,仅{len(unique_materials)}个)")

            # 提取英文关键词(Pexels/Unsplash需要英文)
            search_keyword = self._extract_english_keyword(narration, visual_notes)

            # 🔹 第二级: Pexels视频搜索 (优先视频)
            if self.smart_fetch_config.get('prefer_videos', True) and self.pexels_fetcher:
                pexels_materials = self._fetch_from_pexels_videos(
                    search_keyword,
                    count=limit - len(unique_materials)
                )
                unique_materials.extend(pexels_materials)
                print(f"       ✓ 从Pexels视频获取 {len(pexels_materials)} 个")

            # 🔹 第三级: Pexels/Unsplash图片 (如果仍不足)
            if len(unique_materials) < limit:
                if self.pexels_fetcher:
                    pexels_photos = self._fetch_from_pexels_photos(
                        search_keyword,
                        count=max(2, limit - len(unique_materials))
                    )
                    unique_materials.extend(pexels_photos)
                    print(f"       ✓ 从Pexels图片获取 {len(pexels_photos)} 个")

                if self.unsplash_fetcher and len(unique_materials) < limit:
                    unsplash_photos = self._fetch_from_unsplash(
                        search_keyword,
                        count=limit - len(unique_materials)
                    )
                    unique_materials.extend(unsplash_photos)
                    print(f"       ✓ 从Unsplash获取 {len(unsplash_photos)} 个")

            # 🔹 第四级: DALL-E生成 (最后手段,付费)
            # 暂时注释,避免自动产生费用
            # if len(unique_materials) < limit:
            #     print("       💰 可选: 使用DALL-E生成 (需手动触发)")

        # V5.4修复: 确保所有素材都有match_score和match_reason
        # 外部素材（Pexels/Unsplash）需要重新评分
        for material in unique_materials:
            if 'match_score' not in material or 'match_reason' not in material:
                material['match_score'] = self._calculate_match_score(material, material_requirements)
                material['match_reason'] = self._generate_match_reason(material, material_requirements)

        # 重新排序（外部素材可能评分更高）
        unique_materials.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        # V5.5: AI审核和生成
        final_materials = self._apply_ai_review_and_generation(
            unique_materials[:limit],
            script_section,
            material_requirements
        )

        return final_materials[:limit]

    def _apply_ai_review_and_generation(
        self,
        materials: List[Dict[str, Any]],
        script_section: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        应用AI审核和生成（V5.5新增）

        工作流程:
        1. AI审核现有素材
        2. 如果没有合格素材，AI生成新素材
        3. 返回最终素材列表

        Args:
            materials: 候选素材列表
            script_section: 脚本章节
            requirements: 需求分析结果

        Returns:
            最终素材列表
        """
        # 检查是否启用AI审核
        if not self.config.get('smart_material_selection', {}).get('enable_ai_review', False):
            return materials

        # 执行AI审核
        if self.ai_reviewer:
            try:
                review_result = self.ai_reviewer.review_materials(materials, script_section)

                # 有合格素材，返回合格列表
                if review_result['approved']:
                    approved = review_result['approved']
                    # 将最佳素材放在首位
                    if review_result['best_material']:
                        best = review_result['best_material']
                        approved = [best] + [m for m in approved if m['id'] != best['id']]
                    return approved

                # 无合格素材，尝试AI生成
                if review_result.get('need_generation', False) and self.ai_generator:
                    generation_prompt = review_result.get('generation_prompt', '')
                    if not generation_prompt:
                        print(f"   ⚠️  无生成提示词，跳过AI生成")
                    else:
                        print(f"\n   🎨 现有素材不符合要求，尝试AI生成...")
                        generated = self.ai_generator.generate_material(
                            script_section,
                            generation_prompt
                        )

                        if generated:
                            # 将生成的素材添加到素材库
                            try:
                                self.material_manager.add_material(
                                    name=generated['name'],
                                    file_path=generated['file_path'],
                                    material_type=generated['type'],
                                    tags=generated['tags'],
                                    description=generated['description']
                                )
                                print(f"   ✅ AI生成的素材已添加到素材库")
                            except Exception as e:
                                print(f"   ⚠️  添加到素材库失败: {str(e)}")

                            # 返回生成的素材
                            return [generated]

            except Exception as e:
                print(f"   ⚠️  AI审核/生成失败: {str(e)}")

        # 降级：返回原始素材
        return materials

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
        分析素材需求（V5.4增强：多维度分析）

        Args:
            narration: 旁白文本
            visual_notes: 视觉提示

        Returns:
            需求分析结果
        """
        # 使用AI分析（可选，也可以用简单的关键词提取）
        try:
            prompt = f"""
分析以下科普视频场景需要什么素材，并提取多维度关键词。

旁白: {narration[:200]}
视觉提示: {visual_notes}

请以JSON格式输出（优先推荐视频素材）:
{{
  "material_types": ["video", "image", "animation"],  // 按优先级排序，优先推荐video
  "keywords": ["主体对象", "场景类型", "动作/状态"],  // 3-5个关键词
  "tags": ["科学领域", "视觉风格"],  // 2-3个标签
  "visual_elements": ["具体视觉元素1", "元素2"],  // 需要展示的具体元素
  "scene_type": "微观/宏观/抽象/实景",  // 场景类型
  "mood": "科技感/神秘/温暖/紧张",  // 情感氛围
  "description": "一句话总结素材需求"
}}

示例:
输入: 旁白="DNA双螺旋结构存储着生命的秘密", 视觉="显示DNA分子结构旋转动画"
输出:
{{
  "material_types": ["video", "animation"],
  "keywords": ["DNA", "双螺旋", "分子结构", "旋转"],
  "tags": ["生物学", "微观", "科技"],
  "visual_elements": ["DNA模型", "螺旋动画", "分子"],
  "scene_type": "微观",
  "mood": "科技感",
  "description": "DNA双螺旋结构的微观动画"
}}
"""
            result = self.ai_client.generate_json(prompt)
            return result

        except:
            # 降级到简单关键词提取
            keywords = self._extract_keywords(narration + ' ' + visual_notes)
            return {
                'material_types': ['video', 'image'],  # V5.4: 优先视频
                'keywords': keywords,
                'tags': keywords,
                'visual_elements': keywords[:2],
                'scene_type': 'unknown',
                'mood': 'neutral',
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
        去重并评分排序（V5.4增强：添加匹配原因）

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

                # V5.4: 生成匹配原因
                material['match_reason'] = self._generate_match_reason(material, requirements)

                unique_materials.append(material)

        # 按匹配分数排序
        unique_materials.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        return unique_materials

    def _generate_match_reason(
        self,
        material: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> str:
        """
        生成素材匹配原因说明（V5.4新增）

        Args:
            material: 素材数据
            requirements: 需求数据

        Returns:
            匹配原因文本
        """
        reasons = []

        # 类型匹配
        material_type = material.get('type', '')
        if material_type == 'video':
            reasons.append("视频素材")
        elif material_type == 'image':
            reasons.append("图片素材")

        # 标签匹配
        material_tags = set(material.get('tags', []))
        required_tags = set(requirements.get('tags', []))
        common_tags = material_tags & required_tags
        if common_tags:
            reasons.append(f"标签匹配: {', '.join(list(common_tags)[:2])}")

        # 关键词匹配
        material_text = (
            material.get('name', '') + ' ' +
            material.get('description', '') + ' ' +
            ' '.join(material.get('tags', []))
        ).lower()

        keywords = requirements.get('keywords', [])
        matched_keywords = [kw for kw in keywords if kw.lower() in material_text]
        if matched_keywords:
            reasons.append(f"关键词: {', '.join(matched_keywords[:2])}")

        # 来源说明
        source = material.get('source', '')
        if source == 'pexels':
            reasons.append("Pexels高质量")
        elif source == 'unsplash':
            reasons.append("Unsplash高质量")

        # 使用历史
        used_count = material.get('used_count', 0)
        if used_count == 0:
            reasons.append("新素材")
        elif used_count > 5:
            reasons.append(f"已用{used_count}次")

        return " | ".join(reasons) if reasons else "基础匹配"

    def _calculate_match_score(
        self,
        material: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> float:
        """
        计算素材与需求的匹配分数
        V5.4: 增强评分算法 - 支持多维度分析

        Args:
            material: 素材数据
            requirements: 需求数据

        Returns:
            匹配分数 (0-100)
        """
        score = 0.0

        # ✨ V5.4: 类型匹配（视频素材优先，权重40分）
        material_type = material.get('type')
        required_types = requirements.get('material_types', [])

        if material_type == 'video':
            # 视频在第一优先级：40分
            if required_types and required_types[0] == 'video':
                score += 40
            else:
                score += 30  # 即使不是首选，视频也有高分
        elif material_type in required_types:
            # 其他匹配类型：20-30分
            type_index = required_types.index(material_type)
            score += max(20, 30 - type_index * 5)

        # ✨ V5.4: 标签匹配（权重35分）
        material_tags = set(material.get('tags', []))
        required_tags = set(requirements.get('tags', []))
        tag_overlap = len(material_tags & required_tags)
        if tag_overlap > 0:
            score += min(tag_overlap * 12, 35)

        # ✨ V5.4: 关键词匹配（权重25分）
        material_text = (
            material.get('name', '') + ' ' +
            material.get('description', '') + ' ' +
            ' '.join(material.get('tags', []))
        ).lower()

        # 关键词匹配
        keywords = requirements.get('keywords', [])
        keyword_score = 0
        for keyword in keywords:
            keyword_parts = keyword.lower().split()
            matches = sum(1 for part in keyword_parts if part in material_text)
            if matches > 0:
                keyword_score += min(matches * 8, 15)
        score += min(keyword_score, 25)

        # ✨ V5.4: 视觉元素匹配（新增，权重20分）
        visual_elements = requirements.get('visual_elements', [])
        if visual_elements:
            element_score = 0
            for element in visual_elements:
                if element.lower() in material_text:
                    element_score += 10
            score += min(element_score, 20)

        # ✨ V5.4: 场景类型匹配（新增，权重10分）
        scene_type = requirements.get('scene_type', '').lower()
        if scene_type and scene_type != 'unknown':
            if scene_type in material_text:
                score += 10

        # 评分加成（权重10分）
        rating = material.get('rating')
        if rating:
            score += rating * 2

        # ✨ V5.4: 使用历史（权重-15到+5分）
        used_count = material.get('used_count', 0)
        if used_count == 0:
            score += 5  # 新素材加分
        elif used_count <= 2:
            score += 2  # 少用素材小加分
        elif used_count > 5:
            score -= min((used_count - 5) * 3, 15)  # 用太多次减分

        # ✨ V5.4: 来源加成（Pexels/Unsplash高质量素材）
        source = material.get('source', '')
        if source == 'pexels' and material_type == 'video':
            score += 5  # Pexels视频质量高
        elif source == 'unsplash':
            score += 3  # Unsplash图片质量高

        return max(0, min(score, 100))

    # ===== V5.1 新增: 外部素材获取方法 =====

    def _extract_english_keyword(self, narration: str, visual_notes: str) -> str:
        """
        提取英文关键词(用于Pexels/Unsplash搜索)
        V5.3: 添加AI智能提取 + 多关键词匹配 + 详细日志

        Args:
            narration: 旁白文本
            visual_notes: 视觉提示

        Returns:
            英文关键词
        """
        # 优先使用visual_notes
        text = visual_notes if visual_notes else narration

        print(f"\n   🔍 关键词提取分析:")
        print(f"      输入源: {'visual_notes' if visual_notes else 'narration'}")
        print(f"      文本: {text[:120]}{'...' if len(text) > 120 else ''}")

        # ✨ V5.3 新增: AI智能提取 (优先级最高)
        ai_keyword = self._ai_extract_keyword(text, narration)
        if ai_keyword:
            print(f"      ✓ AI提取: '{ai_keyword}'")
            return ai_keyword

        # 简单映射(中文 → 英文科普关键词)
        # ✨ V5.2 扩展: 添加更多气候和科学相关关键词
        keyword_map = {
            # 宇宙和天文
            '宇宙': 'space universe',
            '星空': 'stars galaxy',
            '太空': 'space',
            '黑洞': 'black hole',
            '星系': 'galaxy',
            '行星': 'planet',
            '恒星': 'star',

            # 生物和医学
            'DNA': 'DNA genetics',
            '基因': 'DNA genetics',
            '细胞': 'cell biology',
            '大脑': 'brain neuroscience',
            '神经': 'neuron brain',
            '医学': 'medicine medical',
            '健康': 'health medical',
            '心脏': 'heart cardiology',
            '肺': 'lungs respiratory',
            '血液': 'blood circulation',

            # 物理和化学
            '量子': 'quantum physics',
            '物理': 'physics',
            '化学': 'chemistry science',
            '分子': 'molecule chemistry',
            '原子': 'atom physics',
            '电子': 'electron technology',
            '光': 'light optics',
            '声音': 'sound wave',
            '电': 'electricity energy',
            '相对论': 'relativity physics',
            '时空': 'spacetime physics',

            # 科技和AI
            '科技': 'technology innovation',
            '人工智能': 'artificial intelligence AI',
            'AI': 'artificial intelligence',
            '机器人': 'robot technology',
            '计算机': 'computer technology',
            '量子计算': 'quantum computing',

            # 环境和气候 (重点扩展)
            '气候': 'climate weather',
            '气候变化': 'climate change global warming',
            '全球变暖': 'global warming',
            '温室效应': 'greenhouse effect',
            '温室气体': 'greenhouse gas emissions',
            '碳排放': 'carbon emissions',
            '二氧化碳': 'carbon dioxide CO2',
            '环境': 'environment nature',
            '生态': 'ecology ecosystem',
            '污染': 'pollution',
            '可再生能源': 'renewable energy',
            '太阳能': 'solar energy',
            '风能': 'wind energy',
            '冰川': 'glacier ice',
            '海平面': 'sea level',
            '极端天气': 'extreme weather',

            # 地球科学
            '地球': 'earth planet',
            '海洋': 'ocean sea',
            '火山': 'volcano',
            '地震': 'earthquake',
            '地质': 'geology',
            '矿物': 'mineral',

            # 能源
            '能源': 'energy renewable',
            '核能': 'nuclear energy',
            '电池': 'battery energy storage',

            # ✨ V5.3 新增: 视觉元素和动作
            '温度计': 'thermometer temperature',
            '温度': 'temperature',
            '温度上升': 'rising temperature',
            '上升': 'rising increase',
            '下降': 'falling decrease',
            '发烧': 'fever heat warming',
            '汽车': 'car vehicle',
            '阳光': 'sunlight solar',
            '玻璃': 'glass transparent',
            '大气层': 'atmosphere',
            '大气': 'atmosphere air',
            '辐射': 'radiation',
            '融化': 'melting ice',
            '蒸发': 'evaporation',
            '循环': 'cycle circulation',
            '动画': 'animation motion',
            '图表': 'chart graph data',
            '曲线': 'curve line graph',
            '数据': 'data statistics',
            '对比': 'comparison before after',
            '变化': 'change transformation',
            '过程': 'process',
            '实验': 'experiment science',
            '显微镜': 'microscope',
            '望远镜': 'telescope'
        }

        # ✨ V5.3 改进: 多关键词匹配 (收集所有匹配)
        matched_keywords = []
        for cn_keyword, en_keyword in keyword_map.items():
            if cn_keyword in text:
                # 记录: (中文词, 英文词, 词长度, 在文本中的位置)
                position = text.index(cn_keyword)
                matched_keywords.append({
                    'cn': cn_keyword,
                    'en': en_keyword,
                    'len': len(cn_keyword),
                    'pos': position
                })

        if matched_keywords:
            # 按关键词长度排序 (优先匹配更具体的长词)
            matched_keywords.sort(key=lambda x: x['len'], reverse=True)

            # 日志显示所有匹配
            print(f"      匹配词: {', '.join([f'{m['cn']}→{m['en']}' for m in matched_keywords[:5]])}")

            # 组合前2个最相关的关键词
            top_matches = matched_keywords[:2]
            combined_keyword = ' '.join([m['en'] for m in top_matches])

            print(f"      ✓ 映射表提取: '{combined_keyword}'")
            return combined_keyword

        # 默认: 通用科普关键词
        print(f"      ⚠️  无匹配，使用默认: 'science education'")
        return 'science education'

    def _check_material_exists(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        检查素材是否已存在数据库（V5.4新增）

        Args:
            material_id: 素材ID（如 pexels_video_29541711）

        Returns:
            素材信息（如果存在），否则返回None
        """
        # 精确ID匹配（通过name字段）
        materials = self.material_manager.search_materials(material_id, search_in=['name'])

        for material in materials:
            # 精确匹配name
            if material.get('name') == material_id:
                # 验证文件是否存在
                file_path = material.get('file_path')
                if file_path and os.path.exists(file_path):
                    return material

        return None

    def _generate_smart_tags(self, keyword: str, material_type: str) -> List[str]:
        """
        生成智能标签（V5.5新增）

        将搜索关键词拆分为独立标签，并添加分类标签

        Args:
            keyword: 搜索关键词（如"black hole animation"）
            material_type: 素材类型（video/image）

        Returns:
            智能标签列表

        示例:
            输入: "black hole animation", "video"
            输出: ["black", "hole", "animation", "black_hole",
                   "hole_animation", "astronomy", "space", "science", "video"]
        """
        tags = []

        # 1. 拆分为独立单词
        words = [w.strip().lower() for w in keyword.split() if w.strip()]
        tags.extend(list(set(words)))  # 去重

        # 2. 添加双词组合（重要！提高精确匹配）
        if len(words) >= 2:
            for i in range(len(words) - 1):
                combined = f"{words[i]}_{words[i+1]}"
                tags.append(combined)

        # 3. 添加合并词（无空格）
        if len(words) >= 2:
            tags.append(''.join(words[:2]))  # 如 "blackhole"

        # 4. 自动分类标签
        category_keywords = {
            'astronomy': ['space', 'star', 'galaxy', 'planet', 'asteroid', 'comet', 'nebula',
                         'black', 'hole', 'sun', 'moon', 'cosmos', 'universe', 'stellar'],
            'biology': ['brain', 'neuron', 'cell', 'DNA', 'gene', 'protein', 'organism',
                       'bacteria', 'virus', 'blood', 'heart', 'organ', 'tissue'],
            'physics': ['atom', 'quantum', 'particle', 'energy', 'wave', 'field',
                       'relativity', 'gravity', 'force', 'motion'],
            'chemistry': ['molecule', 'chemical', 'reaction', 'element', 'compound',
                         'bond', 'acid', 'base'],
            'environment': ['climate', 'weather', 'earth', 'ocean', 'forest', 'pollution',
                           'ecosystem', 'carbon', 'greenhouse', 'renewable'],
            'technology': ['computer', 'robot', 'AI', 'digital', 'network', 'data',
                          'algorithm', 'software']
        }

        # 匹配分类
        matched_categories = []
        for category, keywords_list in category_keywords.items():
            if any(kw in keyword.lower() for kw in keywords_list):
                matched_categories.append(category)
                tags.append(category)

        # 添加通用"science"标签（如果有任何科学分类）
        if matched_categories:
            tags.append('science')

        # 5. 添加视觉特征标签
        visual_keywords = {
            'animation': ['animation', 'animated', 'motion'],
            'abstract': ['abstract', 'pattern', 'texture'],
            'macro': ['macro', 'microscopic', 'close-up', 'micro'],
            'aerial': ['aerial', 'drone', 'bird-eye', 'top-view'],
            'timelapse': ['timelapse', 'time-lapse', 'fast']
        }

        for feature, feature_keywords in visual_keywords.items():
            if any(kw in keyword.lower() for kw in feature_keywords):
                tags.append(feature)

        # 6. 添加类型标签
        tags.append(material_type)

        # 7. 去重并返回
        return list(set(tags))

    def _ai_extract_keyword(self, visual_notes: str, narration: str) -> Optional[str]:
        """
        使用AI智能提取英文关键词
        V5.5优化：更精确的搜索关键词提取，提高Pexels/Unsplash匹配率

        Args:
            visual_notes: 视觉提示
            narration: 旁白文本

        Returns:
            英文关键词或None
        """
        try:
            prompt = f"""你是素材搜索专家。分析以下科普视频场景，提取最适合在Pexels/Unsplash搜索的英文关键词。

## 场景信息
视觉需求: {visual_notes[:200]}
旁白内容: {narration[:100]}

## 关键词提取规则

### 1. 优先级排序
1) 具体物体/现象（如 black hole, DNA molecule, brain scan）
2) 动作/状态（如 rotating, glowing, flowing）
3) 场景类型（如 space, laboratory, nature）
4) 视觉风格（如 animation, abstract, microscopic）

### 2. 避免过于专业的术语
❌ 不好: "accretion disk radiation" → ✅ 好: "black hole space"
❌ 不好: "synaptic vesicles" → ✅ 好: "neuron brain"
❌ 不好: "anthropogenic forcing" → ✅ 好: "climate change earth"

### 3. 关键词组合策略
- 2-4个词为佳（太少→结果太泛，太多→无结果）
- 核心对象 + 修饰词（如 "space nebula colorful"）
- 优先视频关键词（加 "motion" "animation" "4k"）

### 4. 常见科普主题映射
- 黑洞/时空 → black hole space gravity
- DNA/基因 → DNA helix molecule biology
- 大脑/神经 → brain neuron medical
- 气候变化 → climate earth temperature
- 原子/粒子 → atom particle physics
- 细胞 → cell biology microscopic
- 星系/宇宙 → galaxy space stars

## 输出格式
**只输出2-4个英文关键词，用空格分隔，不要任何标点、换行或解释**

示例：
输入: "展示黑洞吸积盘的壮观景象"
输出: black hole accretion disk space

输入: "DNA双螺旋结构旋转动画"
输出: DNA helix rotation animation

输入: "大脑神经元突触连接"
输出: brain neuron synapse connection

现在请提取（单行输出）:"""

            result = self.ai_client.generate(prompt).strip()

            # 清洗和验证结果
            if not result:
                return None

            # 移除中文标点
            result = result.replace('。', ' ').replace('，', ' ').replace(',', ' ')

            # 处理多行：如果有换行，取第一个非空行或合并所有行
            if '\n' in result:
                lines = [line.strip() for line in result.split('\n') if line.strip()]
                if lines:
                    # 如果第一行看起来是完整的关键词，使用第一行
                    first_line = lines[0]
                    if len(first_line) < 100 and ' ' in first_line:
                        result = first_line
                        print(f"      ℹ️  AI返回多行，已取第一行: {result}")
                    else:
                        # 否则合并所有行
                        result = ' '.join(lines)
                        print(f"      ℹ️  AI返回多行，已合并: {result[:50]}")

            # 最终验证
            result = ' '.join(result.split())  # 标准化空格
            if result and len(result) < 150 and not any(c in result for c in ['。', '，', '：', ':']):
                return result
            else:
                print(f"      ⚠️  AI返回格式异常: {result[:50]}")
                return None

        except Exception as e:
            print(f"      ⚠️  AI提取失败: {str(e)}")
            return None

    def _fetch_from_pexels_videos(self, keyword: str, count: int = 3) -> List[Dict[str, Any]]:
        """
        从Pexels获取视频素材（V5.4：优化重复下载检查）

        Args:
            keyword: 英文关键词
            count: 数量

        Returns:
            素材信息列表(已转换为统一格式)
        """
        if not self.pexels_fetcher:
            return []

        try:
            print(f"   🎥 [2/4] 从Pexels搜索视频: '{keyword}'...")

            # 搜索
            videos = self.pexels_fetcher.search_videos(keyword, per_page=count)

            # 自动下载
            materials = []
            for video in videos[:count]:
                # V5.4: 统一素材ID格式
                material_id = f"pexels_video_{video['id']}"

                # V5.4: 早期退出 - 先检查数据库是否已存在（精确ID匹配）
                existing = self._check_material_exists(material_id)
                if existing:
                    print(f"       ⏭️  已存在数据库: {material_id}")
                    materials.append(existing)
                    continue

                if self.smart_fetch_config.get('auto_download', True):
                    filepath = self.pexels_fetcher.download_video(video, keyword)
                    if filepath:
                        # V5.5: 使用智能标签系统
                        smart_tags = self._generate_smart_tags(keyword, 'video')

                        # 转换为统一格式
                        material_data = {
                            'id': material_id,
                            'name': material_id,
                            'type': 'video',
                            'file_path': filepath,
                            'tags': smart_tags,  # V5.5: 智能标签
                            'description': f"Pexels视频: {keyword}",
                            'source': 'pexels',
                            'match_score': 85,
                            'rating': 4,
                            'used_count': 0
                        }
                        materials.append(material_data)

                        # V5.4: 注册到素材库（优化检查逻辑）
                        try:
                            # 再次检查（防止并发问题）
                            if not self._check_material_exists(material_id):
                                self.material_manager.add_material(
                                    name=material_id,  # V5.4: 使用统一ID
                                    file_path=filepath,
                                    material_type='video',
                                    tags=material_data['tags'],
                                    description=material_data['description']
                                )
                                print(f"       ✓ 已注册到素材库: {material_id}")
                            else:
                                print(f"       ⏭️  已在数据库，跳过注册: {material_id}")
                        except Exception as reg_error:
                            print(f"       ⚠️  注册失败: {str(reg_error)}")

            return materials

        except Exception as e:
            print(f"       ❌ Pexels视频获取失败: {str(e)}")
            return []

    def _fetch_from_pexels_photos(self, keyword: str, count: int = 3) -> List[Dict[str, Any]]:
        """从Pexels获取图片素材（V5.4：优化重复下载检查）"""
        if not self.pexels_fetcher:
            return []

        try:
            print(f"   🖼️  [3/4] 从Pexels搜索图片: '{keyword}'...")

            photos = self.pexels_fetcher.search_photos(keyword, per_page=count)

            materials = []
            for photo in photos[:count]:
                # V5.4: 统一素材ID格式
                material_id = f"pexels_photo_{photo['id']}"

                # V5.4: 早期退出 - 先检查数据库
                existing = self._check_material_exists(material_id)
                if existing:
                    print(f"       ⏭️  已存在数据库: {material_id}")
                    materials.append(existing)
                    continue

                if self.smart_fetch_config.get('auto_download', True):
                    filepath = self.pexels_fetcher.download_photo(photo, keyword)
                    if filepath:
                        # V5.5: 使用智能标签系统
                        smart_tags = self._generate_smart_tags(keyword, 'image')

                        material_data = {
                            'id': material_id,
                            'name': material_id,
                            'type': 'image',
                            'file_path': filepath,
                            'tags': smart_tags,  # V5.5: 智能标签
                            'description': f"Pexels图片: {keyword}",
                            'source': 'pexels',
                            'match_score': 75,
                            'rating': 4,
                            'used_count': 0
                        }
                        materials.append(material_data)

                        # V5.4: 注册到素材库（优化检查）
                        try:
                            if not self._check_material_exists(material_id):
                                self.material_manager.add_material(
                                    name=material_id,
                                    file_path=filepath,
                                    material_type='image',
                                    tags=material_data['tags'],
                                    description=material_data['description']
                                )
                                print(f"       ✓ 已注册到素材库: {material_id}")
                            else:
                                print(f"       ⏭️  已在数据库，跳过注册: {material_id}")
                        except Exception as reg_error:
                            print(f"       ⚠️  注册失败: {str(reg_error)}")

            return materials

        except Exception as e:
            print(f"       ❌ Pexels图片获取失败: {str(e)}")
            return []

    def _fetch_from_unsplash(self, keyword: str, count: int = 3) -> List[Dict[str, Any]]:
        """从Unsplash获取高质量图片（V5.4：优化重复下载检查）"""
        if not self.unsplash_fetcher:
            return []

        try:
            print(f"   📸 [3/4] 从Unsplash搜索图片: '{keyword}'...")

            photos = self.unsplash_fetcher.search_photos(keyword, per_page=count)

            materials = []
            for photo in photos[:count]:
                # V5.4: 统一素材ID格式
                material_id = f"unsplash_{photo['id']}"

                # V5.4: 早期退出 - 先检查数据库
                existing = self._check_material_exists(material_id)
                if existing:
                    print(f"       ⏭️  已存在数据库: {material_id}")
                    materials.append(existing)
                    continue

                if self.smart_fetch_config.get('auto_download', True):
                    filepath = self.unsplash_fetcher.download_photo(photo, keyword, quality='regular')
                    if filepath:
                        # V5.5: 使用智能标签系统
                        smart_tags = self._generate_smart_tags(keyword, 'image')

                        material_data = {
                            'id': material_id,
                            'name': material_id,
                            'type': 'image',
                            'file_path': filepath,
                            'tags': smart_tags,  # V5.5: 智能标签
                            'description': photo.get('description', f"Unsplash: {keyword}"),
                            'source': 'unsplash',
                            'match_score': 80,
                            'rating': 5,  # Unsplash质量最高
                            'used_count': 0
                        }
                        materials.append(material_data)

                        # V5.4: 注册到素材库（优化检查）
                        try:
                            if not self._check_material_exists(material_id):
                                self.material_manager.add_material(
                                    name=material_id,
                                    file_path=filepath,
                                    material_type='image',
                                    tags=material_data['tags'],
                                    description=material_data['description']
                                )
                                print(f"       ✓ 已注册到素材库: {material_id}")
                            else:
                                print(f"       ⏭️  已在数据库，跳过注册: {material_id}")
                        except Exception as reg_error:
                            print(f"       ⚠️  注册失败: {str(reg_error)}")

            return materials

        except Exception as e:
            print(f"       ❌ Unsplash获取失败: {str(e)}")
            return []

    def _recommend_with_visual_options(
        self,
        script_section: Dict[str, Any],
        visual_options: List[Dict[str, Any]],
        limit: int,
        enable_smart_fetch: bool
    ) -> List[Dict[str, Any]]:
        """
        使用visual_options多层次场景进行匹配（V5.6新增）

        Args:
            script_section: 脚本章节
            visual_options: 3个优先级的视觉方案
            limit: 返回数量
            enable_smart_fetch: 是否启用外部素材获取

        Returns:
            推荐素材列表
        """
        section_name = script_section.get('section_name', 'N/A')

        # 确保visual_options有priority字段（容错处理）
        for i, opt in enumerate(visual_options):
            if 'priority' not in opt:
                opt['priority'] = i + 1  # 按顺序分配1, 2, 3

        # 显示3个优先级方案
        print(f"\n   🎬 视觉方案（多层次）:")
        for opt in visual_options:
            priority = opt.get('priority', 0)
            desc = opt.get('description', '')[:60]
            complexity = opt.get('complexity', 'unknown')
            source = opt.get('suggested_source', '')
            print(f"      Priority {priority} ({complexity}): {desc}... [{source}]")

        # 1. 收集候选素材（合并所有优先级的关键词）
        all_keywords = []
        for opt in visual_options:
            all_keywords.extend(opt.get('keywords', []))

        # 去重关键词
        all_keywords = list(set(all_keywords))

        # 搜索本地素材库
        print(f"\n   📁 [1/4] 搜索本地素材库 (关键词: {', '.join(all_keywords[:5])}...)")
        candidates = []

        for keyword in all_keywords:
            materials = self.material_manager.search_materials(keyword)
            candidates.extend(materials)

        # 去重
        seen_ids = set()
        unique_candidates = []
        for mat in candidates:
            mat_id = mat.get('id')
            if mat_id not in seen_ids:
                seen_ids.add(mat_id)
                unique_candidates.append(mat)

        print(f"       ✓ 找到 {len(unique_candidates)} 个本地素材")

        # 2. 外部素材获取（如果需要）
        if enable_smart_fetch and len(unique_candidates) < self.smart_fetch_config.get('min_local_results', 3):
            print(f"       ⚠️  本地素材不足，尝试外部获取...")

            # 按优先级尝试搜索
            for opt in sorted(visual_options, key=lambda x: x.get('priority', 999)):
                if len(unique_candidates) >= limit:
                    break

                keywords = opt.get('keywords', [])
                search_keyword = ' '.join(keywords[:3])  # 使用前3个关键词

                # Pexels视频
                if self.pexels_fetcher and self.smart_fetch_config.get('prefer_videos', True):
                    pexels_videos = self._fetch_from_pexels_videos(
                        search_keyword,
                        count=max(2, limit - len(unique_candidates))
                    )
                    unique_candidates.extend(pexels_videos)

                # Pexels图片
                if len(unique_candidates) < limit and self.pexels_fetcher:
                    pexels_photos = self._fetch_from_pexels_photos(
                        search_keyword,
                        count=max(1, limit - len(unique_candidates))
                    )
                    unique_candidates.extend(pexels_photos)

        # 3. AI语义匹配（核心）
        print(f"\n   🧠 [AI语义匹配] 分析 {len(unique_candidates)} 个候选素材...")

        if not unique_candidates:
            print("       ❌ 未找到任何候选素材")
            return []

        # 使用AI语义匹配器
        if self.ai_semantic_matcher:
            try:
                match_result = self.ai_semantic_matcher.match_scene_to_materials(
                    visual_options,
                    unique_candidates,
                    section_name
                )

                # 解析匹配结果
                best_material = match_result.get('best_material')
                selected_priority = match_result.get('selected_priority', 3)
                semantic_score = match_result.get('semantic_score', 0)
                reasoning = match_result.get('reasoning', '')

                if best_material:
                    print(f"       ✅ 最佳匹配: {best_material.get('name', 'N/A')}")
                    print(f"       📊 匹配Priority {selected_priority} | 语义评分: {semantic_score}%")
                    print(f"       💡 AI分析: {reasoning[:80]}...")

                    # 为最佳素材添加匹配信息
                    best_material['match_score'] = semantic_score
                    best_material['matched_priority'] = selected_priority
                    best_material['match_reason'] = reasoning
                    best_material['matched_elements'] = match_result.get('matched_elements', [])
                    best_material['missing_elements'] = match_result.get('missing_elements', [])

                    # 构建返回列表（最佳素材+备选）
                    result_materials = [best_material]

                    # 添加备选素材
                    for alt in match_result.get('alternative_matches', [])[:limit-1]:
                        alt_material = alt.get('material')
                        if alt_material:
                            alt_material['match_score'] = alt.get('score', 0)
                            alt_material['matched_priority'] = alt.get('priority', 3)
                            alt_material['match_reason'] = alt.get('reasoning', '')
                            result_materials.append(alt_material)

                    return result_materials[:limit]
                else:
                    print("       ⚠️  AI未找到合适匹配")

            except Exception as e:
                print(f"       ⚠️  AI语义匹配异常: {str(e)}")

        # 4. 降级到传统评分（AI失败时）
        print("       ⚠️  使用传统关键词匹配...")
        return self._fallback_keyword_matching(visual_options, unique_candidates, limit)

    def _fallback_keyword_matching(
        self,
        visual_options: List[Dict[str, Any]],
        materials: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        降级匹配逻辑（AI失败时使用关键词匹配）

        Args:
            visual_options: 视觉方案
            materials: 候选素材
            limit: 返回数量

        Returns:
            推荐素材列表
        """
        # 提取所有关键词（优先级加权）
        weighted_keywords = []
        for opt in visual_options:
            priority = opt.get('priority', 3)
            keywords = opt.get('keywords', [])
            weight = 4 - priority  # Priority 1权重3，Priority 2权重2，Priority 3权重1
            weighted_keywords.extend([(kw.lower(), weight) for kw in keywords])

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
            for keyword, weight in weighted_keywords:
                if keyword in mat_text:
                    score += 10 * weight

            # 类型加分
            if mat.get('type') == 'video':
                score += 20

            # 来源加分
            if mat.get('source') in ['pexels', 'unsplash']:
                score += 10

            mat['match_score'] = score
            mat['matched_priority'] = 3  # 降级默认Priority 3
            mat['match_reason'] = '关键词匹配（降级模式）'

            scored_materials.append(mat)

        # 排序并返回
        scored_materials.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        return scored_materials[:limit]
