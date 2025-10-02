"""
AI内容生成器（V5.5新增）
当现有素材不符合要求时，使用AI生成定制化图片素材
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# 导入AI图片生成器
sys.path.insert(0, os.path.dirname(__file__))
from ai_generator import AIImageGenerator


class AIContentGenerator:
    """AI内容生成器（支持图片生成）"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化AI内容生成器

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化图片生成器
        self.image_generator = AIImageGenerator(config_path)

        # 生成配置
        self.gen_config = self.config.get('smart_material_selection', {})
        self.enable_auto_generation = self.gen_config.get('enable_auto_generation', True)
        self.generation_provider = self.gen_config.get('generation_provider', 'cogview')
        self.max_generation_per_video = self.gen_config.get('max_generation_per_video', 5)

        # 费用追踪
        self.generation_count = 0
        self.total_cost = 0.0

    def generate_material(
        self,
        script_section: Dict[str, Any],
        generation_prompt: str,
        prefer_video: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        根据需求生成素材

        Args:
            script_section: 脚本章节
            generation_prompt: 生成提示词
            prefer_video: 是否优先生成视频

        Returns:
            生成的素材信息，如果失败返回None
        """
        if not self.enable_auto_generation:
            print("   ⚠️  AI自动生成未启用")
            return None

        # 检查生成次数限制
        if self.generation_count >= self.max_generation_per_video:
            print(f"   ⚠️  已达到单个视频最大生成次数限制({self.max_generation_per_video})")
            return None

        print(f"\n   🎨 AI生成素材 (提供商: {self.generation_provider})...")

        # 尝试视频生成（如果可用且prefer_video=True）
        if prefer_video and self._is_video_generation_available():
            result = self._generate_video(script_section, generation_prompt)
            if result:
                return result

        # 图片生成（默认或降级）
        return self._generate_image(script_section, generation_prompt)

    def _generate_image(
        self,
        script_section: Dict[str, Any],
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        使用CogView/DALL-E生成图片

        Args:
            script_section: 脚本章节
            prompt: 生成提示词

        Returns:
            生成的素材信息
        """
        visual_notes = script_section.get('visual_notes', '')
        section_name = script_section.get('section_name', '未命名章节')

        # 优化生成prompt
        enhanced_prompt = self._enhance_generation_prompt(prompt, visual_notes)

        print(f"   📝 生成提示: {enhanced_prompt[:100]}...")

        # 估算成本
        estimated_cost = self._estimate_cost('image')
        if not self._check_budget(estimated_cost):
            print(f"   ⚠️  预算不足，跳过生成")
            return None

        # 调用图片生成（添加请求间隔避免限流）
        try:
            import time
            time.sleep(0.5)  # 500ms延迟，避免连续请求触发429

            results = self.image_generator.generate_image(
                prompt=enhanced_prompt,
                size="1024x1024",
                quality="hd"
            )

            # generate_image返回的是列表
            if not results or not isinstance(results, list) or len(results) == 0:
                print(f"   ❌ 生成失败: 未返回有效结果")
                return None

            # 取第一个结果
            result = results[0]

            # 保存图片到本地
            output_dir = 'materials/ai_generated'
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"ai_generated_{timestamp}.png"
            file_path = self.image_generator.save_generated_image(
                result,
                output_dir,
                filename
            )

            # 转换为统一素材格式
            material_id = f"ai_generated_{timestamp}"
            material_data = {
                'id': material_id,
                'name': f"AI生成_{section_name}",
                'type': 'image',
                'file_path': file_path,
                'tags': self._generate_tags_for_ai_content(enhanced_prompt),
                'description': f"AI生成: {prompt[:100]}",
                'source': 'ai_generated',
                'generation_prompt': enhanced_prompt,
                'generation_provider': self.generation_provider,
                'match_score': 95,  # AI定制，高分
                'rating': 5,
                'used_count': 0,
                'ai_generated': True,
                'generation_cost': estimated_cost
            }

            # 更新统计
            self.generation_count += 1
            self.total_cost += estimated_cost

            print(f"   ✅ 生成成功: {file_path}")
            print(f"   💰 成本: ¥{estimated_cost:.3f}")

            return material_data

        except Exception as e:
            import traceback
            print(f"   ❌ 生成异常: {str(e)}")
            traceback.print_exc()
            return None

    def _generate_video(
        self,
        script_section: Dict[str, Any],
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        视频生成（预留接口）

        可集成:
        - Runway Gen-2/Gen-3
        - Pika Labs
        - Stable Video Diffusion

        Args:
            script_section: 脚本章节
            prompt: 生成提示词

        Returns:
            生成的视频素材，暂未实现返回None
        """
        print("   ℹ️  视频生成功能开发中，降级到图片生成")
        return None

    def _enhance_generation_prompt(self, prompt: str, visual_notes: str) -> str:
        """
        增强生成提示词

        Args:
            prompt: 原始提示词
            visual_notes: 视觉提示

        Returns:
            增强后的提示词
        """
        # 基础提示词
        enhanced = prompt.strip()

        # 添加视觉细节（如果prompt较短）
        if len(enhanced) < 100 and visual_notes:
            enhanced += f"\n\n场景细节: {visual_notes[:150]}"

        # 添加风格要求
        style_requirements = """

风格要求:
- 科普教育风格，清晰易懂
- 高分辨率，专业品质
- 适合视频使用
- 色彩鲜明，视觉吸引力强
- 无文字说明，纯视觉表现
"""
        enhanced += style_requirements

        return enhanced

    def _generate_tags_for_ai_content(self, prompt: str) -> list:
        """
        为AI生成的内容生成标签

        Args:
            prompt: 生成提示词

        Returns:
            标签列表
        """
        tags = ['ai-generated', self.generation_provider, 'custom', 'high-quality']

        # 从prompt中提取关键词
        keywords = ['space', 'black hole', 'brain', 'DNA', 'cell', 'atom',
                   'climate', 'earth', 'animation', 'science']

        for keyword in keywords:
            if keyword.lower() in prompt.lower():
                tags.extend(keyword.split())

        return list(set(tags))

    def _is_video_generation_available(self) -> bool:
        """
        检查视频生成是否可用

        Returns:
            是否可用
        """
        # TODO: 检查Runway/Pika等API配置
        return False

    def _estimate_cost(self, content_type: str) -> float:
        """
        估算生成成本

        Args:
            content_type: 内容类型 (image/video)

        Returns:
            成本（人民币）
        """
        costs = {
            'image_cogview': 0.05,      # CogView-4: ¥0.05/张
            'image_dalle': 0.04,        # DALL-E 3: $0.04/张 ≈ ¥0.29
            'video_runway': 0.50,       # Runway: $0.50/秒 ≈ ¥3.6/秒
        }

        key = f"{content_type}_{self.generation_provider}"
        return costs.get(key, 0.05)

    def _check_budget(self, estimated_cost: float) -> bool:
        """
        检查预算

        Args:
            estimated_cost: 估算成本

        Returns:
            是否在预算内
        """
        max_budget = self.gen_config.get('max_generation_budget_per_video', 10.0)

        if self.total_cost + estimated_cost > max_budget:
            print(f"   ⚠️  超出预算限制 (已用¥{self.total_cost:.2f} + 预估¥{estimated_cost:.2f} > 限额¥{max_budget:.2f})")
            return False

        return True

    def get_generation_stats(self) -> Dict[str, Any]:
        """
        获取生成统计

        Returns:
            统计信息
        """
        return {
            'generation_count': self.generation_count,
            'total_cost': self.total_cost,
            'provider': self.generation_provider
        }


# 测试代码
if __name__ == "__main__":
    generator = AIContentGenerator()

    test_section = {
        'section_name': '黑洞形成',
        'narration': '当一颗大质量恒星坍缩时，形成黑洞',
        'visual_notes': '展示恒星坍缩成黑洞的过程动画'
    }

    test_prompt = """
请生成一个黑洞形成的科普图片:
- 展示恒星坍缩成黑洞的过程
- 科学准确，视觉震撼
- 适合科普视频使用
"""

    result = generator.generate_material(test_section, test_prompt)

    if result:
        print("\n=== 生成成功 ===")
        print(f"素材ID: {result['id']}")
        print(f"文件路径: {result['file_path']}")
        print(f"标签: {result['tags']}")
        print(f"成本: ¥{result.get('generation_cost', 0):.3f}")

    stats = generator.get_generation_stats()
    print(f"\n=== 统计 ===")
    print(f"生成次数: {stats['generation_count']}")
    print(f"总成本: ¥{stats['total_cost']:.2f}")
