#!/usr/bin/env python3
"""
字幕时间轴对齐器
用于精确对齐字幕与音频的时间轴
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class SubtitleAligner:
    """字幕时间轴对齐器类"""

    def __init__(self):
        """初始化对齐器"""
        pass

    def align_with_audio(self, subtitle_file: str, audio_metadata_path: str,
                        output_file: Optional[str] = None) -> Dict:
        """
        根据音频元数据对齐字幕时间轴

        Args:
            subtitle_file: 字幕文件路径(SRT/ASS)
            audio_metadata_path: 音频元数据JSON文件路径
            output_file: 输出文件路径(可选,默认覆盖原文件)

        Returns:
            对齐结果字典
        """
        print(f"\n⏱️  开始对齐字幕时间轴...")
        print(f"字幕文件: {subtitle_file}")
        print(f"音频元数据: {audio_metadata_path}")

        try:
            # 读取音频元数据
            with open(audio_metadata_path, 'r', encoding='utf-8') as f:
                audio_metadata = json.load(f)

            audio_files = audio_metadata.get("audio_files", [])
            if not audio_files:
                print("❌ 音频元数据中没有音频文件信息")
                return {"success": False, "error": "no_audio_files"}

            # 构建章节时间映射
            section_timings = self._build_section_timings(audio_files)

            # 读取并解析字幕
            subtitle_path = Path(subtitle_file)
            if subtitle_path.suffix.lower() == ".srt":
                subtitles = self._parse_srt(subtitle_file)
                format = "srt"
            elif subtitle_path.suffix.lower() == ".ass":
                subtitles = self._parse_ass(subtitle_file)
                format = "ass"
            else:
                print(f"❌ 不支持的字幕格式: {subtitle_path.suffix}")
                return {"success": False, "error": f"unsupported_format: {subtitle_path.suffix}"}

            if not subtitles:
                print("❌ 没有解析到字幕")
                return {"success": False, "error": "no_subtitles_parsed"}

            # 对齐字幕时间轴
            aligned_subtitles = self._align_subtitles(subtitles, section_timings)

            # 确定输出路径
            if output_file is None:
                output_file = subtitle_file

            # 保存对齐后的字幕
            if format == "srt":
                self._save_srt(aligned_subtitles, output_file)
            else:  # ass
                self._save_ass(aligned_subtitles, output_file)

            print(f"\n✅ 字幕对齐完成!")
            print(f"对齐字幕数: {len(aligned_subtitles)}")
            print(f"输出文件: {output_file}")

            return {
                "success": True,
                "aligned_file": output_file,
                "subtitle_count": len(aligned_subtitles),
                "format": format
            }

        except Exception as e:
            print(f"\n❌ 对齐字幕时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _build_section_timings(self, audio_files: List[Dict]) -> Dict[int, Dict]:
        """
        构建章节时间映射

        Args:
            audio_files: 音频文件列表

        Returns:
            {章节索引: {"start": 开始时间, "end": 结束时间, "duration": 时长}}
        """
        timings = {}
        current_time = 0.0

        for audio_file in audio_files:
            section_index = audio_file.get("section_index")
            duration = audio_file.get("duration", 0)

            timings[section_index] = {
                "start": current_time,
                "end": current_time + duration,
                "duration": duration
            }

            current_time += duration

        return timings

    def _align_subtitles(self, subtitles: List[Dict],
                        section_timings: Dict[int, Dict]) -> List[Dict]:
        """
        对齐字幕时间轴

        Args:
            subtitles: 字幕列表
            section_timings: 章节时间映射

        Returns:
            对齐后的字幕列表
        """
        aligned = []
        current_time = 0.0

        # 按章节分组
        sections = {}
        for sub in subtitles:
            section_idx = sub.get("section_index", 1)
            if section_idx not in sections:
                sections[section_idx] = []
            sections[section_idx].append(sub)

        # 对每个章节的字幕进行时间调整
        for section_idx in sorted(sections.keys()):
            section_subs = sections[section_idx]

            if section_idx not in section_timings:
                # 没有对应的音频时长信息,使用原始时间
                for sub in section_subs:
                    aligned.append(sub)
                if section_subs:
                    current_time = section_subs[-1]["end_time"]
                continue

            # 获取该章节的实际音频时长
            section_timing = section_timings[section_idx]
            audio_start = section_timing["start"]
            audio_duration = section_timing["duration"]

            # 计算该章节原始字幕的总时长
            if section_subs:
                original_start = section_subs[0]["start_time"]
                original_end = section_subs[-1]["end_time"]
                original_duration = original_end - original_start

                # 计算缩放比例
                scale = audio_duration / original_duration if original_duration > 0 else 1.0

                # 调整每条字幕的时间
                for sub in section_subs:
                    # 相对于章节开始的偏移
                    offset_start = sub["start_time"] - original_start
                    offset_end = sub["end_time"] - original_start

                    # 缩放并加上章节的实际开始时间
                    new_start = audio_start + offset_start * scale
                    new_end = audio_start + offset_end * scale

                    aligned_sub = sub.copy()
                    aligned_sub["start_time"] = new_start
                    aligned_sub["end_time"] = new_end
                    aligned.append(aligned_sub)

                current_time = audio_start + audio_duration

        # 重新编号
        for i, sub in enumerate(aligned, 1):
            sub["index"] = i

        return aligned

    def _parse_srt(self, srt_file: str) -> List[Dict]:
        """
        解析SRT字幕文件

        Args:
            srt_file: SRT文件路径

        Returns:
            字幕列表
        """
        subtitles = []

        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 分割字幕块
        blocks = content.strip().split('\n\n')

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            try:
                # 解析序号
                index = int(lines[0])

                # 解析时间轴
                time_line = lines[1]
                start_str, end_str = time_line.split(' --> ')
                start_time = self._parse_srt_time(start_str)
                end_time = self._parse_srt_time(end_str)

                # 解析文本
                text = '\n'.join(lines[2:])

                subtitles.append({
                    "index": index,
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text,
                    "section_index": 1  # 默认值,可能需要从其他元数据获取
                })

            except Exception as e:
                print(f"⚠️  解析字幕块失败: {e}")
                continue

        return subtitles

    def _parse_ass(self, ass_file: str) -> List[Dict]:
        """
        解析ASS字幕文件

        Args:
            ass_file: ASS文件路径

        Returns:
            字幕列表
        """
        subtitles = []
        index = 1

        with open(ass_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line.startswith('Dialogue:'):
                    continue

                try:
                    # 解析Dialogue行
                    parts = line.split(',', 9)
                    if len(parts) < 10:
                        continue

                    start_str = parts[1]
                    end_str = parts[2]
                    text = parts[9]

                    start_time = self._parse_ass_time(start_str)
                    end_time = self._parse_ass_time(end_str)

                    # 处理ASS文本格式
                    text = text.replace('\\N', '\n')

                    subtitles.append({
                        "index": index,
                        "start_time": start_time,
                        "end_time": end_time,
                        "text": text,
                        "section_index": 1
                    })

                    index += 1

                except Exception as e:
                    print(f"⚠️  解析ASS行失败: {e}")
                    continue

        return subtitles

    def _parse_srt_time(self, time_str: str) -> float:
        """
        解析SRT时间码为秒数

        Args:
            time_str: SRT时间字符串 (HH:MM:SS,mmm)

        Returns:
            秒数
        """
        time_str = time_str.strip()
        # 处理格式: 00:00:05,000
        parts = time_str.replace(',', ':').split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        millis = int(parts[3])

        return hours * 3600 + minutes * 60 + seconds + millis / 1000.0

    def _parse_ass_time(self, time_str: str) -> float:
        """
        解析ASS时间码为秒数

        Args:
            time_str: ASS时间字符串 (H:MM:SS.cc)

        Returns:
            秒数
        """
        time_str = time_str.strip()
        # 处理格式: 0:00:05.00
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        sec_parts = parts[2].split('.')
        seconds = int(sec_parts[0])
        centis = int(sec_parts[1]) if len(sec_parts) > 1 else 0

        return hours * 3600 + minutes * 60 + seconds + centis / 100.0

    def _save_srt(self, subtitles: List[Dict], output_path: str):
        """
        保存SRT格式字幕

        Args:
            subtitles: 字幕列表
            output_path: 输出路径
        """
        from datetime import timedelta

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

    def _save_ass(self, subtitles: List[Dict], output_path: str):
        """
        保存ASS格式字幕(需要先读取原文件头部)

        Args:
            subtitles: 字幕列表
            output_path: 输出路径
        """
        # 读取原文件头部(到[Events]部分)
        header = ""
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                header += line
                if line.startswith('Format: Layer'):
                    break

        # 写入新文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)

            # 字幕内容
            for sub in subtitles:
                start = self._format_ass_time(sub['start_time'])
                end = self._format_ass_time(sub['end_time'])
                text = sub['text'].replace('\n', '\\N')

                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    def _format_srt_time(self, seconds: float) -> str:
        """格式化SRT时间码"""
        from datetime import timedelta

        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millis = int((td.total_seconds() % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_ass_time(self, seconds: float) -> str:
        """格式化ASS时间码"""
        from datetime import timedelta

        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        centis = int((td.total_seconds() % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


# 命令行测试
if __name__ == "__main__":
    import sys

    aligner = SubtitleAligner()

    if len(sys.argv) > 2:
        subtitle_file = sys.argv[1]
        audio_metadata = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None

        aligner.align_with_audio(subtitle_file, audio_metadata, output_file)
    else:
        print("用法:")
        print("  python aligner.py <subtitle.srt/ass> <audio_metadata.json> [output_file]")
