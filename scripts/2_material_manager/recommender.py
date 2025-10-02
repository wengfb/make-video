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

        # 智能获取配置
        self.smart_fetch_config = self.config.get('smart_material_fetch', {
            'enable': True,
            'auto_download': True,
            'prefer_videos': True,
            'min_local_results': 3
        })

    def recommend_for_script_section(
        self,
        script_section: Dict[str, Any],
        limit: int = 5,
        enable_smart_fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """
        为脚本章节推荐素材 (智能四级获取)

        Args:
            script_section: 脚本章节数据
            limit: 推荐数量
            enable_smart_fetch: 是否启用智能获取 (从外部API)

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
        V5.3: 优化评分算法

        Args:
            material: 素材数据
            requirements: 需求数据

        Returns:
            匹配分数 (0-100)
        """
        score = 0.0

        # ✨ V5.3: 类型匹配 (提高视频权重)
        material_type = material.get('type')
        required_types = requirements.get('material_types', [])

        if material_type == 'video':
            score += 50  # 视频素材优先 (从30→50)
        elif material_type in required_types:
            score += 30

        # ✨ V5.3: 标签匹配 (提高权重)
        material_tags = set(material.get('tags', []))
        required_tags = set(requirements.get('tags', []))
        tag_overlap = len(material_tags & required_tags)
        if tag_overlap > 0:
            score += min(tag_overlap * 15, 40)  # 从30→40

        # ✨ V5.3: 关键词匹配 (支持部分匹配)
        material_text = (
            material.get('name', '') + ' ' +
            material.get('description', '') + ' ' +
            ' '.join(material.get('tags', []))
        ).lower()

        keywords = requirements.get('keywords', [])
        keyword_score = 0
        for keyword in keywords:
            # 支持多词关键词的部分匹配
            keyword_parts = keyword.lower().split()
            matches = sum(1 for part in keyword_parts if part in material_text)
            if matches > 0:
                keyword_score += min(matches * 8, 20)

        score += min(keyword_score, 30)

        # 评分加成
        rating = material.get('rating')
        if rating:
            score += rating * 2

        # ✨ V5.3: 使用历史惩罚 (避免重复)
        used_count = material.get('used_count', 0)
        if used_count == 0:
            score += 5  # 新素材加分
        elif used_count <= 2:
            score += 2  # 少用素材小加分
        elif used_count > 5:
            score -= min((used_count - 5) * 3, 15)  # 用太多次减分

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

    def _ai_extract_keyword(self, visual_notes: str, narration: str) -> Optional[str]:
        """
        使用AI智能提取英文关键词
        V5.3新增

        Args:
            visual_notes: 视觉提示
            narration: 旁白文本

        Returns:
            英文关键词或None
        """
        try:
            prompt = f"""分析以下科普视频视觉需求,提取最相关的Pexels/Unsplash搜索关键词。

视觉提示: {visual_notes[:200]}
旁白: {narration[:100]}

要求:
1. 提取1-3个最相关的英文关键词
2. 优先提取具体的视觉元素(如动画、场景、物体)
3. 关键词要适合在免费素材库搜索
4. 只返回关键词,不要其他内容

示例:
输入: "显示地球温度计动画，温度不断上升"
输出: earth temperature rising animation

输入: "汽车在阳光下，车内温度上升"
输出: car greenhouse effect sunlight

输入: "展示全球温度变化曲线"
输出: global temperature chart rising

现在请提取关键词:"""

            result = self.ai_client.generate(prompt).strip()

            # 验证结果
            if result and len(result) < 100 and not any(c in result for c in ['。', '，', '\n']):
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
                        # 转换为统一格式（V5.4：统一命名）
                        material_data = {
                            'id': material_id,
                            'name': material_id,  # V5.4: 统一使用material_id作为名称
                            'type': 'video',
                            'file_path': filepath,
                            'tags': [keyword, 'pexels', 'HD'],
                            'description': f"Pexels视频: {keyword}",
                            'source': 'pexels',
                            'match_score': 85,  # 外部视频默认高分
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
                        material_data = {
                            'id': material_id,
                            'name': material_id,  # V5.4: 统一使用material_id
                            'type': 'image',
                            'file_path': filepath,
                            'tags': [keyword, 'pexels', 'HD'],
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
                        material_data = {
                            'id': material_id,
                            'name': material_id,  # V5.4: 统一使用material_id
                            'type': 'image',
                            'file_path': filepath,
                            'tags': [keyword, 'unsplash', 'HD'],
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
