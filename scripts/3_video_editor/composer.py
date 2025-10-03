"""
视频合成器
基于脚本自动合成完整视频
"""

import json
import os
import sys
from dataclasses import replace
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import tempfile
import shutil

# 修复相对导入问题 - 导入VideoEditor
sys.path.insert(0, os.path.dirname(__file__))
from editor import VideoEditor

# V5.6: 导入项目归档器
from project_archiver import ProjectArchiver

# 导入素材推荐器
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '2_material_manager'))
from recommender import MaterialRecommender
from manager import MaterialManager

from ffmpeg_renderer import (
    AudioPlan,
    FFmpegRenderError,
    FFmpegTimelineRenderer,
    SegmentSpec,
)


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
        根据脚本自动合成视频
        V5.6: 新增项目归档功能，将所有相关文件整理到项目文件夹

        Args:
            script: 脚本字典（包含sections）
            auto_select_materials: 是否自动选择素材
            output_filename: 输出文件名（已废弃，使用脚本标题）
            tts_metadata_path: TTS音频元数据JSON文件路径 (V5.0新增)
            subtitle_file: 字幕文件路径(.srt/.ass) (V5.0新增)
            use_tts_audio: 是否使用TTS音频替代BGM (V5.0新增)

        Returns:
            项目文件夹路径（V5.6变更：之前返回视频路径）
        """
        print(f"\n🎬 开始合成视频: {script.get('title', '未命名')}")
        print("=" * 60)

        sections = script.get('sections', [])
        if not sections:
            raise ValueError("脚本没有章节内容")

        # V5.6: 创建项目文件夹和归档器
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        script_title = script.get('title', 'video')
        safe_title = "".join(c for c in script_title if c.isalnum() or c in (' ', '-', '_')).strip()
        project_name = f"{safe_title}_{timestamp}"
        project_folder = os.path.join('output/projects', project_name)

        archiver = ProjectArchiver(project_folder)
        archiver.create_project_structure()

        # 保存脚本副本
        archiver.save_script(script)

        # 🚀 多线程优化: 并行处理所有章节
        print(f"\n🚀 使用多线程并行处理 {len(sections)} 个章节...")

        # V5.6: 批量推荐素材（保存完整推荐信息）
        section_materials = {}
        section_recommendations = {}  # 新增：保存所有推荐（用于报告）

        if auto_select_materials:
            print("🔍 批量推荐素材...")
            with ThreadPoolExecutor(max_workers=min(8, len(sections))) as executor:
                future_to_section = {
                    executor.submit(self._recommend_material_for_section_v2, i, section): i
                    for i, section in enumerate(sections)
                }

                for future in as_completed(future_to_section):
                    section_idx = future_to_section[future]
                    try:
                        material_path, material_info, all_recommendations = future.result()
                        section_materials[section_idx] = (material_path, material_info)
                        section_recommendations[section_idx] = all_recommendations
                    except Exception as e:
                        print(f"   ⚠️  章节 {section_idx + 1} 素材推荐失败: {str(e)}")
                        section_materials[section_idx] = (None, None)
                        section_recommendations[section_idx] = []

        # 并行创建视频片段
        print("🎬 并行创建视频片段...")
        # V5.6: 视频输出到临时路径
        temp_video_path = os.path.join(tempfile.gettempdir(), f"{project_name}.mp4")

        print(f"\n💾 导出视频...")

        total_duration, segment_count = self._render_with_ffmpeg(
            sections=sections,
            section_materials=section_materials,
            output_path=temp_video_path,
            use_tts_audio=use_tts_audio,
            tts_metadata_path=tts_metadata_path,
            subtitle_file=subtitle_file,
        )

        print(f"\n✅ 视频合成完成")
        print(f"   时长: {total_duration:.1f}秒")
        print(f"   片段数: {segment_count}")

        # V5.6: 归档所有相关文件
        print(f"\n📦 归档项目文件...")

        # 复制素材文件
        archiver.copy_materials(section_materials, sections)

        # 生成素材选择报告
        archiver.generate_selection_report(
            script,
            section_materials,
            section_recommendations
        )

        # 复制音频文件
        if use_tts_audio and tts_metadata_path:
            archiver.copy_audio_files(tts_metadata_path)

        # 复制字幕文件
        if subtitle_file:
            archiver.copy_subtitle_file(subtitle_file)

        # 保存合成日志
        archiver.save_composition_log({
            'timestamp': timestamp,
            'duration': total_duration,
            'segments': segment_count,
            'use_tts_audio': use_tts_audio,
            'bgm_enabled': self.config.get('tts', {}).get('enable_bgm_mixing', True),
            'config': {
                'resolution': self.video_config.get('resolution'),
                'fps': self.video_config.get('fps'),
                'codec': self.video_config.get('codec'),
                'bitrate': self.video_config.get('bitrate')
            }
        })

        # 移动视频到项目文件夹
        final_video_path = os.path.join(project_folder, 'video.mp4')
        shutil.move(temp_video_path, final_video_path)

        # 生成项目元数据
        archiver.generate_metadata(
            script,
            {
                'duration': total_duration,
                'segments': segment_count,
                'resolution': self.video_config.get('resolution'),
                'fps': self.video_config.get('fps')
            }
        )

        print(f"\n🎉 项目归档完成!")
        print(f"   📁 项目文件夹: {project_folder}")
        print(f"   🎬 视频文件: {final_video_path}")
        print(f"\n   包含文件:")
        print(f"      • video.mp4 - 最终视频")
        print(f"      • script.json - 脚本文件")
        print(f"      • material_selection_report.json/txt - 素材选择报告")
        print(f"      • materials/ - 使用的素材副本")
        if use_tts_audio and tts_metadata_path:
            print(f"      • audio/ - TTS音频文件")
        if subtitle_file:
            print(f"      • subtitles.* - 字幕文件")
        print(f"      • composition_log.txt - 合成日志")
        print(f"      • project_metadata.json - 项目元数据")

        return project_folder

    def _build_segments(
        self,
        sections: List[Dict[str, Any]],
        section_materials: Dict[int, Tuple[Optional[str], Optional[Dict[str, Any]]]],
        tts_durations: Optional[List[float]] = None,
    ) -> List[SegmentSpec]:
        """
        构建视频片段列表

        Args:
            sections: 脚本章节列表
            section_materials: 章节素材映射
            tts_durations: TTS音频时长列表（优先使用，如果提供）

        Returns:
            视频片段列表
        """
        segments: List[SegmentSpec] = []
        text_enabled = self.video_config.get('show_narration_text', True)
        text_style = self._get_text_style()

        # V5.4: 是否使用TTS时长（配置项）
        use_tts_duration = self.video_config.get('use_tts_duration', True)

        for idx, section in enumerate(sections):
            section_name = section.get('section_name', f'章节{idx + 1}')
            narration = section.get('narration', '')

            # V5.4: 优先使用TTS实际时长，确保音画同步
            if use_tts_duration and tts_durations and idx < len(tts_durations):
                duration = tts_durations[idx]
                print(f"   🎙️  章节 {idx + 1} 使用TTS时长: {duration:.2f}秒")
            else:
                duration = self._parse_duration(
                    section.get('duration', self.default_image_duration),
                    default=self.default_image_duration
                )

            material_path = None
            material_info = None
            if idx in section_materials:
                material_path, material_info = section_materials[idx]

            if not material_path:
                fallback_path = section.get('material_path') or section.get('material')
                if fallback_path and os.path.exists(fallback_path):
                    material_path = fallback_path

            source_type = self._detect_media_type(material_path)

            text_value = narration if text_enabled and narration else None
            segment = SegmentSpec(
                index=idx,
                source_path=material_path,
                source_type=source_type,
                duration=duration,
                text=text_value,
                section_name=section_name,
                text_style=text_style if text_value else None,
            )
            segments.append(segment)

            material_desc = '黑屏' if source_type == 'color' else os.path.basename(material_path)
            print(f"   ✅ 章节 {idx + 1}/{len(sections)}: {section_name} (素材: {material_desc})")

        return segments

    def _detect_media_type(self, path: Optional[str]) -> str:
        if not path or not os.path.exists(path):
            return 'color'

        ext = os.path.splitext(path)[1].lower()
        if ext in {'.mp4', '.mov', '.mkv', '.avi', '.webm'}:
            return 'video'
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
            return 'image'
        return 'color'

    def _get_text_style(self) -> Dict[str, str]:
        style: Dict[str, str] = {}
        subtitle_cfg = self.config.get('subtitle', {})
        font_path = subtitle_cfg.get('font')
        if font_path and os.path.exists(font_path):
            style['font'] = font_path
        style['fontsize'] = str(self.video_config.get('text_size', 40))
        style['fontcolor'] = subtitle_cfg.get('font_color', 'white')
        style['boxcolor'] = f"{subtitle_cfg.get('bg_color', 'black')}@{subtitle_cfg.get('bg_opacity', 0.5)}"
        style['boxborder'] = '30'
        style['margin'] = '100'
        return style

    def _build_audio_plan(
        self,
        *,
        use_tts_audio: bool,
        tts_metadata_path: Optional[str],
        video_duration: float,
    ) -> Optional[AudioPlan]:
        audio_codec = self.video_config.get('audio_codec', 'aac')
        bgm_path = self.video_config.get('default_bgm')
        bgm_volume = self.config.get('tts', {}).get('bgm_volume', 0.2)
        enable_bgm_mix = self.config.get('tts', {}).get('enable_bgm_mixing', True)

        if use_tts_audio and tts_metadata_path and os.path.exists(tts_metadata_path):
            print("🎙️  使用TTS音频...")
            try:
                with open(tts_metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"   ⚠️  无法读取TTS元数据: {exc}")
            else:
                audio_items = metadata.get('audio_files', [])
                audio_files = [item.get('file_path') for item in audio_items if item.get('file_path') and os.path.exists(item.get('file_path'))]
                durations = [float(item.get('duration', 0.0) or 0.0) for item in audio_items if item.get('file_path') and os.path.exists(item.get('file_path'))]

                if audio_files:
                    print(f"   ✅ 合并 {len(audio_files)} 段语音")
                    bgm_candidate = bgm_path if (bgm_path and os.path.exists(bgm_path) and enable_bgm_mix) else None
                    target_duration = sum(durations) if durations else video_duration
                    return AudioPlan(
                        use_tts=True,
                        tts_inputs=audio_files,
                        tts_durations=durations or [target_duration],
                        bgm_path=bgm_candidate,
                        bgm_volume=bgm_volume,
                        target_duration=target_duration,
                        audio_codec=audio_codec,
                    )

        if bgm_path and os.path.exists(bgm_path):
            print("🎵 使用背景音乐填充音轨")
            return AudioPlan(
                use_tts=False,
                tts_inputs=[],
                tts_durations=[],
                bgm_path=bgm_path,
                bgm_volume=bgm_volume,
                target_duration=video_duration,
                audio_codec=audio_codec,
            )

        print("🔇 未配置音频，将输出无声视频")
        return None

    def _get_resolution(self) -> Tuple[int, int]:
        resolution = self.video_config.get('resolution', {'width': 1920, 'height': 1080})
        if isinstance(resolution, dict):
            width = int(resolution.get('width', 1920))
            height = int(resolution.get('height', 1080))
        else:
            width, height = resolution
        return width, height

    def _render_with_ffmpeg(
        self,
        *,
        sections: List[Dict[str, Any]],
        section_materials: Dict[int, Tuple[Optional[str], Optional[Dict[str, Any]]]],
        output_path: str,
        use_tts_audio: bool,
        tts_metadata_path: Optional[str],
        subtitle_file: Optional[str] = None,
    ) -> Tuple[float, int]:
        # V5.4: 提取TTS时长列表（如果有）
        tts_durations = None
        if use_tts_audio and tts_metadata_path and os.path.exists(tts_metadata_path):
            try:
                with open(tts_metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                audio_items = metadata.get('audio_files', [])
                tts_durations = [
                    float(item.get('duration', 0.0) or 0.0)
                    for item in audio_items
                    if item.get('file_path') and os.path.exists(item.get('file_path'))
                ]
                if tts_durations:
                    print(f"   📊 已加载 {len(tts_durations)} 段TTS时长数据")
            except (OSError, json.JSONDecodeError) as exc:
                print(f"   ⚠️  无法读取TTS元数据: {exc}")
                tts_durations = None

        # 构建视频片段（使用TTS时长）
        segments = self._build_segments(
            sections=sections,
            section_materials=section_materials,
            tts_durations=tts_durations,
        )

        if not segments:
            raise ValueError("没有生成任何视频片段")

        total_duration = sum(segment.duration for segment in segments)
        audio_plan = self._build_audio_plan(
            use_tts_audio=use_tts_audio,
            tts_metadata_path=tts_metadata_path,
            video_duration=total_duration,
        )

        # V5.4: 由于已经使用TTS时长构建片段，不再需要调整最后一个片段
        # 只在极端情况下（误差>1秒）才调整
        if audio_plan and audio_plan.use_tts:
            audio_total = sum(audio_plan.tts_durations)
            diff = audio_total - total_duration
            if abs(diff) > 1.0:  # 从0.1改为1.0，只在有明显误差时才调整
                print(f"   ⚠️  视频总时长与音频不匹配（差异 {diff:.2f}秒），调整最后片段")
                last_segment = segments[-1]
                adjusted_duration = max(0.5, last_segment.duration + diff)
                segments[-1] = replace(last_segment, duration=adjusted_duration)

        total_duration = sum(segment.duration for segment in segments)
        if audio_plan:
            if audio_plan.use_tts:
                audio_total = sum(audio_plan.tts_durations)
                audio_plan.target_duration = max(audio_total, total_duration)
            else:
                audio_plan.target_duration = total_duration

        renderer = FFmpegTimelineRenderer(
            ffmpeg_path=os.environ.get('IMAGEIO_FFMPEG_EXE', 'ffmpeg'),
            ffprobe_path=os.environ.get('FFPROBE_BINARY', 'ffprobe'),
        )

        codec = self.video_config.get('codec', 'libx264')
        use_gpu = self.video_config.get('gpu_acceleration', False) and 'nvenc' in codec

        preset = None
        nvenc_params = None
        if use_gpu:
            preset = self.video_config.get('gpu_preset', 'p4')
            custom_nvenc = self.video_config.get('nvenc_params')
            if isinstance(custom_nvenc, list) and custom_nvenc:
                nvenc_params = [str(p) for p in custom_nvenc]
            else:
                cq = str(self.video_config.get('nvenc_cq', 19))
                nvenc_params = ['-rc', 'vbr', '-cq', cq]
            print(f"   🚀 启用GPU加速: {codec} (preset: {preset})")
        else:
            preset = self.video_config.get('preset', 'medium')

        # 构建字幕样式配置
        subtitle_style = None
        if subtitle_file and os.path.exists(subtitle_file):
            subtitle_cfg = self.config.get('subtitle', {})
            subtitle_style = {
                'fontsize': str(subtitle_cfg.get('font_size', 48)),
                'fontcolor': subtitle_cfg.get('font_color', 'white'),
                'bg_color': subtitle_cfg.get('bg_color', 'black'),
                'bg_opacity': str(subtitle_cfg.get('bg_opacity', 0.5)),
            }
            print(f"   📝 使用字幕文件: {os.path.basename(subtitle_file)}")

        render_kwargs = dict(
            segments=segments,
            output_path=output_path,
            fps=self.video_config.get('fps', 24),
            resolution=self._get_resolution(),
            codec=codec,
            preset=preset,
            bitrate=self.video_config.get('bitrate'),
            threads=self.video_config.get('threads'),
            nvenc_params=nvenc_params,
            audio_plan=audio_plan,
            subtitle_file=subtitle_file,
            subtitle_style=subtitle_style,
        )

        try:
            renderer.render(**render_kwargs)
        except FFmpegRenderError as exc:
            if use_gpu:
                print("\n⚠️  NVENC导出失败，尝试回退到CPU编码(libx264)...")
                print(f"   ❌ NVENC失败详情: {exc}")
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass

                render_kwargs.update(
                    codec='libx264',
                    preset=self.video_config.get('preset', 'medium'),
                    nvenc_params=None,
                )
                renderer.render(**render_kwargs)
            else:
                raise

        return total_duration, len(segments)

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
        print(f"\n🎬 开始合成视频（自定义素材）: {script.get('title', '未命名')}")

        sections = script.get('sections', [])
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_custom_{timestamp}.mp4"

        output_path = os.path.join(self.editor.output_dir, output_filename)
        section_materials = {
            idx: (path if path and os.path.exists(path) else None, None)
            for idx, path in material_mapping.items()
        }

        total_duration, segment_count = self._render_with_ffmpeg(
            sections=sections,
            section_materials=section_materials,
            output_path=output_path,
            use_tts_audio=False,
            tts_metadata_path=None,
        )

        print(f"\n✅ 视频合成完成: {output_path}")
        print(f"   时长: {total_duration:.1f}秒")
        print(f"   片段数: {segment_count}")

        return output_path

    def preview_material_recommendations(self, script: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        预览脚本各章节的素材推荐
        V5.6: 支持visual_options多层次场景展示

        Args:
            script: 脚本字典

        Returns:
            推荐列表（每个章节的推荐素材）
        """
        sections = script.get('sections', [])
        all_recommendations = []

        print(f"\n🔍 素材推荐预览: {script.get('title', '未命名')}")
        print("=" * 80)

        for i, section in enumerate(sections, 1):
            section_name = section.get('section_name', f'章节{i}')
            narration = section.get('narration', '')[:60]

            print(f"\n📌 {i}. {section_name}")
            print(f"   旁白: {narration}...")

            # V5.6: 显示visual_options（如果有）
            visual_options = section.get('visual_options', [])
            if visual_options:
                print(f"\n   🎬 视觉方案（3个层次）:")
                for opt in visual_options:
                    priority = opt.get('priority', 0)
                    desc = opt.get('description', '')
                    complexity = opt.get('complexity', 'unknown')
                    source = opt.get('suggested_source', '')

                    # 优先级emoji
                    priority_emoji = {1: "🌟", 2: "⭐", 3: "✨"}.get(priority, "•")

                    print(f"      {priority_emoji} Priority {priority} ({complexity})")
                    print(f"         {desc}")
                    print(f"         建议来源: {source}")
            else:
                # 显示旧格式的visual_notes
                visual_notes = section.get('visual_notes', '')
                if visual_notes:
                    print(f"   视觉: {visual_notes[:80]}...")

            print()  # 空行

            # 获取推荐素材
            recommendations = self.recommender.recommend_for_script_section(
                section,
                limit=5
            )

            if recommendations:
                # V5.6: 增强显示格式
                best_rec = recommendations[0]
                matched_priority = best_rec.get('matched_priority', 0)
                semantic_score = best_rec.get('match_score', 0)

                # 评分等级
                if semantic_score >= 80:
                    score_level = "优秀"
                    score_color = "✅"
                elif semantic_score >= 60:
                    score_level = "良好"
                    score_color = "⚠️ "
                else:
                    score_level = "一般"
                    score_color = "❌"

                print(f"   🎯 智能匹配结果:")
                if matched_priority:
                    print(f"      ✅ 采用 Priority {matched_priority} 方案")
                print(f"      {score_color} 语义匹配度: {semantic_score:.0f}% ({score_level})")

                # 匹配/缺失元素
                matched_elements = best_rec.get('matched_elements', [])
                missing_elements = best_rec.get('missing_elements', [])
                if matched_elements:
                    print(f"      ✅ 匹配元素: {', '.join(matched_elements)}")
                if missing_elements:
                    print(f"      ❌ 缺失元素: {', '.join(missing_elements)}")

                print(f"\n   💎 推荐素材:")
                for j, rec in enumerate(recommendations, 1):
                    marker = "⭐" if j == 1 else "  "
                    type_icon = "🎥" if rec['type'] == 'video' else "🖼️"
                    print(f"   {marker} {j}) {type_icon} {rec['name']}")

                    # 匹配信息
                    rec_score = rec.get('match_score', 0)
                    rec_priority = rec.get('matched_priority')
                    print(f"      📊 匹配度: {rec_score:.0f}%", end="")
                    if rec_priority:
                        print(f" | Priority {rec_priority}", end="")
                    print(f" | 类型: {rec['type']}")

                    # 标签
                    tags = rec.get('tags', [])[:3]
                    if tags:
                        print(f"      🏷️  标签: {', '.join(tags)}")

                    # AI分析原因
                    match_reason = rec.get('match_reason', '')
                    if match_reason:
                        print(f"      💡 AI分析: {match_reason[:80]}...")

                    # 文件路径
                    file_path = rec.get('file_path', '')
                    if file_path:
                        file_name = os.path.basename(file_path)
                        print(f"      📁 文件: {file_name}")

                    if j < len(recommendations):
                        print()  # 素材间空行
            else:
                print("   ⚠️  未找到合适素材")
                print("   💡 建议: 使用AI生成或手动上传素材")

            all_recommendations.append({
                'section_index': i - 1,
                'section_name': section_name,
                'recommendations': recommendations
            })

        print("\n" + "=" * 80)
        print(f"💡 提示: ⭐标记的素材将被自动选择用于视频合成")
        print(f"📋 操作选项:")
        print(f"   [1] 使用推荐素材直接合成")
        print(f"   [2] 查看单个章节详情")
        print(f"   [3] 手动选择素材")

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

    def _recommend_material_for_section(self, section_idx: int, section: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict]]:
        """
        为单个章节推荐素材（多线程辅助函数）

        Args:
            section_idx: 章节索引
            section: 章节字典

        Returns:
            (素材路径, 素材信息) 元组
        """
        recommendations = self.recommender.recommend_for_script_section(section, limit=3)

        if recommendations:
            best_material = recommendations[0]
            return best_material['file_path'], best_material
        else:
            return None, None

    def _recommend_material_for_section_v2(self, section_idx: int, section: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict], List[Dict]]:
        """
        为单个章节推荐素材（V5.6增强版 - 返回完整推荐列表用于归档）

        Args:
            section_idx: 章节索引
            section: 章节字典

        Returns:
            (素材路径, 最佳素材信息, 所有推荐列表) 元组
        """
        recommendations = self.recommender.recommend_for_script_section(section, limit=5)

        if recommendations:
            best_material = recommendations[0]
            return best_material['file_path'], best_material, recommendations
        else:
            return None, None, []

    def _create_clip_from_material(self, material_path: Optional[str], duration: float):
        """
        从素材创建视频片段（多线程辅助函数）

        Args:
            material_path: 素材路径
            duration: 持续时间

        Returns:
            视频片段对象
        """
        from moviepy import ImageClip, VideoFileClip
        from moviepy.video.fx import Loop

        if material_path and os.path.exists(material_path):
            # 根据素材类型创建剪辑
            ext = os.path.splitext(material_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                clip = ImageClip(material_path).with_duration(duration)
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                video_clip = VideoFileClip(material_path)

                # 移除音频（因为我们会使用TTS音频）
                video_clip = video_clip.without_audio()

                # 如果视频长度不够，循环播放
                if video_clip.duration < duration:
                    clip = video_clip.with_effects([Loop(duration=duration)])
                else:
                    clip = video_clip.subclipped(0, duration)
            else:
                clip = self._create_color_clip((0, 0, 0), duration)
        else:
            # 创建黑屏
            clip = self._create_color_clip((0, 0, 0), duration)

        return self._ensure_target_resolution(clip)

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

            # NVENC 需要偶数分辨率
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

            # 保证偶数尺寸
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
