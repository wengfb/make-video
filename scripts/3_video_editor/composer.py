"""
视频合成器
基于脚本自动合成完整视频
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# 修复相对导入问题 - 导入VideoEditor
sys.path.insert(0, os.path.dirname(__file__))
from editor import VideoEditor

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
        self.material_manager = MaterialManager()  # 使用默认参数
        self.recommender = MaterialRecommender(self.material_manager, config_path)

        self.video_config = self.config.get('video', {})
        self.default_image_duration = self.video_config.get('default_image_duration', 5.0)
        self.default_transition_duration = self.video_config.get('transition_duration', 1.0)

    def compose_from_script(
        self,
        script: Dict[str, Any],
        auto_select_materials: bool = True,
        output_filename: Optional[str] = None,
        tts_metadata_path: Optional[str] = None,
        subtitle_file: Optional[str] = None,
        use_tts_audio: bool = True
    ) -> str:
        """
        根据脚本自动合成视频 (V5.0 - 支持TTS和字幕)

        Args:
            script: 脚本字典（包含sections）
            auto_select_materials: 是否自动选择素材
            output_filename: 输出文件名
            tts_metadata_path: TTS音频元数据JSON文件路径 (V5.0新增)
            subtitle_file: 字幕文件路径(.srt/.ass) (V5.0新增)
            use_tts_audio: 是否使用TTS音频替代BGM (V5.0新增)

        Returns:
            视频文件路径
        """
        if not self.editor.moviepy_available:
            raise ImportError("moviepy未安装。请运行: pip install moviepy")

        from moviepy import (
            ImageClip, VideoFileClip, TextClip, CompositeVideoClip,
            concatenate_videoclips, AudioFileClip
        )
        from moviepy.video.fx import Loop
        from moviepy.audio.fx import AudioLoop

        print(f"\n🎬 开始合成视频: {script.get('title', '未命名')}")
        print("=" * 60)

        sections = script.get('sections', [])
        if not sections:
            raise ValueError("脚本没有章节内容")

        # 初始化clips列表(必须在try外部,确保finally可以访问)
        all_clips = []
        temp_clips = []  # 用于跟踪需要清理的临时clip
        audio_clips = []  # 用于跟踪音频clips

        # 遍历每个章节
        for i, section in enumerate(sections, 1):
            print(f"\n📝 处理章节 {i}/{len(sections)}: {section.get('section_name', f'章节{i}')}")

            # 获取章节信息
            narration = section.get('narration', '')
            visual_notes = section.get('visual_notes', '')
            duration = self._parse_duration(
                section.get('duration', self.default_image_duration),
                default=self.default_image_duration
            )

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
                    clip = ImageClip(material_path).with_duration(duration)
                elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    video_clip = VideoFileClip(material_path)
                    # 如果视频长度不够，循环播放
                    if video_clip.duration < duration:
                        clip = video_clip.with_effects([Loop(duration=duration)])
                    else:
                        clip = video_clip.subclipped(0, duration)
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

        # V5.0: 添加TTS语音或背景音乐
        if use_tts_audio and tts_metadata_path and os.path.exists(tts_metadata_path):
            print("🎙️  添加TTS语音...")
            try:
                # 读取TTS元数据
                with open(tts_metadata_path, 'r', encoding='utf-8') as f:
                    tts_metadata = json.load(f)

                audio_files = [item['file_path'] for item in tts_metadata.get('audio_files', [])]

                if audio_files:
                    # 合并所有TTS音频
                    tts_audio_clips = [AudioFileClip(f) for f in audio_files if os.path.exists(f)]
                    audio_clips.extend(tts_audio_clips)  # 追踪以便清理
                    if tts_audio_clips:
                        from moviepy import concatenate_audioclips
                        tts_audio = concatenate_audioclips(tts_audio_clips)

                        # 添加BGM作为背景(降低音量)
                        bgm_path = self.video_config.get('default_bgm')
                        if bgm_path and os.path.exists(bgm_path):
                            bgm = AudioFileClip(bgm_path)
                            if bgm.duration < tts_audio.duration:
                                bgm = bgm.with_effects([AudioLoop(duration=tts_audio.duration)])
                            else:
                                bgm = bgm.subclipped(0, tts_audio.duration)
                            # 降低BGM音量
                            bgm = bgm.with_volume_scaled(0.2)
                            # 混合TTS和BGM
                            from moviepy.audio.AudioClip import CompositeAudioClip
                            final_audio = CompositeAudioClip([tts_audio, bgm])
                        else:
                            final_audio = tts_audio

                        final_video = final_video.with_audio(final_audio)
                        print(f"   ✅ TTS音频已添加 (时长: {tts_audio.duration:.1f}秒)")

                        # 调整视频长度以匹配音频
                        if final_video.duration != tts_audio.duration:
                            print(f"   ⚠️  调整视频长度: {final_video.duration:.1f}秒 -> {tts_audio.duration:.1f}秒")
                            final_video = final_video.with_duration(tts_audio.duration)
            except Exception as e:
                print(f"   ⚠️  添加TTS音频失败: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            # 添加背景音乐（如果配置了）
            bgm_path = self.video_config.get('default_bgm')
            if bgm_path and os.path.exists(bgm_path):
                print("🎵 添加背景音乐...")
                try:
                    audio = AudioFileClip(bgm_path)
                    # 循环背景音乐以匹配视频长度
                    if audio.duration < final_video.duration:
                        audio = audio.with_effects([AudioLoop(duration=final_video.duration)])
                    else:
                        audio = audio.subclipped(0, final_video.duration)

                    final_video = final_video.with_audio(audio)
                except Exception as e:
                    print(f"   ⚠️  添加音乐失败: {str(e)}")

        # V5.0: 添加字幕
        if subtitle_file and os.path.exists(subtitle_file):
            print(f"📝 添加字幕: {subtitle_file}")
            try:
                from moviepy.video.tools.subtitles import SubtitlesClip

                # 创建字幕函数
                def generator(txt):
                    from moviepy import TextClip
                    return TextClip(
                        text=txt,
                        font_size=self.video_config.get('text_size', 48),
                        color='white',
                        bg_color='black',
                        method='caption',
                        size=(final_video.w - 200, None)
                    )

                # 加载字幕
                subtitles = SubtitlesClip(subtitle_file, generator)

                # 合成视频和字幕
                from moviepy import CompositeVideoClip
                final_video = CompositeVideoClip([
                    final_video,
                    subtitles.with_position(('center', 'bottom'))
                ])

                print("   ✅ 字幕已添加")
            except Exception as e:
                print(f"   ⚠️  添加字幕失败: {str(e)}")
                print(f"   提示: 确保字幕文件格式正确,且moviepy支持字幕功能")
                import traceback
                traceback.print_exc()

        # 输出文件
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            script_title = script.get('title', 'video')
            # 清理文件名
            safe_title = "".join(c for c in script_title if c.isalnum() or c in (' ', '-', '_')).strip()
            output_filename = f"{safe_title}_{timestamp}.mp4"

        output_path = os.path.join(self.editor.output_dir, output_filename)

        print(f"\n💾 导出视频...")
        try:
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

        finally:
            # 清理资源 - 防止内存泄漏
            print("\n🧹 清理临时资源...")
            try:
                # 清理视频clips
                for clip in all_clips:
                    if clip and hasattr(clip, 'close'):
                        try:
                            clip.close()
                        except:
                            pass

                # 清理音频clips
                for clip in audio_clips:
                    if clip and hasattr(clip, 'close'):
                        try:
                            clip.close()
                        except:
                            pass

                # 清理最终视频
                if 'final_video' in locals() and hasattr(final_video, 'close'):
                    try:
                        final_video.close()
                    except:
                        pass
            except Exception as e:
                print(f"   ⚠️  清理资源时出现警告: {str(e)}")

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

        from moviepy import (
            ImageClip, VideoFileClip, TextClip, CompositeVideoClip,
            concatenate_videoclips
        )

        print(f"\n🎬 开始合成视频（自定义素材）: {script.get('title', '未命名')}")

        sections = script.get('sections', [])
        all_clips = []

        for i, section in enumerate(sections):
            material_path = material_mapping.get(i)

            if material_path and os.path.exists(material_path):
                duration = self._parse_duration(
                    section.get('duration', self.default_image_duration),
                    default=self.default_image_duration
                )

                ext = os.path.splitext(material_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    clip = ImageClip(material_path).with_duration(duration)
                elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    video_clip = VideoFileClip(material_path)
                    if video_clip.duration < duration:
                        clip = video_clip.with_effects([Loop(duration=duration)])
                    else:
                        clip = video_clip.subclipped(0, duration)
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
        from moviepy import ColorClip

        # 兼容字典和列表两种resolution格式
        resolution = self.video_config.get('resolution', {'width': 1920, 'height': 1080})
        if isinstance(resolution, dict):
            size = (resolution.get('width', 1920), resolution.get('height', 1080))
        else:
            size = resolution  # 向后兼容列表格式
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
        from moviepy import TextClip

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

        # 兼容字典和列表两种resolution格式
        resolution = self.video_config.get('resolution', {'width': 1920, 'height': 1080})
        if isinstance(resolution, dict):
            width = resolution.get('width', 1920)
        else:
            width = resolution[0]  # 向后兼容列表格式

        txt_clip = TextClip(
            text=formatted_text,
            font_size=fontsize,
            color=color,
            bg_color=bg_color,
            method='caption',
            size=(width - 200, None)
        ).with_duration(duration).with_position(position)

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

        total_duration = sum(
            self._parse_duration(s.get('duration', self.default_image_duration), self.default_image_duration)
            for s in sections
        )

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
                'duration': self._parse_duration(
                    section.get('duration', self.default_image_duration),
                    self.default_image_duration
                ),
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

    def _parse_duration(self, duration_value: Any, default: float = 5.0) -> float:
        """
        解析duration值，支持字符串和数字格式

        Args:
            duration_value: duration值（可能是"15秒"、"15s"、15、15.0等）
            default: 解析失败时的默认值

        Returns:
            解析后的浮点数秒数

        Examples:
            "15秒" -> 15.0
            "110秒" -> 110.0
            "15s" -> 15.0
            15 -> 15.0
            15.0 -> 15.0
        """
        import re

        # 如果已经是数字，直接返回
        if isinstance(duration_value, (int, float)):
            return float(duration_value)

        # 如果是字符串，提取数字
        if isinstance(duration_value, str):
            # 匹配数字（整数或小数）
            match = re.search(r'(\d+\.?\d*)', duration_value)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass

        # 解析失败，返回默认值
        return default
