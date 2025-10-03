"""
素材语义分析器
使用GLM-4V视觉模型分析素材内容，生成详细场景描述
V5.6新增
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List
import subprocess
import tempfile

# 导入AI客户端
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_script_generator'))
from ai_client import AIClient


class SemanticAnalyzer:
    """素材语义分析器 - 为素材生成详细场景描述"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化语义分析器

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化AI客户端
        self.ai_client = AIClient(self.config['ai'])

    def analyze_material(
        self,
        material: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        分析单个素材，生成语义元数据

        Args:
            material: 素材数据

        Returns:
            语义元数据字典，如果分析失败返回None
        """
        file_path = material.get('file_path', '')
        material_type = material.get('type', '')

        if not file_path or not os.path.exists(file_path):
            print(f"   ⚠️  文件不存在: {file_path}")
            return None

        try:
            if material_type == 'video':
                return self._analyze_video(file_path, material)
            elif material_type == 'image':
                return self._analyze_image(file_path, material)
            else:
                print(f"   ⚠️  不支持的类型: {material_type}")
                return None

        except Exception as e:
            print(f"   ❌ 分析失败: {str(e)}")
            return None

    def _analyze_video(
        self,
        video_path: str,
        material: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        分析视频素材

        Args:
            video_path: 视频文件路径
            material: 素材数据

        Returns:
            语义元数据
        """
        # 提取关键帧
        keyframes = self._extract_keyframes(video_path, num_frames=3)

        if not keyframes:
            print(f"   ⚠️  无法提取关键帧")
            return None

        # 分析第一帧（主要场景）
        semantic_data = self._analyze_image_with_ai(keyframes[0], material)

        # 清理临时文件
        for frame in keyframes:
            try:
                os.remove(frame)
            except:
                pass

        return semantic_data

    def _analyze_image(
        self,
        image_path: str,
        material: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        分析图片素材

        Args:
            image_path: 图片路径
            material: 素材数据

        Returns:
            语义元数据
        """
        return self._analyze_image_with_ai(image_path, material)

    def _analyze_image_with_ai(
        self,
        image_path: str,
        material: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI分析图片（GLM-4V视觉模型）

        Args:
            image_path: 图片路径
            material: 素材数据

        Returns:
            语义元数据
        """
        # 检查是否支持视觉模型
        ai_config = self.config.get('ai', {})
        provider = ai_config.get('provider', 'openai')

        # 当前只有GLM支持视觉模型，其他降级到文本分析
        if provider != 'glm':
            print(f"   ⚠️  当前AI提供商({provider})不支持视觉分析，使用文本分析降级")
            return self._fallback_text_analysis(material)

        # 构建分析prompt
        prompt = self._build_vision_prompt()

        try:
            # 调用GLM-4V视觉模型（需要API支持）
            # 注意：这里假设AI客户端支持图片输入，实际需要根据API调整
            result = self._call_vision_api(image_path, prompt)

            if result:
                return result
            else:
                # 降级到文本分析
                return self._fallback_text_analysis(material)

        except Exception as e:
            print(f"   ⚠️  视觉分析失败: {str(e)}，使用文本分析降级")
            return self._fallback_text_analysis(material)

    def _call_vision_api(
        self,
        image_path: str,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        调用视觉API（GLM-4V）

        Args:
            image_path: 图片路径
            prompt: 分析prompt

        Returns:
            分析结果
        """
        # TODO: 这里需要根据GLM-4V API实际接口调整
        # 当前版本暂时不实现图片上传，直接降级到文本分析
        # 未来可以添加：
        # 1. 读取图片并base64编码
        # 2. 调用GLM-4V vision API
        # 3. 解析返回结果

        return None

    def _fallback_text_analysis(
        self,
        material: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        降级文本分析（基于素材名称、描述、标签）

        Args:
            material: 素材数据

        Returns:
            语义元数据
        """
        # 提取文本信息
        name = material.get('name', '')
        description = material.get('description', '')
        tags = material.get('tags', [])

        # 构建分析文本
        text = f"素材: {name}\n描述: {description}\n标签: {', '.join(tags)}"

        # 构建prompt
        prompt = f"""分析以下素材的场景内容，生成详细的语义描述。

{text}

请以JSON格式输出：
{{
  "scene_description": "详细的场景描述（50-100字）",
  "main_objects": ["主要对象1", "主要对象2", "..."],
  "actions": ["动作1", "动作2", "..."],
  "visual_style": "视觉风格描述",
  "viewpoint": "视角/镜头类型",
  "has_human": true/false,
  "complexity": "low/medium/high",
  "best_for_scenes": ["适合的场景类型1", "场景类型2", "..."]
}}

只返回JSON，无其他文字。"""

        try:
            result = self.ai_client.generate_json(prompt)
            return result
        except Exception as e:
            print(f"   ⚠️  文本分析失败: {str(e)}")
            # 返回基础元数据
            return self._create_basic_metadata(material)

    def _create_basic_metadata(
        self,
        material: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建基础语义元数据（最低降级方案）

        Args:
            material: 素材数据

        Returns:
            基础元数据
        """
        description = material.get('description', '')
        tags = material.get('tags', [])

        return {
            'scene_description': description or f"素材: {material.get('name', '')}",
            'main_objects': tags[:3] if tags else [],
            'actions': [],
            'visual_style': material.get('type', 'unknown'),
            'viewpoint': 'unknown',
            'has_human': False,
            'complexity': 'medium',
            'best_for_scenes': tags[:2] if tags else []
        }

    def _extract_keyframes(
        self,
        video_path: str,
        num_frames: int = 3
    ) -> List[str]:
        """
        从视频提取关键帧

        Args:
            video_path: 视频路径
            num_frames: 提取帧数

        Returns:
            关键帧文件路径列表
        """
        keyframes = []

        try:
            # 获取视频时长
            duration_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]

            result = subprocess.run(
                duration_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            duration = float(result.stdout.strip())

            # 计算提取时间点（均匀分布）
            timestamps = [duration * i / (num_frames + 1) for i in range(1, num_frames + 1)]

            # 提取关键帧
            for i, timestamp in enumerate(timestamps):
                temp_file = os.path.join(
                    tempfile.gettempdir(),
                    f"keyframe_{os.getpid()}_{i}.jpg"
                )

                extract_cmd = [
                    'ffmpeg',
                    '-ss', str(timestamp),
                    '-i', video_path,
                    '-vframes', '1',
                    '-y',
                    temp_file
                ]

                result = subprocess.run(
                    extract_cmd,
                    capture_output=True,
                    timeout=10
                )

                if result.returncode == 0 and os.path.exists(temp_file):
                    keyframes.append(temp_file)

        except Exception as e:
            print(f"   ⚠️  提取关键帧失败: {str(e)}")

        return keyframes

    def _build_vision_prompt(self) -> str:
        """
        构建视觉分析prompt

        Returns:
            prompt文本
        """
        return """分析这张图片的内容，用于科普视频素材匹配。

请详细描述：
1. 主要视觉对象（具体物体、人物、场景）
2. 动作或状态（静态/动态，发生了什么）
3. 视觉风格（CG动画/实拍/插画/图表等）
4. 镜头视角（特写/全景/俯视等）
5. 是否有人物出现
6. 适合哪些科普场景

以JSON格式输出：
{
  "scene_description": "详细场景描述（50-100字）",
  "main_objects": ["对象1", "对象2"],
  "actions": ["动作1", "动作2"],
  "visual_style": "视觉风格",
  "viewpoint": "视角类型",
  "has_human": true/false,
  "complexity": "low/medium/high",
  "best_for_scenes": ["场景1", "场景2"]
}

只返回JSON，无其他内容。"""


def auto_analyze_new_material(
    material: Dict[str, Any],
    config_path: str = 'config/settings.json'
) -> Dict[str, Any]:
    """
    自动分析新素材并添加语义元数据（工具函数）

    Args:
        material: 新添加的素材数据
        config_path: 配置文件路径

    Returns:
        添加了semantic_metadata的素材数据
    """
    analyzer = SemanticAnalyzer(config_path)

    print(f"   🔍 正在分析素材: {material.get('name', 'N/A')}...")

    semantic_metadata = analyzer.analyze_material(material)

    if semantic_metadata:
        material['semantic_metadata'] = semantic_metadata
        print(f"   ✅ 语义分析完成")
        print(f"      场景: {semantic_metadata.get('scene_description', 'N/A')[:60]}...")
    else:
        print(f"   ⚠️  语义分析失败，使用基础元数据")
        material['semantic_metadata'] = analyzer._create_basic_metadata(material)

    return material
