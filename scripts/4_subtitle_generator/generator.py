#!/usr/bin/env python3
"""
字幕生成器
根据脚本和音频时长生成SRT/ASS字幕文件
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import timedelta


class SubtitleGenerator:
    """字幕生成器类"""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        初始化字幕生成器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.subtitle_config = self.config.get("subtitle", {})
        self.output_dir = Path(self.config["paths"]["subtitles"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {str(e)}")
            return {}

    def generate_from_script(self, script_path: str,
                            audio_metadata_path: Optional[str] = None,
                            output_name: Optional[str] = None,
                            format: str = "srt") -> Dict:
        """
        根据脚本生成字幕

        Args:
            script_path: 脚本JSON文件路径
            audio_metadata_path: 音频元数据文件路径(用于精确时间对齐)
            output_name: 输出文件名(不含扩展名)
            format: 字幕格式(srt/ass)

        Returns:
            生成结果字典
        """
        print(f"\n📝 开始生成字幕...")
        print(f"📄 脚本: {script_path}")

        try:
            # 读取脚本
            with open(script_path, 'r', encoding='utf-8') as f:
                script = json.load(f)

            sections = script.get("sections", [])
            if not sections:
                print("❌ 脚本中没有找到章节")
                return {"success": False, "error": "no_sections"}

            # 确定输出文件名
            if output_name is None:
                output_name = script.get("title", "untitled").replace(" ", "_")

            # 读取音频时长(如果提供)
            audio_durations = None
            if audio_metadata_path and os.path.exists(audio_metadata_path):
                audio_durations = self._load_audio_durations(audio_metadata_path)
                print(f"✅ 加载音频时长数据: {len(audio_durations)}个章节")

            # 生成字幕条目
            subtitles = self._create_subtitles(sections, audio_durations)

            if not subtitles:
                print("❌ 没有生成任何字幕")
                return {"success": False, "error": "no_subtitles"}

            # 保存字幕文件
            if format.lower() == "srt":
                output_path = self.output_dir / f"{output_name}.srt"
                self._save_srt(subtitles, output_path)
            elif format.lower() == "ass":
                output_path = self.output_dir / f"{output_name}.ass"
                self._save_ass(subtitles, output_path)
            else:
                print(f"❌ 不支持的字幕格式: {format}")
                return {"success": False, "error": f"unsupported_format: {format}"}

            # 计算总时长
            total_duration = subtitles[-1]["end_time"] if subtitles else 0

            print(f"\n✅ 字幕生成完成!")
            print(f"📊 字幕条数: {len(subtitles)}")
            print(f"⏱️  总时长: {total_duration:.1f}秒")
            print(f"💾 输出文件: {output_path}")

            return {
                "success": True,
                "subtitle_file": str(output_path),
                "format": format,
                "subtitle_count": len(subtitles),
                "total_duration": total_duration,
                "subtitles": subtitles
            }

        except Exception as e:
            print(f"\n❌ 生成字幕时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _load_audio_durations(self, audio_metadata_path: str) -> Dict[int, float]:
        """
        从音频元数据加载各章节时长

        Args:
            audio_metadata_path: 音频元数据文件路径

        Returns:
            {章节索引: 时长} 字典
        """
        try:
            with open(audio_metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            durations = {}
            for item in metadata.get("audio_files", []):
                section_index = item.get("section_index")
                duration = item.get("duration", 0)
                if section_index is not None:
                    durations[section_index] = duration

            return durations

        except Exception as e:
            print(f"⚠️  加载音频时长失败: {str(e)}")
            return {}

    def _create_subtitles(self, sections: List[Dict],
                         audio_durations: Optional[Dict[int, float]] = None) -> List[Dict]:
        """
        创建字幕条目列表

        Args:
            sections: 脚本章节列表
            audio_durations: 音频时长字典(可选)

        Returns:
            字幕条目列表
        """
        subtitles = []
        current_time = 0.0

        for i, section in enumerate(sections, 1):
            narration = section.get("narration", "").strip()
            if not narration:
                continue

            # 确定字幕时长
            if audio_durations and i in audio_durations:
                # 使用实际音频时长
                duration = audio_durations[i]
            else:
                # 使用脚本中的时长或估算
                duration = self._parse_duration(section.get("duration", 0), default=0)
                if duration == 0:
                    # 粗略估算: 中文约2.5字/秒
                    duration = max(2.0, len(narration) / 2.5)

            # 分割长文本为多个字幕条目
            subtitle_items = self._split_text(narration, duration)

            for item_text, item_duration in subtitle_items:
                subtitle = {
                    "index": len(subtitles) + 1,
                    "start_time": current_time,
                    "end_time": current_time + item_duration,
                    "text": item_text,
                    "section_index": i,
                    "section_name": section.get("section_name", "")
                }
                subtitles.append(subtitle)
                current_time += item_duration

        return subtitles

    def _split_text(self, text: str, total_duration: float,
                   max_chars: int = 40) -> List[Tuple[str, float]]:
        """
        分割长文本为多个字幕条目

        Args:
            text: 文本内容
            total_duration: 总时长
            max_chars: 每条字幕最大字符数

        Returns:
            [(文本, 时长), ...] 列表
        """
        # 按标点符号分割
        sentences = []
        current = ""

        for char in text:
            current += char
            if char in "。!?;,、":
                if current.strip():
                    sentences.append(current.strip())
                    current = ""

        if current.strip():
            sentences.append(current.strip())

        # 合并短句,确保不超过max_chars
        items = []
        current_item = ""

        for sentence in sentences:
            if len(current_item) + len(sentence) <= max_chars:
                current_item += sentence
            else:
                if current_item:
                    items.append(current_item)
                current_item = sentence

        if current_item:
            items.append(current_item)

        # 分配时长(按字符数比例)
        total_chars = sum(len(item) for item in items)
        result = []

        for item in items:
            char_ratio = len(item) / total_chars if total_chars > 0 else 1.0 / len(items)
            item_duration = total_duration * char_ratio
            result.append((item, item_duration))

        return result

    def _save_srt(self, subtitles: List[Dict], output_path: Path):
        """
        保存SRT格式字幕

        Args:
            subtitles: 字幕列表
            output_path: 输出路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for sub in subtitles:
                # 字幕序号
                f.write(f"{sub['index']}\n")

                # 时间轴
                start = self._format_srt_time(sub['start_time'])
                end = self._format_srt_time(sub['end_time'])
                f.write(f"{start} --> {end}\n")

                # 字幕文本
                f.write(f"{sub['text']}\n\n")

    def _save_ass(self, subtitles: List[Dict], output_path: Path):
        """
        保存ASS格式字幕

        Args:
            subtitles: 字幕列表
            output_path: 输出路径
        """
        # ASS头部
        header = """[Script Info]
Title: Generated Subtitle
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,2,{alignment},10,10,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(
            font=self.subtitle_config.get("font", "Arial"),
            fontsize=self.subtitle_config.get("font_size", 48),
            alignment=self._get_ass_alignment(),
            margin=self._get_margin_v()
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)

            # 字幕内容
            for sub in subtitles:
                start = self._format_ass_time(sub['start_time'])
                end = self._format_ass_time(sub['end_time'])
                text = sub['text'].replace('\n', '\\N')

                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    def _format_srt_time(self, seconds: float) -> str:
        """
        格式化SRT时间码

        Args:
            seconds: 秒数

        Returns:
            SRT时间格式 (HH:MM:SS,mmm)
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millis = int((td.total_seconds() % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_ass_time(self, seconds: float) -> str:
        """
        格式化ASS时间码

        Args:
            seconds: 秒数

        Returns:
            ASS时间格式 (H:MM:SS.cc)
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        centis = int((td.total_seconds() % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def _get_ass_alignment(self) -> int:
        """
        获取ASS对齐方式

        Returns:
            ASS对齐代码
        """
        position = self.subtitle_config.get("position", "bottom")

        alignment_map = {
            "top": 8,     # 顶部居中
            "middle": 5,  # 中间居中
            "bottom": 2   # 底部居中
        }

        return alignment_map.get(position, 2)

    def _get_margin_v(self) -> int:
        """
        获取垂直边距

        Returns:
            垂直边距(像素)
        """
        position = self.subtitle_config.get("position", "bottom")

        if position == "top":
            return 50
        elif position == "bottom":
            return 50
        else:  # middle
            return 0

    def _parse_duration(self, duration_value, default: float = 5.0) -> float:
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


# 命令行测试
if __name__ == "__main__":
    import sys

    generator = SubtitleGenerator()

    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        audio_metadata = sys.argv[2] if len(sys.argv) > 2 else None
        format = sys.argv[3] if len(sys.argv) > 3 else "srt"

        generator.generate_from_script(script_path, audio_metadata, format=format)
    else:
        print("用法:")
        print("  python generator.py <script.json> [audio_metadata.json] [format]")
        print("  format: srt (默认) 或 ass")
