"""FFmpeg-based timeline renderer for video composition."""

from __future__ import annotations

import json
import math
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Sequence, Dict, Tuple


class FFmpegRenderError(RuntimeError):
    """Raised when FFmpeg rendering fails."""


@dataclass
class SegmentSpec:
    """Represents a single timeline segment."""

    index: int
    source_path: Optional[str]
    source_type: str  # 'video', 'image', or 'color'
    duration: float
    text: Optional[str]
    section_name: str
    text_style: Optional[Dict[str, str]] = None


@dataclass
class AudioPlan:
    """Audio rendering plan."""

    use_tts: bool
    tts_inputs: List[str]
    tts_durations: List[float]
    bgm_path: Optional[str]
    bgm_volume: float
    target_duration: float
    audio_codec: str


class FFmpegTimelineRenderer:
    """Builds and executes FFmpeg commands to render video timelines."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe") -> None:
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render(
        self,
        segments: Sequence[SegmentSpec],
        output_path: str,
        *,
        fps: int,
        resolution: Tuple[int, int],
        codec: str,
        preset: Optional[str],
        bitrate: Optional[str],
        threads: Optional[int],
        nvenc_params: Optional[List[str]],
        audio_plan: Optional[AudioPlan],
        subtitle_file: Optional[str] = None,
        subtitle_style: Optional[Dict[str, str]] = None,
    ) -> None:
        if not segments:
            raise ValueError("segments must not be empty")

        width, height = resolution
        # 如果有字幕文件，禁用segment级别的文字显示（避免重复）
        use_segment_text = subtitle_file is None

        video_inputs, filter_graph, concat_label = self._build_video_filters(
            segments=segments,
            fps=fps,
            resolution=(width, height),
            use_segment_text=use_segment_text,
        )

        audio_inputs, audio_label, audio_filters = self._build_audio_filters(
            len(video_inputs),
            audio_plan,
        )

        # 如果有字幕文件，在concat之后添加字幕filter
        final_video_label = concat_label
        if subtitle_file and os.path.exists(subtitle_file):
            subtitle_filter = self._build_subtitle_filter(
                concat_label,
                subtitle_file,
                subtitle_style,
            )
            filter_graph.append(subtitle_filter)
            final_video_label = "[vfinal]"

        filter_parts = filter_graph + audio_filters
        filter_complex = ";".join(part for part in filter_parts if part)

        cmd: List[str] = [
            self.ffmpeg_path,
            "-y",
            "-loglevel",
            "error",
        ]

        for input_args in video_inputs + audio_inputs:
            cmd.extend(input_args)

        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex])

        cmd.extend(["-map", final_video_label])
        if audio_label:
            cmd.extend(["-map", audio_label])

        cmd.extend(["-c:v", codec])
        use_nvenc = 'nvenc' in codec.lower()
        if codec.lower().startswith("h264"):
            cmd.extend(["-pix_fmt", "yuv420p"])

        if preset:
            cmd.extend(["-preset", str(preset)])

        if bitrate and not use_nvenc:
            cmd.extend(["-b:v", str(bitrate)])

        if threads:
            cmd.extend(["-threads", str(threads)])

        if nvenc_params:
            cmd.extend(nvenc_params)

        if audio_plan and audio_label:
            cmd.extend(["-c:a", audio_plan.audio_codec])

        cmd.extend([
            "-movflags",
            "+faststart",
            output_path,
        ])

        self._run(cmd, description="FFmpeg rendering")

    # ------------------------------------------------------------------
    # Video filter construction
    # ------------------------------------------------------------------
    def _build_video_filters(
        self,
        segments: Sequence[SegmentSpec],
        fps: int,
        resolution: Tuple[int, int],
        use_segment_text: bool = True,
    ) -> Tuple[List[List[str]], List[str], str]:
        width, height = resolution
        inputs: List[List[str]] = []
        filters: List[str] = []
        concat_inputs: List[str] = []

        for segment in segments:
            input_idx = len(inputs)
            concat_inputs.append(f"[v{segment.index}]")

            input_args = self._build_video_input_args(segment, fps, resolution)
            inputs.append(input_args)

            filter_chain = self._build_segment_filter(
                input_index=input_idx,
                segment=segment,
                fps=fps,
                resolution=resolution,
                use_segment_text=use_segment_text,
            )
            filters.append(filter_chain)

        concat_label = "[vout]"
        filters.append(
            "".join(concat_inputs)
            + f"concat=n={len(segments)}:v=1:a=0{concat_label}"
        )

        return inputs, filters, concat_label

    def _build_video_input_args(
        self,
        segment: SegmentSpec,
        fps: int,
        resolution: Tuple[int, int],
    ) -> List[str]:
        width, height = resolution
        if segment.source_type == "image" and segment.source_path:
            return [
                "-loop",
                "1",
                "-framerate",
                str(fps),
                "-i",
                segment.source_path,
            ]

        if segment.source_type == "video" and segment.source_path:
            args = ["-i", segment.source_path]
            if not self._is_duration_sufficient(segment.source_path, segment.duration):
                args = ["-stream_loop", "-1"] + args
            return args

        # Fallback: generated color source
        color_filter = (
            f"color=size={width}x{height}:rate={fps}:color=black"
        )
        return ["-f", "lavfi", "-i", color_filter]

    def _build_segment_filter(
        self,
        input_index: int,
        segment: SegmentSpec,
        fps: int,
        resolution: Tuple[int, int],
        use_segment_text: bool = True,
    ) -> str:
        width, height = resolution
        label = f"[{input_index}:v]"
        chain: List[str] = []

        if segment.source_type in {"video", "image"}:
            chain.extend(
                [
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease",
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
                ]
            )

        chain.append(f"trim=duration={segment.duration:.6f}")
        chain.append("setpts=PTS-STARTPTS")
        chain.append(f"fps={fps}")

        # 只有在use_segment_text=True时才添加segment文字（避免与字幕文件重复）
        if use_segment_text and segment.text:
            chain.append(self._drawtext_filter(segment.text, segment.text_style))

        chain.extend(["format=yuv420p", "setsar=1"])

        return f"{label}{','.join(chain)}[v{segment.index}]"

    # ------------------------------------------------------------------
    # Audio filters
    # ------------------------------------------------------------------
    def _build_audio_filters(
        self,
        video_input_count: int,
        plan: Optional[AudioPlan],
    ) -> Tuple[List[List[str]], str, List[str]]:
        if plan is None:
            return [], "", []

        inputs: List[List[str]] = []
        filters: List[str] = []
        audio_label = ""

        tts_labels: List[str] = []

        for idx, audio_path in enumerate(plan.tts_inputs):
            inputs.append(["-i", audio_path])
            tts_labels.append(f"[{video_input_count + idx}:a]")

        bgm_label: Optional[str] = None
        if plan.bgm_path:
            inputs.append(["-stream_loop", "-1", "-i", plan.bgm_path])
            bgm_label = f"[{video_input_count + len(plan.tts_inputs)}:a]"

        current_label: Optional[str] = None

        if plan.use_tts and tts_labels:
            concat_label = "[atts]"
            filters.append(
                "".join(tts_labels)
                + f"concat=n={len(tts_labels)}:v=0:a=1,asetpts=N/SR/TB{concat_label}"
            )
            current_label = concat_label

        if bgm_label:
            trimmed_label = "[bgmtrim]"
            filters.append(
                f"{bgm_label}aloop=loop=-1:size=0,asetpts=N/SR/TB,atrim=duration={plan.target_duration:.6f},asetpts=PTS-STARTPTS,volume={plan.bgm_volume}{trimmed_label}"
            )

            if current_label:
                mix_out = "[amix]"
                filters.append(
                    f"{current_label}{trimmed_label}amix=inputs=2:normalize=0:dropout_transition=0{mix_out}"
                )
                current_label = mix_out
            else:
                current_label = trimmed_label

        audio_label = current_label or ""
        return inputs, audio_label, filters

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_subtitle_filter(
        self,
        input_label: str,
        subtitle_file: str,
        style: Optional[Dict[str, str]],
    ) -> str:
        """
        构建字幕filter（使用FFmpeg subtitles filter）

        Args:
            input_label: 输入视频的label（如"[vout]"）
            subtitle_file: 字幕文件路径（.srt或.ass）
            style: 字幕样式配置

        Returns:
            完整的字幕filter字符串
        """
        style = style or {}

        # 转义字幕文件路径（FFmpeg filter需要）
        # 在Windows和Linux上，路径中的反斜杠和冒号需要转义
        escaped_path = subtitle_file.replace('\\', '\\\\').replace(':', '\\:')

        # 构建ASS样式覆盖
        fontsize = style.get("fontsize", "48")
        fontcolor = style.get("fontcolor", "white")
        bg_color = style.get("bg_color", "black")
        bg_opacity = style.get("bg_opacity", "0.5")

        # 将颜色转换为ASS格式 (&HAABBGGRR，注意是BGR顺序)
        # 这里简化处理，只支持基本颜色名
        color_map = {
            "white": "&H00FFFFFF",
            "black": "&H00000000",
            "yellow": "&H0000FFFF",
            "red": "&H000000FF",
            "blue": "&H00FF0000",
        }

        primary_color = color_map.get(fontcolor.lower(), "&H00FFFFFF")
        back_color = color_map.get(bg_color.lower(), "&H00000000")

        # 计算背景透明度（ASS使用0-255，0为不透明）
        try:
            opacity_value = float(bg_opacity)
            ass_alpha = int((1.0 - opacity_value) * 255)
            back_color_with_alpha = f"&H{ass_alpha:02X}000000"
        except (ValueError, TypeError):
            back_color_with_alpha = "&H80000000"  # 默认50%透明

        # 构建force_style字符串（ASS样式覆盖）
        force_style_parts = [
            f"FontSize={fontsize}",
            f"PrimaryColour={primary_color}",
            f"BackColour={back_color_with_alpha}",
            "Alignment=2",  # 底部居中
            "MarginV=50",   # 垂直边距
        ]

        force_style = ",".join(force_style_parts)

        # 返回完整的filter字符串
        return f"{input_label}subtitles={escaped_path}:force_style='{force_style}'[vfinal]"

    def _drawtext_filter(self, text: str, style: Optional[Dict[str, str]]) -> str:
        style = style or {}
        font_path = style.get("font") or ""
        fontsize = style.get("fontsize", "40")
        fontcolor = style.get("fontcolor", "white")
        box_color = style.get("boxcolor", "black@0.5")
        box_border = style.get("boxborder", "30")
        margin = style.get("margin", "80")

        escaped_text = self._escape_drawtext(text)
        escaped_font = self._escape_drawtext(font_path) if font_path else ""
        font_part = f":fontfile={escaped_font}" if escaped_font else ""
        return (
            f"drawtext=text={escaped_text}{font_part}:fontsize={fontsize}:fontcolor={fontcolor}"
            f":box=1:boxcolor={box_color}:boxborderw={box_border}:x=(w-text_w)/2:y=h-(text_h+{margin})"
        )

    @staticmethod
    def _escape_drawtext(text: str) -> str:
        """转义FFmpeg drawtext filter的特殊字符（不使用引号模式）"""
        # 必须首先转义反斜杠
        escaped = text.replace("\\", "\\\\")
        # 转义FFmpeg filter特殊字符
        escaped = escaped.replace("'", "\\'")
        escaped = escaped.replace(":", "\\:")
        escaped = escaped.replace("[", "\\[")
        escaped = escaped.replace("]", "\\]")
        escaped = escaped.replace(",", "\\,")
        escaped = escaped.replace(";", "\\;")
        escaped = escaped.replace("=", "\\=")
        escaped = escaped.replace("%", "\\%")
        escaped = escaped.replace("\n", "\\n")
        escaped = escaped.replace("\r", "")  # 移除回车符
        return escaped

    def _is_duration_sufficient(self, path: str, target: float) -> bool:
        duration = self._probe_duration(path)
        if duration is None:
            return True
        return duration >= (target - 0.05)

    def _probe_duration(self, path: str) -> Optional[float]:
        if not os.path.exists(path):
            return None

        cmd = [
            self.ffprobe_path,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ]
        try:
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError:
            return None

        output = result.stdout.strip()
        try:
            return float(output)
        except (TypeError, ValueError):
            return None

    def _run(self, cmd: Sequence[str], *, description: str) -> None:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if process.returncode != 0:
            raise FFmpegRenderError(
                f"{description} failed (code {process.returncode}).\nCommand: {' '.join(shlex.quote(c) for c in cmd)}\nError: {process.stderr.strip()}"
            )
