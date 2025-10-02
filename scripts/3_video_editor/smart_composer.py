"""
智能视频合成器（AI驱动）
整合语义分析、转场决策和Ken Burns效果的智能合成系统
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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

        from moviepy import (
            ImageClip, VideoFileClip, TextClip, CompositeVideoClip,
            concatenate_videoclips, AudioFileClip
        )
        from moviepy.video.fx import Loop, FadeIn, CrossFadeIn
        from moviepy.audio.fx import AudioLoop

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

        # ========== 第2步: 🚀 并行生成带动效的clips ==========
        all_clips = []
        temp_clips = []
        audio_clips = []

        print(f"\n🎨 🚀 并行生成视频片段...")

        # 预先获取所有素材路径（如果需要自动选择）
        section_materials = {}
        if auto_select_materials:
            print("🔍 批量推荐素材...")
            with ThreadPoolExecutor(max_workers=min(8, len(sections))) as executor:
                future_to_idx = {
                    executor.submit(self._get_material_for_section, section, True): i
                    for i, section in enumerate(sections)
                }
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        section_materials[idx] = future.result()
                    except Exception as e:
                        print(f"   ⚠️  章节 {idx + 1} 素材推荐失败: {str(e)}")
                        section_materials[idx] = None

        # 并行创建视频片段（保留顺序）
        clips_dict = {}
        lock = threading.Lock()

        def create_smart_clip(i, section, analysis):
            """智能创建单个视频片段"""
            section_name = section.get('section_name', f'章节{i+1}')

            # 2.1 获取素材
            if auto_select_materials:
                material_path = section_materials.get(i)
            else:
                material_path = None

            duration = self._parse_duration(
                section.get('duration', self.default_image_duration),
                default=self.default_image_duration
            )

            # 2.2 创建基础clip
            clip = self._create_base_clip(material_path, duration)

            # 2.3 应用Ken Burns效果（如果是静态图片）
            kb_info = ""
            if self.ken_burns_enabled and material_path:
                ext = os.path.splitext(material_path)[1].lower()
                if ext in ['.jpg', '.png', '.jpeg', '.gif']:
                    movement_type = self.ken_burns._decide_movement_type(
                        analysis['energy_level'],
                        analysis['emotion']
                    )
                    clip = self.ken_burns.apply_ken_burns(clip, analysis, duration)
                    kb_info = f" | KB: {movement_type}"

            # 2.4 决定转场（除第一个clip）
            trans_info = ""
            if i > 0:
                transition = self.transition_engine.decide_transition(
                    analyses[i-1],
                    analysis,
                    analyses[i+1] if i < len(analyses)-1 else None
                )
                trans_info = f" | 转场: {transition['type']}"
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

            with lock:
                clips_dict[i] = clip
                print(f"   ✅ 章节 {i+1}/{len(sections)}: {section_name}{kb_info}{trans_info}")

            return clip

        # 并行处理所有章节（由于转场需要前后信息，降低并行度）
        with ThreadPoolExecutor(max_workers=min(3, len(sections))) as executor:
            futures = [
                executor.submit(create_smart_clip, i, section, analyses[i])
                for i, section in enumerate(sections)
            ]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"   ⚠️  创建片段失败: {str(e)}")

        # 按顺序组装clips
        all_clips = [clips_dict[i] for i in sorted(clips_dict.keys())]

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
        from moviepy import ImageClip, VideoFileClip
        from moviepy.video.fx import Loop

        if material_path and os.path.exists(material_path):
            ext = os.path.splitext(material_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                clip = ImageClip(material_path).with_duration(duration)
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                video_clip = VideoFileClip(material_path)

                # 移除音频（因为我们会使用TTS音频）
                video_clip = video_clip.without_audio()

                if video_clip.duration < duration:
                    clip = video_clip.with_effects([Loop(duration=duration)])
                else:
                    clip = video_clip.subclipped(0, duration)
            else:
                print(f"   ⚠️  不支持的格式: {ext}")
                clip = self._create_color_clip((0, 0, 0), duration)
        else:
            clip = self._create_color_clip((0, 0, 0), duration)

        return self._ensure_target_resolution(clip)

    def _apply_transition(self, clip, transition: Dict[str, Any]):
        """应用转场效果到clip"""
        trans_type = transition['type']
        duration = transition['duration']
        params = transition.get('params', {})

        if trans_type == 'fade':
            return clip.with_effects([FadeIn(duration)])
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
            return clip.with_effects([CrossFadeIn(duration)])
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
        from moviepy import AudioFileClip, concatenate_audioclips, CompositeAudioClip

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
                                bgm = bgm.with_effects([AudioLoop(duration=tts_audio.duration)])
                            else:
                                bgm = bgm.subclipped(0, tts_audio.duration)
                            bgm = bgm.with_volume_scaled(0.2)
                            final_audio = CompositeAudioClip([tts_audio, bgm])
                        else:
                            final_audio = tts_audio

                        video_clip = video_clip.with_audio(final_audio)
                        print(f"   ✅ TTS音频已添加 (时长: {tts_audio.duration:.1f}秒)")

                        if video_clip.duration != tts_audio.duration:
                            video_clip = video_clip.with_duration(tts_audio.duration)
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
                        audio = audio.with_effects([AudioLoop(duration=video_clip.duration)])
                    else:
                        audio = audio.subclipped(0, video_clip.duration)
                    video_clip = video_clip.with_audio(audio)
                except Exception as e:
                    print(f"   ⚠️  添加BGM失败: {str(e)}")

        return video_clip

    def _add_subtitles(self, video_clip, subtitle_file: str):
        """添加字幕"""
        print(f"\n📝 添加字幕: {subtitle_file}")
        try:
            from moviepy.video.tools.subtitles import SubtitlesClip
            from moviepy import TextClip, CompositeVideoClip

            def generator(txt):
                return TextClip(
                    text=txt,
                    font_size=self.video_config.get('text_size', 48),
                    color='white',
                    bg_color='black',
                    method='caption',
                    size=(video_clip.w - 200, None)
                )

            subtitles = SubtitlesClip(subtitle_file, generator)
            video_clip = CompositeVideoClip([
                video_clip,
                subtitles.with_position(('center', 'bottom'))
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

        # 构建FFmpeg参数（支持GPU加速）
        codec = self.video_config.get('codec', 'libx264')
        ffmpeg_params = []

        if self.video_config.get('gpu_acceleration', False) and 'nvenc' in codec:
            # NVIDIA GPU加速参数（NVENC编码器选项）
            preset = self.video_config.get('gpu_preset', 'p4')
            ffmpeg_params = ['-preset', str(preset)]

            custom_nvenc = self.video_config.get('nvenc_params')
            if isinstance(custom_nvenc, list):
                ffmpeg_params.extend(str(p) for p in custom_nvenc)

            print(f"   🚀 启用GPU加速: {codec} (preset: {preset})")

        # 构建write_videofile参数
        write_params = {
            'fps': self.video_config.get('fps', 24),
            'codec': codec,
            'audio_codec': self.video_config.get('audio_codec', 'aac'),
            'threads': self.video_config.get('threads', 4)
        }

        # 添加FFmpeg参数（如果有）
        if ffmpeg_params:
            write_params['ffmpeg_params'] = ffmpeg_params

        # 如果不是GPU编码，添加preset
        if 'nvenc' not in codec:
            write_params['preset'] = self.video_config.get('preset', 'medium')

        # 执行导出，失败时自动回退到CPU编码
        try:
            try:
                from moviepy.video.io import ffmpeg_writer
                print(f"   🧪 FFmpeg二进制: {ffmpeg_writer.FFMPEG_BINARY}")
                print(f"   🧵 FFmpeg线程数: {write_params.get('threads')}")
            except Exception:
                pass

            video_clip.write_videofile(output_path, **write_params)
        except Exception as e:
            if 'nvenc' in codec.lower():
                print("\n⚠️  NVENC导出失败，尝试回退到CPU编码(libx264)...")
                print(f"   ❌ NVENC失败详情: {e}")
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception:
                    pass

                try:
                    write_params.pop('ffmpeg_params', None)
                    write_params['codec'] = 'libx264'
                    write_params['preset'] = self.video_config.get('preset', 'medium')
                    video_clip.write_videofile(output_path, **write_params)
                except Exception:
                    raise e
            else:
                raise

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

    def _ensure_target_resolution(self, clip):
        """确保剪辑符合目标分辨率（Letterbox 适配）。"""
        try:
            resolution = self.video_config.get('resolution', {'width': 1920, 'height': 1080})
            if isinstance(resolution, dict):
                target_width = int(resolution.get('width', 1920))
                target_height = int(resolution.get('height', 1080))
            else:
                target_width, target_height = resolution

            if not target_width or not target_height:
                return clip

            clip_width, clip_height = clip.size
            if clip_width is None or clip_height is None:
                return clip

            target_width = max(2, (target_width // 2) * 2)
            target_height = max(2, (target_height // 2) * 2)

            if clip_width == target_width and clip_height == target_height:
                return clip

            clip_ratio = clip_width / clip_height
            target_ratio = target_width / target_height

            if clip_ratio >= target_ratio:
                new_width = target_width
                new_height = int(round(target_width / clip_ratio))
            else:
                new_height = target_height
                new_width = int(round(target_height * clip_ratio))

            new_width = max(2, (new_width // 2) * 2)
            new_height = max(2, (new_height // 2) * 2)

            resized_clip = clip.resized(new_size=(new_width, new_height))

            return resized_clip.with_background_color(
                size=(target_width, target_height),
                color=(0, 0, 0),
                pos='center'
            )
        except Exception as e:
            print(f"   ⚠️  调整分辨率失败: {e}")
            return clip
