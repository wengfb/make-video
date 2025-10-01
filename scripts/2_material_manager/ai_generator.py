"""
AI图片生成器
支持多种AI图片生成服务（DALL-E, Stable Diffusion等）
"""

import json
import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64


class AIImageGenerator:
    """AI图片生成器"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化AI图片生成器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.ai_image_config = self.config.get('ai_image', {})
        self.provider = self.ai_image_config.get('provider', 'dalle')
        self.api_key = self.ai_image_config.get('api_key', os.getenv('OPENAI_API_KEY', ''))

    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1
    ) -> List[Dict[str, Any]]:
        """
        生成图片

        Args:
            prompt: 图片描述提示词
            size: 图片尺寸 (DALL-E: "1024x1024", "1792x1024", "1024x1792")
            quality: 质量 ("standard" or "hd")
            style: 风格 ("vivid" or "natural")
            n: 生成数量 (1-10)

        Returns:
            生成结果列表，每项包含url或b64_json
        """
        if self.provider == 'dalle':
            return self._generate_dalle(prompt, size, quality, style, n)
        elif self.provider == 'stable-diffusion':
            return self._generate_stable_diffusion(prompt, size, n)
        else:
            raise ValueError(f"不支持的AI图片生成服务: {self.provider}")

    def generate_from_script(
        self,
        script_section: Dict[str, Any],
        image_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        根据脚本章节生成配图

        Args:
            script_section: 脚本章节数据
            image_count: 生成图片数量

        Returns:
            生成的图片列表
        """
        # 提取关键信息
        narration = script_section.get('narration', '')
        visual_notes = script_section.get('visual_notes', '')

        # 构建提示词
        prompt = self._build_image_prompt(narration, visual_notes)

        print(f"\n🎨 正在生成配图...")
        print(f"   提示词: {prompt[:100]}...")

        try:
            results = self.generate_image(
                prompt=prompt,
                size="1024x1024",
                n=min(image_count, 3)  # DALL-E限制
            )
            return results
        except Exception as e:
            print(f"❌ 图片生成失败: {str(e)}")
            return []

    def save_generated_image(
        self,
        image_data: Dict[str, Any],
        output_dir: str,
        filename: Optional[str] = None
    ) -> str:
        """
        保存生成的图片

        Args:
            image_data: 图片数据（包含url或b64_json）
            output_dir: 输出目录
            filename: 文件名（可选）

        Returns:
            保存的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ai_generated_{timestamp}.png"

        filepath = os.path.join(output_dir, filename)

        # 下载或解码图片
        if 'url' in image_data:
            # 从URL下载
            response = requests.get(image_data['url'])
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)

        elif 'b64_json' in image_data:
            # 解码base64
            image_bytes = base64.b64decode(image_data['b64_json'])
            with open(filepath, 'wb') as f:
                f.write(image_bytes)

        else:
            raise ValueError("图片数据格式错误")

        print(f"✅ 图片已保存: {filepath}")
        return filepath

    def _generate_dalle(
        self,
        prompt: str,
        size: str,
        quality: str,
        style: Optional[str],
        n: int
    ) -> List[Dict[str, Any]]:
        """使用DALL-E生成图片"""
        if not self.api_key:
            raise ValueError("未配置DALL-E API密钥")

        url = "https://api.openai.com/v1/images/generations"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': self.ai_image_config.get('model', 'dall-e-3'),
            'prompt': prompt,
            'n': n,
            'size': size,
            'quality': quality
        }

        if style:
            data['style'] = style

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])

        except requests.exceptions.RequestException as e:
            raise Exception(f"DALL-E API调用失败: {str(e)}")

    def _generate_stable_diffusion(
        self,
        prompt: str,
        size: str,
        n: int
    ) -> List[Dict[str, Any]]:
        """使用Stable Diffusion生成图片"""
        # 这里是Stable Diffusion的接口示例
        # 需要根据实际使用的服务（如Stability AI, Replicate等）调整

        api_url = self.ai_image_config.get('api_url', '')
        api_key = self.ai_image_config.get('sd_api_key', '')

        if not api_url or not api_key:
            raise ValueError("未配置Stable Diffusion服务")

        # 解析尺寸
        width, height = map(int, size.split('x'))

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'prompt': prompt,
            'width': width,
            'height': height,
            'samples': n
        }

        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()

            # 根据具体API返回格式调整
            return result.get('images', [])

        except requests.exceptions.RequestException as e:
            raise Exception(f"Stable Diffusion API调用失败: {str(e)}")

    def _build_image_prompt(self, narration: str, visual_notes: str) -> str:
        """
        根据脚本内容构建图片生成提示词

        Args:
            narration: 旁白文本
            visual_notes: 视觉提示

        Returns:
            优化后的提示词
        """
        # 简化叙述，提取关键视觉元素
        prompt_parts = []

        if visual_notes:
            prompt_parts.append(visual_notes)

        # 从旁白中提取关键词（这里简化处理，实际可以用NLP）
        if narration and not visual_notes:
            # 截取前200字符作为提示
            prompt_parts.append(narration[:200])

        prompt = ' '.join(prompt_parts)

        # 添加风格指导
        style_guide = self.ai_image_config.get('default_style', 'educational illustration, clear, simple')
        prompt = f"{prompt}. Style: {style_guide}"

        return prompt

    def suggest_prompts_for_script(self, script: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        为整个脚本建议图片生成提示词

        Args:
            script: 完整脚本数据

        Returns:
            提示词列表，每项包含section和prompt
        """
        suggestions = []

        sections = script.get('sections', [])
        for section in sections:
            section_name = section.get('section_name', '')
            visual_notes = section.get('visual_notes', '')
            narration = section.get('narration', '')

            if visual_notes or narration:
                prompt = self._build_image_prompt(narration, visual_notes)
                suggestions.append({
                    'section': section_name,
                    'prompt': prompt,
                    'visual_notes': visual_notes
                })

        return suggestions
