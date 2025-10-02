"""
Ken Burns效果生成器
为静态图片添加动态缩放和平移效果
"""

from typing import Dict, Any


class KenBurnsGenerator:
    """Ken Burns效果生成器"""

    def __init__(self):
        """初始化Ken Burns生成器"""
        pass

    def apply_ken_burns(
        self,
        clip,
        analysis: Dict[str, Any],
        duration: float
    ):
        """
        根据内容分析应用Ken Burns效果

        Args:
            clip: moviepy ImageClip对象
            analysis: 章节语义分析结果
            duration: 持续时长

        Returns:
            应用效果后的clip
        """
        energy = analysis['energy_level']
        emotion = analysis['emotion']

        # 1. 决定运动类型
        movement_type = self._decide_movement_type(energy, emotion)

        # 2. 应用效果
        if movement_type == 'zoom_in_slow':
            return self._zoom_in_slow(clip, duration)
        elif movement_type == 'zoom_in_fast':
            return self._zoom_in_fast(clip, duration)
        elif movement_type == 'zoom_out':
            return self._zoom_out(clip, duration)
        elif movement_type == 'pan_left':
            return self._pan_horizontal(clip, duration, direction='left')
        elif movement_type == 'pan_right':
            return self._pan_horizontal(clip, duration, direction='right')
        elif movement_type == 'diagonal_zoom':
            return self._diagonal_zoom(clip, duration)
        else:  # static
            return clip

    def _decide_movement_type(self, energy: float, emotion: str) -> str:
        """
        决定运动类型

        规则：
        - 极高能量(8+): 快速放大，强烈冲击
        - 高能量(6-8): 缓慢放大，吸引注意
        - 中能量(4-6): 水平平移，平稳展示
        - 低能量(<4): 缩小或静止，舒缓氛围
        - 特殊情绪(满足感): 拉远总结

        Args:
            energy: 能量等级
            emotion: 情绪

        Returns:
            运动类型
        """
        if energy >= 8.5:
            return 'zoom_in_fast'      # 极高能量 → 快速放大
        elif energy >= 7.5:
            return 'diagonal_zoom'     # 高能量 → 对角缩放
        elif energy >= 6.0:
            return 'zoom_in_slow'      # 中高能量 → 缓慢放大
        elif energy >= 4.5:
            return 'pan_left'          # 中等能量 → 水平平移
        elif emotion == 'satisfied':
            return 'zoom_out'          # 满足感 → 拉远
        elif energy >= 3.0:
            return 'pan_right'         # 低能量 → 缓慢平移
        else:
            return 'static'            # 极低能量 → 静止

    def _zoom_in_slow(self, clip, duration: float):
        """
        缓慢放大效果（1.0 → 1.15）

        适用场景：
        - 中高能量章节
        - 吸引注意但不过于激进

        Args:
            clip: 图片clip
            duration: 持续时长

        Returns:
            应用效果后的clip
        """
        def resize_func(t):
            progress = t / duration
            # 缓慢放大到1.15倍
            return 1.0 + 0.15 * progress

        return clip.resize(resize_func)

    def _zoom_in_fast(self, clip, duration: float):
        """
        快速放大效果（1.0 → 1.3）

        适用场景：
        - 高能量、激动人心的章节
        - 强调重点、冲击力强

        Args:
            clip: 图片clip
            duration: 持续时长

        Returns:
            应用效果后的clip
        """
        def resize_func(t):
            progress = t / duration
            # 快速放大到1.3倍
            return 1.0 + 0.3 * progress

        return clip.resize(resize_func)

    def _zoom_out(self, clip, duration: float):
        """
        缩小效果（1.2 → 1.0）

        适用场景：
        - 总结、结论章节
        - 拉远视角，展示全貌

        Args:
            clip: 图片clip
            duration: 持续时长

        Returns:
            应用效果后的clip
        """
        def resize_func(t):
            progress = t / duration
            # 从1.2倍缩小到正常
            return 1.2 - 0.2 * progress

        return clip.resize(resize_func)

    def _pan_horizontal(self, clip, duration: float, direction: str = 'left'):
        """
        水平平移效果

        适用场景：
        - 中等能量章节
        - 平稳展示，不过于激烈

        Args:
            clip: 图片clip
            duration: 持续时长
            direction: 方向 ('left' or 'right')

        Returns:
            应用效果后的clip
        """
        w, h = clip.size

        def position_func(t):
            progress = t / duration

            if direction == 'left':
                # 向左平移（图片向左滑动）
                x_offset = -int(w * 0.08 * progress)
            else:
                # 向右平移
                x_offset = int(w * 0.08 * progress)

            return (x_offset, 0)

        # 先放大图片以避免边缘黑边
        clip = clip.resize(1.15)

        return clip.set_position(position_func)

    def _diagonal_zoom(self, clip, duration: float):
        """
        对角缩放效果（同时缩放+平移）

        适用场景：
        - 高能量章节
        - 更动态的效果

        Args:
            clip: 图片clip
            duration: 持续时长

        Returns:
            应用效果后的clip
        """
        w, h = clip.size

        def resize_func(t):
            progress = t / duration
            return 1.0 + 0.2 * progress

        def position_func(t):
            progress = t / duration
            # 从右下角放大
            x_offset = -int(w * 0.05 * progress)
            y_offset = -int(h * 0.05 * progress)
            return (x_offset, y_offset)

        clip = clip.resize(resize_func)
        return clip.set_position(position_func)

    def get_movement_description(self, movement_type: str) -> str:
        """
        获取运动类型描述

        Args:
            movement_type: 运动类型

        Returns:
            描述文字
        """
        descriptions = {
            'zoom_in_slow': '缓慢放大 (1.0→1.15)',
            'zoom_in_fast': '快速放大 (1.0→1.3)',
            'zoom_out': '缩小展开 (1.2→1.0)',
            'pan_left': '向左平移',
            'pan_right': '向右平移',
            'diagonal_zoom': '对角缩放',
            'static': '静止'
        }

        return descriptions.get(movement_type, '未知效果')


