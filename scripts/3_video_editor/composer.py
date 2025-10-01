"""
视频合成器
基于脚本自动合成完整视频
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# 导入VideoEditor
from .editor import VideoEditor

# 导入素材推荐器
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '2_material_manager'))
from recommender import MaterialRecommender
from manager import MaterialManager


class VideoComposer:
    """视频合成器（基于脚本自动生成视频）"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化视频合成器

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.editor = VideoEditor(config_path)
        self.material_manager = MaterialManager(config_path)
        self.recommender = MaterialRecommender(self.material_manager, config_path)

        self.video_config = self.config.get('video', {})
        self.default_image_duration = self.video_config.get('default_image_duration', 5.0)
        self.default_transition_duration = self.video_config.get('transition_duration', 1.0)

    def compose_from_script(
        self,
        script: Dict[str, Any],
        auto_select_materials: bool = True,
        output_filename: Optional[str] = None
    ) -> str:
        """
        根据脚本自动合成视频

        Args:
            script: 脚本字典（包含sections）
            auto_select_materials: 是否自动选择素材
            output_filename: 输出文件名

        Returns:
            视频文件路径
        """
        if not self.editor.moviepy_available:
            raise ImportError("moviepy未安装。请运行: pip install moviepy")

        from moviepy.editor import (
            ImageClip, VideoFileClip, TextClip, CompositeVideoClip,
            concatenate_videoclips, AudioFileClip
        )

        print(f"\n🎬 开始合成视频: {script.get('title', '未命名')}")
        print("=" * 60)

        sections = script.get('sections', [])
        if not sections:
            raise ValueError("脚本没有章节内容")

        all_clips = []

        # 遍历每个章节
        for i, section in enumerate(sections, 1):
            print(f"\n📝 处理章节 {i}/{len(sections)}: {section.get('section_name', f'章节{i}')}")

            # 获取章节信息
            narration = section.get('narration', '')
            visual_notes = section.get('visual_notes', '')
            duration = section.get('duration', self.default_image_duration)

            # 推荐素材
            if auto_select_materials:
                print("   🔍 智能推荐素材...")
                recommendations = self.recommender.recommend_for_script_section(
                    section,
                    limit=3
                )

                if recommendations:
                    best_material = recommendations[0]
                    material_path = best_material['file_path']
                    print(f"   ✅ 选择素材: {best_material['name']} (匹配度: {best_material['match_score']:.0f}%)")
                else:
                    print("   ⚠️  未找到合适素材，使用默认黑屏")
                    material_path = None
            else:
                material_path = None

            # 创建视频片段
            if material_path and os.path.exists(material_path):
                # 根据素材类型创建剪辑
                ext = os.path.splitext(material_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    clip = ImageClip(material_path).set_duration(duration)
                elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    video_clip = VideoFileClip(material_path)
                    # 如果视频长度不够，循环播放
                    if video_clip.duration < duration:
                        clip = video_clip.loop(duration=duration)
                    else:
                        clip = video_clip.subclip(0, duration)
                else:
                    print(f"   ⚠️  不支持的素材格式: {ext}")
                    clip = self._create_color_clip((0, 0, 0), duration)
            else:
                # 创建黑屏
                clip = self._create_color_clip((0, 0, 0), duration)

            # 添加文字（如果需要）
            if self.video_config.get('show_narration_text', True) and narration:
                text_clip = self._create_text_clip(
                    narration,
                    duration=duration,
                    position=('center', 'bottom'),
                    fontsize=self.video_config.get('text_size', 40)
                )
                clip = CompositeVideoClip([clip, text_clip])

            all_clips.append(clip)

        if not all_clips:
            raise ValueError("没有生成任何视频片段")

        # 合并所有片段
        print(f"\n🎞️  合并 {len(all_clips)} 个片段...")
        final_video = concatenate_videoclips(all_clips, method="compose")

        # 添加背景音乐（如果配置了）
        bgm_path = self.video_config.get('default_bgm')
        if bgm_path and os.path.exists(bgm_path):
            print("🎵 添加背景音乐...")
            try:
                audio = AudioFileClip(bgm_path)
                # 循环背景音乐以匹配视频长度
                if audio.duration < final_video.duration:
                    audio = audio.loop(duration=final_video.duration)
                else:
                    audio = audio.subclip(0, final_video.duration)

                final_video = final_video.set_audio(audio)
            except Exception as e:
                print(f"   ⚠️  添加音乐失败: {str(e)}")

        # 输出文件
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            script_title = script.get('title', 'video')
            # 清理文件名
            safe_title = "".join(c for c in script_title if c.isalnum() or c in (' ', '-', '_')).strip()
            output_filename = f"{safe_title}_{timestamp}.mp4"

        output_path = os.path.join(self.editor.output_dir, output_filename)

        print(f"\n💾 导出视频...")
        final_video.write_videofile(
            output_path,
            fps=self.video_config.get('fps', 24),
            codec=self.video_config.get('codec', 'libx264'),
            audio_codec=self.video_config.get('audio_codec', 'aac')
        )

        print(f"\n✅ 视频合成完成: {output_path}")
        print(f"   时长: {final_video.duration:.1f}秒")
        print(f"   片段数: {len(all_clips)}")

        return output_path

    def compose_with_custom_materials(
        self,
        script: Dict[str, Any],
        material_mapping: Dict[int, str],
        output_filename: Optional[str] = None
    ) -> str:
        """
        使用自定义素材映射合成视频

        Args:
            script: 脚本字典
            material_mapping: 章节索引 -> 素材路径的映射
            output_filename: 输出文件名

        Returns:
            视频文件路径
        """
        if not self.editor.moviepy_available:
            raise ImportError("moviepy未安装")

        from moviepy.editor import (
            ImageClip, VideoFileClip, TextClip, CompositeVideoClip,
            concatenate_videoclips
        )

        print(f"\n🎬 开始合成视频（自定义素材）: {script.get('title', '未命名')}")

        sections = script.get('sections', [])
        all_clips = []

        for i, section in enumerate(sections):
            material_path = material_mapping.get(i)

            if material_path and os.path.exists(material_path):
                duration = section.get('duration', self.default_image_duration)

                ext = os.path.splitext(material_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    clip = ImageClip(material_path).set_duration(duration)
                elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    video_clip = VideoFileClip(material_path)
                    if video_clip.duration < duration:
                        clip = video_clip.loop(duration=duration)
                    else:
                        clip = video_clip.subclip(0, duration)
                else:
                    continue

                # 添加文字
                narration = section.get('narration', '')
                if narration and self.video_config.get('show_narration_text', True):
                    text_clip = self._create_text_clip(
                        narration,
                        duration=duration,
                        position=('center', 'bottom')
                    )
                    clip = CompositeVideoClip([clip, text_clip])

                all_clips.append(clip)

        if not all_clips:
            raise ValueError("没有有效的视频片段")

        final_video = concatenate_videoclips(all_clips, method="compose")

        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_custom_{timestamp}.mp4"

        output_path = os.path.join(self.editor.output_dir, output_filename)
        final_video.write_videofile(output_path, fps=24)

        print(f"\n✅ 视频合成完成: {output_path}")
        return output_path

    def preview_material_recommendations(self, script: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        预览脚本各章节的素材推荐

        Args:
            script: 脚本字典

        Returns:
            推荐列表（每个章节的推荐素材）
        """
        sections = script.get('sections', [])
        all_recommendations = []

        print(f"\n🔍 素材推荐预览: {script.get('title', '未命名')}")
        print("=" * 60)

        for i, section in enumerate(sections, 1):
            section_name = section.get('section_name', f'章节{i}')
            print(f"\n{i}. {section_name}")

            recommendations = self.recommender.recommend_for_script_section(
                section,
                limit=5
            )

            if recommendations:
                for j, rec in enumerate(recommendations, 1):
                    print(f"   {j}) {rec['name']} (匹配度: {rec['match_score']:.0f}%)")
                    print(f"      类型: {rec['type']} | 标签: {', '.join(rec.get('tags', []))}")
                    print(f"      原因: {rec.get('match_reason', 'N/A')}")
            else:
                print("   ⚠️  未找到合适素材")

            all_recommendations.append({
                'section_index': i - 1,
                'section_name': section_name,
                'recommendations': recommendations
            })

        return all_recommendations

    def _create_color_clip(self, color: Tuple[int, int, int], duration: float):
        """创建纯色剪辑"""
        from moviepy.editor import ColorClip

        size = self.video_config.get('resolution', [1920, 1080])
        return ColorClip(size=size, color=color, duration=duration)

    def _create_text_clip(
        self,
        text: str,
        duration: float,
        position: Tuple = ('center', 'bottom'),
        fontsize: int = 40,
        color: str = 'white',
        bg_color: str = 'black'
    ):
        """创建文字剪辑"""
        from moviepy.editor import TextClip

        # 文字换行处理
        max_chars_per_line = 30
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line + word) <= max_chars_per_line:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        formatted_text = "\n".join(lines[:3])  # 最多3行

        txt_clip = TextClip(
            formatted_text,
            fontsize=fontsize,
            color=color,
            bg_color=bg_color,
            method='caption',
            size=(self.video_config.get('resolution', [1920, 1080])[0] - 200, None)
        ).set_duration(duration).set_position(position)

        return txt_clip

    def get_composition_info(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取合成信息（不实际合成）

        Args:
            script: 脚本字典

        Returns:
            合成信息字典
        """
        sections = script.get('sections', [])

        total_duration = sum(s.get('duration', self.default_image_duration) for s in sections)

        info = {
            'title': script.get('title', '未命名'),
            'total_sections': len(sections),
            'estimated_duration': total_duration,
            'estimated_file_size_mb': self._estimate_file_size(total_duration),
            'sections': []
        }

        for i, section in enumerate(sections, 1):
            section_info = {
                'index': i,
                'name': section.get('section_name', f'章节{i}'),
                'duration': section.get('duration', self.default_image_duration),
                'has_narration': bool(section.get('narration')),
                'has_visual_notes': bool(section.get('visual_notes'))
            }
            info['sections'].append(section_info)

        return info

    def _estimate_file_size(self, duration: float) -> float:
        """估算文件大小（MB）"""
        # 粗略估算：1080p 24fps 约 5MB/分钟
        bitrate_mb_per_min = self.video_config.get('estimated_bitrate_mb_per_min', 5.0)
        return round((duration / 60.0) * bitrate_mb_per_min, 2)
