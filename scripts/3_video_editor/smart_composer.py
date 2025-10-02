"""
智能视频合成器（AI驱动）
整合语义分析、转场决策和Ken Burns效果的智能合成系统
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# 导入基础合成器
sys.path.insert(0, os.path.dirname(__file__))
from composer import VideoComposer

# 导入智能组件
from semantic_analyzer import SemanticAnalyzer
from transition_engine import TransitionDecisionEngine
from ken_burns import KenBurnsGenerator
from transitions import TransitionLibrary

# 导入AI客户端
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '1_script_generator'))
from ai_client import AIClient


class SmartVideoComposer(VideoComposer):
    """智能视频合成器（增强版）"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化智能合成器

        Args:
            config_path: 配置文件路径
        """
        super().__init__(config_path)

        # 加载智能动效配置
        self.smart_config = self.config.get('smart_effects', {})
        self.smart_enabled = self.smart_config.get('enable', True)
        self.use_ai_analysis = self.smart_config.get('use_ai_analysis', False)
        self.ken_burns_enabled = self.smart_config.get('ken_burns_enabled', True)

        # 初始化AI客户端（如果启用）
        ai_client = None
        if self.use_ai_analysis:
            try:
                ai_client = AIClient(self.config['ai'])
            except Exception as e:
                print(f"   ⚠️  AI客户端初始化失败: {str(e)}")
                print(f"   → 降级到规则引擎模式")
                self.use_ai_analysis = False

        # 初始化智能组件
        self.semantic_analyzer = SemanticAnalyzer(
            ai_client=ai_client,
            use_ai=self.use_ai_analysis
        )
        self.transition_engine = TransitionDecisionEngine()
        self.ken_burns = KenBurnsGenerator()

        print(f"\n🧠 智能动效系统: "
              f"{'已启用' if self.smart_enabled else '已禁用'}")
        if self.smart_enabled:
            print(f"   AI分析: {'已启用' if self.use_ai_analysis else '规则引擎'}")
            print(f"   Ken Burns: {'已启用' if self.ken_burns_enabled else '已禁用'}")

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
        智能合成视频（覆盖父类方法）

        根据配置自动选择：
        - smart_enabled=True: 使用智能系统
        - smart_enabled=False: 使用原始方法

        Args:
            script: 脚本字典
            auto_select_materials: 是否自动选择素材
            output_filename: 输出文件名
            tts_metadata_path: TTS元数据路径
            subtitle_file: 字幕文件路径
            use_tts_audio: 是否使用TTS音频

        Returns:
            视频文件路径
        """
        if not self.smart_enabled:
            # 降级到原始方法
            return super().compose_from_script(
                script,
                auto_select_materials,
                output_filename,
                tts_metadata_path,
                subtitle_file,
                use_tts_audio
            )

        # 使用智能合成
        return self._smart_compose(
            script,
            auto_select_materials,
            output_filename,
            tts_metadata_path,
            subtitle_file,
            use_tts_audio
        )

    def _smart_compose(
        self,
        script: Dict[str, Any],
        auto_select_materials: bool,
        output_filename: Optional[str],
        tts_metadata_path: Optional[str],
        subtitle_file: Optional[str],
        use_tts_audio: bool
    ) -> str:
        """智能合成核心逻辑"""

        if not self.editor.moviepy_available:
            raise ImportError("moviepy未安装。请运行: pip install moviepy")

        from moviepy.editor import (
            ImageClip, VideoFileClip, TextClip, CompositeVideoClip,
            concatenate_videoclips, AudioFileClip
        )

        print(f"\n🎬 智能视频合成: {script.get('title', '未命名')}")
        print("=" * 70)

        sections = script.get('sections', [])
        if not sections:
            raise ValueError("脚本没有章节内容")

        # ========== 第1步: AI语义分析 ==========
        print(f"\n🧠 AI语义分析中...")
        analyses = self.semantic_analyzer.analyze_all_sections(sections)

        # 打印分析结果摘要
        print(f"\n📊 分析结果摘要:")
        for i, (section, analysis) in enumerate(zip(sections, analyses), 1):
            print(f"   {i}. {section.get('section_name', 'N/A')}: "
                  f"能量{analysis['energy_level']:.1f}, "
                  f"情绪{analysis['emotion']}")

        # ========== 第2步: 生成带动效的clips ==========
        all_clips = []
        temp_clips = []
        audio_clips = []

        print(f"\n🎨 生成视频片段...")

        for i, (section, analysis) in enumerate(zip(sections, analyses), 1):
            section_name = section.get('section_name', f'章节{i}')
            print(f"\n📝 处理章节 {i}/{len(sections)}: {section_name}")

            # 2.1 获取素材
            material_path = self._get_material_for_section(
                section,
                auto_select_materials
            )

            duration = section.get('duration', self.default_image_duration)

            # 2.2 创建基础clip
            clip = self._create_base_clip(material_path, duration)

            # 2.3 应用Ken Burns效果（如果是静态图片）
            if self.ken_burns_enabled and material_path:
                ext = os.path.splitext(material_path)[1].lower()
                if ext in ['.jpg', '.png', '.jpeg', '.gif']:
                    movement_type = self.ken_burns._decide_movement_type(
                        analysis['energy_level'],
                        analysis['emotion']
                    )
                    clip = self.ken_burns.apply_ken_burns(clip, analysis, duration)
                    print(f"   ✨ Ken Burns: {movement_type}")

            # 2.4 决定转场（除第一个clip）
            if i > 0:
                transition = self.transition_engine.decide_transition(
                    analyses[i-1],
                    analysis,
                    analyses[i+1] if i < len(analyses)-1 else None
                )

                print(f"   🎬 转场: {transition['type']} "
                      f"({transition['duration']}s)")
                print(f"      理由: {transition['reason']}")

                # 应用转场
                clip = self._apply_transition(clip, transition)

            # 2.5 添加文字（如果配置启用）
            narration = section.get('narration', '')
            if self.video_config.get('show_narration_text', False) and narration:
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

        # ========== 第3步: 合并clips ==========
        print(f"\n🎞️  合并 {len(all_clips)} 个片段...")
        final_video = concatenate_videoclips(all_clips, method="compose")

        # ========== 第4步: 添加音频 ==========
        final_video = self._add_audio(
            final_video,
            use_tts_audio,
            tts_metadata_path,
            audio_clips
        )

        # ========== 第5步: 添加字幕 ==========
        if subtitle_file and os.path.exists(subtitle_file):
            final_video = self._add_subtitles(final_video, subtitle_file)

        # ========== 第6步: 导出视频 ==========
        output_path = self._export_video(
            final_video,
            script,
            output_filename,
            len(all_clips)
        )

        # ========== 第7步: 清理资源 ==========
        self._cleanup_resources(all_clips, audio_clips, final_video)

        return output_path

    def _get_material_for_section(
        self,
        section: Dict[str, Any],
        auto_select: bool
    ) -> Optional[str]:
        """获取章节素材"""
        if auto_select:
            print("   🔍 智能推荐素材...")
            recommendations = self.recommender.recommend_for_script_section(
                section,
                limit=3
            )

            if recommendations:
                best_material = recommendations[0]
                material_path = best_material['file_path']
                print(f"   ✅ 选择: {best_material['name']} "
                      f"(匹配度: {best_material.get('match_score', 0):.0f}%)")
                return material_path
            else:
                print("   ⚠️  未找到合适素材，使用默认黑屏")
                return None
        else:
            return None

    def _create_base_clip(self, material_path: Optional[str], duration: float):
        """创建基础clip"""
        from moviepy.editor import ImageClip, VideoFileClip

        if material_path and os.path.exists(material_path):
            ext = os.path.splitext(material_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return ImageClip(material_path).set_duration(duration)
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                video_clip = VideoFileClip(material_path)
                if video_clip.duration < duration:
                    return video_clip.loop(duration=duration)
                else:
                    return video_clip.subclip(0, duration)
            else:
                print(f"   ⚠️  不支持的格式: {ext}")
                return self._create_color_clip((0, 0, 0), duration)
        else:
            return self._create_color_clip((0, 0, 0), duration)

    def _apply_transition(self, clip, transition: Dict[str, Any]):
        """应用转场效果到clip"""
        trans_type = transition['type']
        duration = transition['duration']
        params = transition.get('params', {})

        if trans_type == 'fade':
            return clip.fadein(duration)
        elif trans_type == 'zoom_in':
            zoom_ratio = params.get('zoom_ratio', 1.3)
            return TransitionLibrary.zoom_in(clip, duration, zoom_ratio)
        elif trans_type == 'zoom_out':
            zoom_ratio = params.get('zoom_ratio', 1.3)
            return TransitionLibrary.zoom_out(clip, duration, zoom_ratio)
        elif trans_type == 'slide_left':
            return TransitionLibrary.slide_in(clip, 'left', duration)
        elif trans_type == 'slide_right':
            return TransitionLibrary.slide_in(clip, 'right', duration)
        elif trans_type == 'hard_cut':
            return clip  # 无转场
        elif trans_type == 'crossfade':
            return clip.crossfadein(duration)
        else:
            return clip

    def _add_audio(
        self,
        video_clip,
        use_tts: bool,
        tts_metadata_path: Optional[str],
        audio_clips: list
    ):
        """添加音频（TTS或BGM）"""
        from moviepy.editor import AudioFileClip, concatenate_audioclips
        from moviepy.audio.AudioClip import CompositeAudioClip

        if use_tts and tts_metadata_path and os.path.exists(tts_metadata_path):
            print("\n🎙️  添加TTS语音...")
            try:
                with open(tts_metadata_path, 'r', encoding='utf-8') as f:
                    tts_metadata = json.load(f)

                audio_files = [item['file_path']
                              for item in tts_metadata.get('audio_files', [])]

                if audio_files:
                    tts_audio_clips = [AudioFileClip(f)
                                      for f in audio_files if os.path.exists(f)]
                    audio_clips.extend(tts_audio_clips)

                    if tts_audio_clips:
                        tts_audio = concatenate_audioclips(tts_audio_clips)

                        # 添加BGM背景
                        bgm_path = self.video_config.get('default_bgm')
                        if bgm_path and os.path.exists(bgm_path):
                            bgm = AudioFileClip(bgm_path)
                            if bgm.duration < tts_audio.duration:
                                bgm = bgm.loop(duration=tts_audio.duration)
                            else:
                                bgm = bgm.subclip(0, tts_audio.duration)
                            bgm = bgm.volumex(0.2)
                            final_audio = CompositeAudioClip([tts_audio, bgm])
                        else:
                            final_audio = tts_audio

                        video_clip = video_clip.set_audio(final_audio)
                        print(f"   ✅ TTS音频已添加 (时长: {tts_audio.duration:.1f}秒)")

                        if video_clip.duration != tts_audio.duration:
                            video_clip = video_clip.set_duration(tts_audio.duration)
            except Exception as e:
                print(f"   ⚠️  添加TTS失败: {str(e)}")
        else:
            # 添加BGM
            bgm_path = self.video_config.get('default_bgm')
            if bgm_path and os.path.exists(bgm_path):
                print("\n🎵 添加背景音乐...")
                try:
                    audio = AudioFileClip(bgm_path)
                    if audio.duration < video_clip.duration:
                        audio = audio.loop(duration=video_clip.duration)
                    else:
                        audio = audio.subclip(0, video_clip.duration)
                    video_clip = video_clip.set_audio(audio)
                except Exception as e:
                    print(f"   ⚠️  添加BGM失败: {str(e)}")

        return video_clip

    def _add_subtitles(self, video_clip, subtitle_file: str):
        """添加字幕"""
        print(f"\n📝 添加字幕: {subtitle_file}")
        try:
            from moviepy.video.tools.subtitles import SubtitlesClip
            from moviepy.editor import TextClip, CompositeVideoClip

            def generator(txt):
                return TextClip(
                    txt,
                    fontsize=self.video_config.get('text_size', 48),
                    color='white',
                    bg_color='black',
                    method='caption',
                    size=(video_clip.w - 200, None)
                )

            subtitles = SubtitlesClip(subtitle_file, generator)
            video_clip = CompositeVideoClip([
                video_clip,
                subtitles.set_position(('center', 'bottom'))
            ])

            print("   ✅ 字幕已添加")
        except Exception as e:
            print(f"   ⚠️  添加字幕失败: {str(e)}")

        return video_clip

    def _export_video(
        self,
        video_clip,
        script: Dict[str, Any],
        output_filename: Optional[str],
        clip_count: int
    ) -> str:
        """导出视频"""
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            script_title = script.get('title', 'video')
            safe_title = "".join(c for c in script_title
                                if c.isalnum() or c in (' ', '-', '_')).strip()
            output_filename = f"{safe_title}_{timestamp}.mp4"

        output_path = os.path.join(self.editor.output_dir, output_filename)

        print(f"\n💾 导出视频...")
        video_clip.write_videofile(
            output_path,
            fps=self.video_config.get('fps', 24),
            codec=self.video_config.get('codec', 'libx264'),
            audio_codec=self.video_config.get('audio_codec', 'aac')
        )

        print(f"\n✅ 智能视频合成完成!")
        print(f"   输出: {output_path}")
        print(f"   时长: {video_clip.duration:.1f}秒")
        print(f"   片段数: {clip_count}")

        return output_path

    def _cleanup_resources(self, all_clips: list, audio_clips: list, final_video):
        """清理资源防止内存泄漏"""
        print("\n🧹 清理临时资源...")
        try:
            for clip in all_clips:
                if clip and hasattr(clip, 'close'):
                    try:
                        clip.close()
                    except:
                        pass

            for clip in audio_clips:
                if clip and hasattr(clip, 'close'):
                    try:
                        clip.close()
                    except:
                        pass

            if hasattr(final_video, 'close'):
                try:
                    final_video.close()
                except:
                    pass
        except Exception as e:
            print(f"   ⚠️  清理时出错: {str(e)}")