# 测试代码
if __name__ == "__main__":
    # 模拟测试（需要moviepy）
    try:
        from moviepy.editor import ImageClip
        import numpy as np

        print("🎨 Ken Burns效果测试\n")
        print("=" * 60)

        # 创建测试图片
        test_image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        clip = ImageClip(test_image).set_duration(5.0)

        generator = KenBurnsGenerator()

        # 测试各种能量等级
        test_cases = [
            {'energy_level': 9.0, 'emotion': 'excitement', 'name': '极高能量'},
            {'energy_level': 7.0, 'emotion': 'focus', 'name': '高能量'},
            {'energy_level': 5.0, 'emotion': 'curiosity', 'name': '中等能量'},
            {'energy_level': 3.0, 'emotion': 'calm', 'name': '低能量'},
            {'energy_level': 5.0, 'emotion': 'satisfied', 'name': '满足感'}
        ]

        for test in test_cases:
            movement = generator._decide_movement_type(
                test['energy_level'],
                test['emotion']
            )
            desc = generator.get_movement_description(movement)

            print(f"\n{test['name']} (能量{test['energy_level']}, {test['emotion']})")
            print(f"  运动类型: {movement}")
            print(f"  描述: {desc}")

        print("\n" + "=" * 60)
        print("\n✅ 测试完成！")

    except ImportError:
        print("⚠️  moviepy未安装，跳过实际效果测试")
        print("测试逻辑:")

        generator = KenBurnsGenerator()

        test_analyses = [
            {'energy_level': 9.2, 'emotion': 'excitement'},
            {'energy_level': 6.5, 'emotion': 'curiosity'},
            {'energy_level': 4.0, 'emotion': 'calm'},
            {'energy_level': 5.0, 'emotion': 'satisfied'}
        ]

        for analysis in test_analyses:
            movement = generator._decide_movement_type(
                analysis['energy_level'],
                analysis['emotion']
            )
            print(f"能量{analysis['energy_level']}: {movement}")
