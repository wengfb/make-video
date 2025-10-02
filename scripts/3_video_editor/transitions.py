"""
转场效果库
提供多种视频转场效果
"""

from typing import Callable, List
import numpy as np
from moviepy.video.fx import FadeIn, FadeOut


class TransitionLibrary:
    """转场效果库"""

    @staticmethod
    def fade_in(clip, duration: float = 1.0):
        """淡入效果"""
        return clip.with_effects([FadeIn(duration)])

    @staticmethod
    def fade_out(clip, duration: float = 1.0):
        """淡出效果"""
        return clip.with_effects([FadeOut(duration)])

    @staticmethod
    def crossfade(clip1, clip2, duration: float = 1.0):
        """交叉淡化（两个片段之间）"""
        from moviepy import CompositeVideoClip

        # clip1淡出
        clip1_faded = clip1.with_effects([FadeOut(duration)])
        # clip2淡入，并设置开始时间
        clip2_faded = clip2.with_effects([FadeIn(duration)]).set_start(clip1.duration - duration)

        # 合成
        return CompositeVideoClip([clip1_faded, clip2_faded])

    @staticmethod
    def slide_in(clip, direction: str = 'left', duration: float = 1.0):
        """
        滑入效果

        Args:
            clip: 视频片段
            direction: 方向 ('left', 'right', 'top', 'bottom')
            duration: 转场时长
        """
        w, h = clip.size

        if direction == 'left':
            # 从左侧滑入
            position = lambda t: (max(-w, -w + int(w * t / duration)), 0) if t < duration else (0, 0)
        elif direction == 'right':
            # 从右侧滑入
            position = lambda t: (min(w, w - int(w * t / duration)), 0) if t < duration else (0, 0)
        elif direction == 'top':
            # 从顶部滑入
            position = lambda t: (0, max(-h, -h + int(h * t / duration))) if t < duration else (0, 0)
        else:  # bottom
            # 从底部滑入
            position = lambda t: (0, min(h, h - int(h * t / duration))) if t < duration else (0, 0)

        return clip.with_position(position)

    @staticmethod
    def zoom_in(clip, duration: float = 1.0, zoom_ratio: float = 1.5):
        """
        放大效果

        Args:
            clip: 视频片段
            duration: 转场时长
            zoom_ratio: 最大放大倍数
        """
        def scale_function(t):
            if t < duration:
                return 1 + (zoom_ratio - 1) * (t / duration)
            return zoom_ratio

        return clip.resize(scale_function)

    @staticmethod
    def zoom_out(clip, duration: float = 1.0, zoom_ratio: float = 1.5):
        """
        缩小效果

        Args:
            clip: 视频片段
            duration: 转场时长
            zoom_ratio: 初始放大倍数
        """
        def scale_function(t):
            if t < duration:
                return zoom_ratio - (zoom_ratio - 1) * (t / duration)
            return 1.0

        return clip.resize(scale_function)

    @staticmethod
    def rotate_in(clip, duration: float = 1.0, angle: float = 360):
        """
        旋转进入效果

        Args:
            clip: 视频片段
            duration: 转场时长
            angle: 旋转角度
        """
        def rotation_function(t):
            if t < duration:
                return angle * (1 - t / duration)
            return 0

        return clip.rotate(rotation_function)

    @staticmethod
    def wipe(clip1, clip2, duration: float = 1.0, direction: str = 'left'):
        """
        擦除转场（从一个片段擦除到另一个）

        Args:
            clip1: 第一个片段
            clip2: 第二个片段
            duration: 转场时长
            direction: 方向 ('left', 'right', 'top', 'bottom')
        """
        from moviepy import CompositeVideoClip

        w, h = clip1.size

        def make_frame(t):
            # 计算擦除进度
            if t < clip1.duration - duration:
                return clip1.get_frame(t)
            elif t < clip1.duration:
                progress = (t - (clip1.duration - duration)) / duration
                frame1 = clip1.get_frame(t)
                frame2 = clip2.get_frame(t - clip1.duration + duration)

                if direction == 'left':
                    split = int(w * progress)
                    frame1[:, split:] = frame2[:, split:]
                elif direction == 'right':
                    split = int(w * (1 - progress))
                    frame1[:, :split] = frame2[:, :split]
                elif direction == 'top':
                    split = int(h * progress)
                    frame1[split:, :] = frame2[split:, :]
                else:  # bottom
                    split = int(h * (1 - progress))
                    frame1[:split, :] = frame2[:split, :]

                return frame1
            else:
                return clip2.get_frame(t - clip1.duration)

        from moviepy import VideoClip
        total_duration = clip1.duration + clip2.duration - duration
        return VideoClip(make_frame=make_frame, duration=total_duration)

    @staticmethod
    def apply_transition_sequence(
        clips: List,
        transition_type: str = 'fade',
        transition_duration: float = 1.0
    ):
        """
        为一系列片段应用转场效果

        Args:
            clips: 视频片段列表
            transition_type: 转场类型 ('fade', 'slide', 'zoom', 'none')
            transition_duration: 转场时长

        Returns:
            应用转场后的片段列表
        """
        if not clips or len(clips) == 0:
            return clips

        if transition_type == 'none':
            return clips

        processed_clips = []

        for i, clip in enumerate(clips):
            if transition_type == 'fade':
                # 第一个片段淡入，最后一个片段淡出
                if i == 0:
                    clip = TransitionLibrary.fade_in(clip, transition_duration)
                if i == len(clips) - 1:
                    clip = TransitionLibrary.fade_out(clip, transition_duration)

            elif transition_type == 'slide':
                # 滑入效果
                directions = ['left', 'right', 'top', 'bottom']
                direction = directions[i % len(directions)]
                clip = TransitionLibrary.slide_in(clip, direction, transition_duration)

            elif transition_type == 'zoom':
                # 交替缩放效果
                if i % 2 == 0:
                    clip = TransitionLibrary.zoom_in(clip, transition_duration)
                else:
                    clip = TransitionLibrary.zoom_out(clip, transition_duration)

            processed_clips.append(clip)

        return processed_clips

    @staticmethod
    def get_available_transitions() -> List[str]:
        """
        获取所有可用的转场效果名称

        Returns:
            转场效果名称列表
        """
        return [
            'fade',      # 淡入淡出
            'slide',     # 滑动
            'zoom',      # 缩放
            'rotate',    # 旋转
            'wipe',      # 擦除
            'none'       # 无转场
        ]

    @staticmethod
    def get_transition_info() -> dict:
        """
        获取转场效果的详细信息

        Returns:
            转场效果信息字典
        """
        return {
            'fade': {
                'name': '淡入淡出',
                'description': '片段通过渐变透明度平滑过渡',
                'suitable_for': '通用，适合大多数场景'
            },
            'slide': {
                'name': '滑动',
                'description': '片段从边缘滑入',
                'suitable_for': '动态场景，展示空间关系'
            },
            'zoom': {
                'name': '缩放',
                'description': '片段通过放大或缩小进入',
                'suitable_for': '强调重点，吸引注意力'
            },
            'rotate': {
                'name': '旋转',
                'description': '片段旋转进入',
                'suitable_for': '创意场景，趣味性内容'
            },
            'wipe': {
                'name': '擦除',
                'description': '一个片段擦除显示另一个',
                'suitable_for': '对比场景，前后关系'
            },
            'none': {
                'name': '无转场',
                'description': '直接切换，无过渡效果',
                'suitable_for': '快节奏内容，简洁风格'
            }
        }
