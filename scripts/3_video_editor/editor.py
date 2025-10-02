"""
视频剪辑器核心模块
基于moviepy的视频编辑功能
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class VideoEditor:
    """视频剪辑器（基础框架）"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化视频剪辑器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.video_config = self.config.get('video', {})
        self.output_dir = self.config['paths'].get('videos', './output/videos')

        os.makedirs(self.output_dir, exist_ok=True)

        # 检查moviepy是否可用
        self.moviepy_available = self._check_moviepy()

    def _check_moviepy(self) -> bool:
        """检查moviepy是否安装"""
        try:
            import moviepy
            return True
        except ImportError:
            return False

    def create_simple_video(
        self,
        images: List[str],
        durations: Optional[List[float]] = None,
        output_filename: Optional[str] = None,
        fps: int = 24
    ) -> str:
        """
        创建简单的图片幻灯片视频

        Args:
            images: 图片文件路径列表
            durations: 每张图片的持续时间（秒），默认每张3秒
            output_filename: 输出文件名
            fps: 帧率

        Returns:
            输出文件路径
        """
        if not self.moviepy_available:
            raise ImportError("moviepy未安装。请运行: pip install moviepy")

        from moviepy import ImageClip, concatenate_videoclips

        # 默认持续时间
        if durations is None:
            durations = [3.0] * len(images)

        # 创建图片剪辑
        clips = []
        for img_path, duration in zip(images, durations):
            if os.path.exists(img_path):
                clip = ImageClip(img_path).with_duration(duration)
                clips.append(clip)
            else:
                print(f"⚠️  图片不存在，跳过: {img_path}")

        if not clips:
            raise ValueError("没有有效的图片文件")

        # 合成视频
        final_clip = concatenate_videoclips(clips, method="compose")

        # 输出文件名
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_{timestamp}.mp4"

        output_path = os.path.join(self.output_dir, output_filename)

        # 写入文件
        final_clip.write_videofile(
            output_path,
            fps=fps,
            codec=self.video_config.get('codec', 'libx264')
        )

        print(f"\n✅ 视频已生成: {output_path}")
        return output_path

    def add_audio_to_video(
        self,
        video_path: str,
        audio_path: str,
        output_filename: Optional[str] = None
    ) -> str:
        """
        为视频添加音频

        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_filename: 输出文件名

        Returns:
            输出文件路径
        """
        if not self.moviepy_available:
            raise ImportError("moviepy未安装")

        from moviepy import VideoFileClip, AudioFileClip

        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        # 设置音频
        final_video = video.with_audio(audio)

        # 输出文件名
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_with_audio_{timestamp}.mp4"

        output_path = os.path.join(self.output_dir, output_filename)

        # 写入文件
        final_video.write_videofile(output_path)

        print(f"\n✅ 已添加音频: {output_path}")
        return output_path

    def add_text_overlay(
        self,
        video_path: str,
        text: str,
        position: Tuple[int, int] = (50, 50),
        fontsize: int = 40,
        color: str = 'white',
        duration: Optional[float] = None,
        output_filename: Optional[str] = None
    ) -> str:
        """
        在视频上添加文字

        Args:
            video_path: 视频文件路径
            text: 文字内容
            position: 位置 (x, y)
            fontsize: 字体大小
            color: 颜色
            duration: 文字显示时长（秒），None表示全程
            output_filename: 输出文件名

        Returns:
            输出文件路径
        """
        if not self.moviepy_available:
            raise ImportError("moviepy未安装")

        from moviepy import VideoFileClip, TextClip, CompositeVideoClip

        video = VideoFileClip(video_path)

        # 创建文字剪辑
        txt_clip = TextClip(
            text=text,
            font_size=fontsize,
            color=color
        ).with_position(position).with_duration(duration or video.duration)

        # 合成
        final_video = CompositeVideoClip([video, txt_clip])

        # 输出文件名
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_with_text_{timestamp}.mp4"

        output_path = os.path.join(self.output_dir, output_filename)

        # 写入文件
        final_video.write_videofile(output_path)

        print(f"\n✅ 已添加文字: {output_path}")
        return output_path

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息字典
        """
        if not self.moviepy_available:
            raise ImportError("moviepy未安装")

        from moviepy import VideoFileClip

        video = VideoFileClip(video_path)

        info = {
            'duration': video.duration,
            'fps': video.fps,
            'size': video.size,
            'width': video.w,
            'height': video.h,
            'has_audio': video.audio is not None
        }

        video.close()

        return info

    def trim_video(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_filename: Optional[str] = None
    ) -> str:
        """
        裁剪视频

        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_filename: 输出文件名

        Returns:
            输出文件路径
        """
        if not self.moviepy_available:
            raise ImportError("moviepy未安装")

        from moviepy import VideoFileClip

        video = VideoFileClip(video_path).subclipped(start_time, end_time)

        # 输出文件名
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_trimmed_{timestamp}.mp4"

        output_path = os.path.join(self.output_dir, output_filename)

        # 写入文件
        video.write_videofile(output_path)

        print(f"\n✅ 视频已裁剪: {output_path}")
        return output_path

    def concatenate_videos(
        self,
        video_paths: List[str],
        output_filename: Optional[str] = None
    ) -> str:
        """
        拼接多个视频

        Args:
            video_paths: 视频文件路径列表
            output_filename: 输出文件名

        Returns:
            输出文件路径
        """
        if not self.moviepy_available:
            raise ImportError("moviepy未安装")

        from moviepy import VideoFileClip, concatenate_videoclips

        clips = [VideoFileClip(path) for path in video_paths if os.path.exists(path)]

        if not clips:
            raise ValueError("没有有效的视频文件")

        final_clip = concatenate_videoclips(clips)

        # 输出文件名
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_concatenated_{timestamp}.mp4"

        output_path = os.path.join(self.output_dir, output_filename)

        # 写入文件
        final_clip.write_videofile(output_path)

        print(f"\n✅ 视频已拼接: {output_path}")
        return output_path
