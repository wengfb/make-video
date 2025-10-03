"""
视频项目归档器
将视频制作过程中的所有相关文件整理到项目文件夹
V5.6新增
"""

import json
import os
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class ProjectArchiver:
    """视频项目归档器 - 整理所有相关文件到项目文件夹"""

    def __init__(self, project_folder: str):
        """
        初始化项目归档器

        Args:
            project_folder: 项目文件夹路径
        """
        self.project_folder = project_folder
        self.materials_folder = os.path.join(project_folder, 'materials')
        self.audio_folder = os.path.join(project_folder, 'audio')

    def create_project_structure(self):
        """创建项目文件夹结构"""
        print(f"\n📁 创建项目文件夹: {os.path.basename(self.project_folder)}")

        # 创建主文件夹
        os.makedirs(self.project_folder, exist_ok=True)

        # 创建子文件夹
        os.makedirs(self.materials_folder, exist_ok=True)
        os.makedirs(self.audio_folder, exist_ok=True)

        print(f"   ✅ 文件夹结构已创建")

    def save_script(self, script: Dict[str, Any]):
        """
        保存脚本副本

        Args:
            script: 脚本数据
        """
        script_path = os.path.join(self.project_folder, 'script.json')

        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)

        print(f"   ✅ 脚本已保存: script.json")

    def copy_materials(
        self,
        section_materials: Dict[int, tuple],
        sections: List[Dict[str, Any]]
    ):
        """
        复制使用的素材到项目文件夹，按章节命名

        Args:
            section_materials: {section_idx: (file_path, material_info)}
            sections: 脚本章节列表
        """
        print(f"\n📦 复制素材文件...")

        copied_count = 0

        for section_idx, (file_path, material_info) in section_materials.items():
            if not file_path or not os.path.exists(file_path):
                continue

            # 获取章节名称
            section = sections[section_idx]
            section_name = section.get('section_name', f'章节{section_idx + 1}')

            # 清理章节名称（去除特殊字符）
            safe_section_name = "".join(
                c for c in section_name if c.isalnum() or c in (' ', '-', '_')
            ).strip()

            # 获取文件扩展名
            file_ext = Path(file_path).suffix

            # 生成目标文件名：section_01_章节名.mp4
            target_filename = f"section_{section_idx + 1:02d}_{safe_section_name}{file_ext}"
            target_path = os.path.join(self.materials_folder, target_filename)

            # 复制文件
            try:
                shutil.copy2(file_path, target_path)
                copied_count += 1
                print(f"   ✅ {target_filename}")
            except Exception as e:
                print(f"   ❌ 复制失败 {target_filename}: {str(e)}")

        print(f"   总计: {copied_count} 个素材文件")

    def generate_selection_report(
        self,
        script: Dict[str, Any],
        section_materials: Dict[int, tuple],
        section_recommendations: Dict[int, List[Dict[str, Any]]]
    ):
        """
        生成素材选择报告（JSON和TXT两种格式）

        Args:
            script: 脚本数据
            section_materials: 选中的素材
            section_recommendations: 所有推荐素材（包括候选）
        """
        print(f"\n📝 生成素材选择报告...")

        # 生成JSON报告
        json_report = self._build_json_report(
            script,
            section_materials,
            section_recommendations
        )

        json_path = os.path.join(self.project_folder, 'material_selection_report.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)

        print(f"   ✅ JSON报告: material_selection_report.json")

        # 生成TXT可读报告
        txt_report = self._build_txt_report(json_report)

        txt_path = os.path.join(self.project_folder, 'material_selection_report.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(txt_report)

        print(f"   ✅ TXT报告: material_selection_report.txt")

    def _build_json_report(
        self,
        script: Dict[str, Any],
        section_materials: Dict[int, tuple],
        section_recommendations: Dict[int, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """构建JSON格式的报告"""
        sections_data = []
        sections = script.get('sections', [])

        # 统计数据
        stats = {
            'priority_distribution': {'priority_1': 0, 'priority_2': 0, 'priority_3': 0},
            'score_distribution': {'excellent_80_plus': 0, 'good_60_79': 0, 'fair_below_60': 0},
            'material_sources': {},
            'total_semantic_scores': []
        }

        for idx, section in enumerate(sections):
            section_name = section.get('section_name', f'章节{idx + 1}')
            narration = section.get('narration', '')
            duration = section.get('duration', 'N/A')

            # 视觉方案
            visual_options = section.get('visual_options', [])

            # 选中的素材
            selected_material = None
            match_result = {}

            if idx in section_materials:
                _, material_info = section_materials[idx]
                if material_info:
                    selected_material = {
                        'id': material_info.get('id', 'N/A'),
                        'name': material_info.get('name', 'N/A'),
                        'type': material_info.get('type', 'N/A'),
                        'source': material_info.get('source', 'local'),
                        'file_path': material_info.get('file_path', ''),
                        'file_size': self._format_file_size(material_info.get('file_size', 0)),
                        'copied_to': f"section_{idx + 1:02d}_{section_name}.{material_info.get('file_ext', 'mp4').lstrip('.')}"
                    }

                    # 匹配结果
                    matched_priority = material_info.get('matched_priority', 0)
                    semantic_score = material_info.get('match_score', 0)

                    match_result = {
                        'matched_priority': matched_priority,
                        'semantic_score': semantic_score,
                        'score_level': self._get_score_level(semantic_score),
                        'matched_elements': material_info.get('matched_elements', []),
                        'missing_elements': material_info.get('missing_elements', []),
                        'ai_reasoning': material_info.get('match_reason', ''),
                        'recommendation': '推荐使用' if semantic_score >= 70 else '可用但建议优化'
                    }

                    # 统计
                    if matched_priority:
                        stats['priority_distribution'][f'priority_{matched_priority}'] += 1

                    if semantic_score >= 80:
                        stats['score_distribution']['excellent_80_plus'] += 1
                    elif semantic_score >= 60:
                        stats['score_distribution']['good_60_79'] += 1
                    else:
                        stats['score_distribution']['fair_below_60'] += 1

                    stats['total_semantic_scores'].append(semantic_score)

                    # 来源统计
                    source = material_info.get('source', 'local')
                    stats['material_sources'][source] = stats['material_sources'].get(source, 0) + 1

            # 备选素材
            alternative_materials = []
            if idx in section_recommendations:
                recommendations = section_recommendations[idx]
                for rank, rec in enumerate(recommendations[1:6], 2):  # 取2-6名
                    alternative_materials.append({
                        'rank': rank,
                        'id': rec.get('id', 'N/A'),
                        'name': rec.get('name', 'N/A'),
                        'matched_priority': rec.get('matched_priority', 0),
                        'semantic_score': rec.get('match_score', 0),
                        'reasoning': rec.get('match_reason', '')[:100]
                    })

            sections_data.append({
                'section_index': idx,
                'section_name': section_name,
                'duration': str(duration),
                'narration': narration[:150] + '...' if len(narration) > 150 else narration,
                'visual_options': visual_options,
                'material_selection': {
                    'selected_material': selected_material,
                    'match_result': match_result,
                    'alternative_materials': alternative_materials
                }
            })

        # 计算平均分
        avg_score = sum(stats['total_semantic_scores']) / len(stats['total_semantic_scores']) if stats['total_semantic_scores'] else 0

        report = {
            'video_title': script.get('title', '未命名'),
            'generated_at': datetime.now().isoformat(),
            'total_sections': len(sections),
            'total_duration': script.get('total_duration', 'N/A'),
            'sections': sections_data,
            'statistics': {
                'priority_distribution': stats['priority_distribution'],
                'average_semantic_score': round(avg_score, 1),
                'score_distribution': stats['score_distribution'],
                'material_sources': stats['material_sources']
            }
        }

        return report

    def _build_txt_report(self, json_report: Dict[str, Any]) -> str:
        """构建TXT可读格式的报告"""
        lines = []

        # 标题
        lines.append("═" * 70)
        lines.append("    视频素材选择报告".center(70))
        lines.append("═" * 70)
        lines.append("")

        # 基本信息
        lines.append(f"项目: {json_report['video_title']}")
        lines.append(f"生成时间: {json_report['generated_at']}")
        lines.append(f"总章节: {json_report['total_sections']}个")
        lines.append(f"总时长: {json_report['total_duration']}")
        lines.append("")

        # 章节详情
        for section in json_report['sections']:
            lines.append("─" * 70)
            lines.append(f"\n📌 章节 {section['section_index'] + 1}: {section['section_name']} ({section['duration']})")
            lines.append(f"\n旁白:")
            lines.append(section['narration'])

            # 视觉方案
            visual_options = section.get('visual_options', [])
            if visual_options:
                lines.append(f"\n🎬 视觉方案（{len(visual_options)}个层次）:")
                for opt in visual_options:
                    priority = opt.get('priority', 0)
                    emoji = {1: "🌟", 2: "⭐", 3: "✨"}.get(priority, "•")
                    complexity = opt.get('complexity', 'unknown')
                    desc = opt.get('description', '')
                    source = opt.get('suggested_source', '')

                    lines.append(f"\n  {emoji} Priority {priority} ({complexity})")
                    lines.append(f"     {desc}")
                    lines.append(f"     建议来源: {source}")

            # 最终选择
            selection = section['material_selection']
            selected = selection.get('selected_material')
            match_result = selection.get('match_result', {})

            if selected:
                lines.append(f"\n🎯 最终选择:")
                lines.append(f"\n  ✅ 素材: {selected['name']}")
                lines.append(f"     类型: {selected['type']}")
                lines.append(f"     来源: {selected['source']}")
                lines.append(f"     大小: {selected['file_size']}")

                if match_result:
                    lines.append(f"\n  📊 匹配结果:")
                    lines.append(f"     匹配方案: Priority {match_result['matched_priority']}")
                    lines.append(f"     语义评分: {match_result['semantic_score']}% ({match_result['score_level']})")

                    matched = match_result.get('matched_elements', [])
                    if matched:
                        lines.append(f"\n  ✅ 匹配元素:")
                        for elem in matched:
                            lines.append(f"     • {elem}")

                    missing = match_result.get('missing_elements', [])
                    if missing:
                        lines.append(f"\n  ❌ 缺失元素:")
                        for elem in missing:
                            lines.append(f"     • {elem}")

                    reasoning = match_result.get('ai_reasoning', '')
                    if reasoning:
                        lines.append(f"\n  💡 AI分析:")
                        # 换行处理
                        for i in range(0, len(reasoning), 60):
                            lines.append(f"     {reasoning[i:i+60]}")

                lines.append(f"\n  💾 保存位置: materials/{selected['copied_to']}")
            else:
                lines.append(f"\n  ⚠️  未找到合适素材")

            lines.append("")

        # 统计汇总
        lines.append("─" * 70)
        lines.append("\n📊 统计汇总\n")

        stats = json_report['statistics']

        lines.append("方案分布:")
        priority_dist = stats['priority_distribution']
        total = sum(priority_dist.values())
        for i in range(1, 4):
            count = priority_dist.get(f'priority_{i}', 0)
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"  Priority {i}: {count} 个章节 ({pct:.0f}%)")

        lines.append("\n匹配质量:")
        lines.append(f"  平均语义评分: {stats['average_semantic_score']}%")
        score_dist = stats['score_distribution']
        lines.append(f"  优秀 (80%+): {score_dist['excellent_80_plus']} 个章节")
        lines.append(f"  良好 (60-79%): {score_dist['good_60_79']} 个章节")
        lines.append(f"  一般 (<60%): {score_dist['fair_below_60']} 个章节")

        lines.append("\n素材来源:")
        for source, count in stats['material_sources'].items():
            source_name = {
                'pexels': 'Pexels',
                'unsplash': 'Unsplash',
                'local': '本地素材库'
            }.get(source, source)
            lines.append(f"  {source_name}: {count} 个")

        lines.append("\n" + "═" * 70)

        return "\n".join(lines)

    def copy_audio_files(self, tts_metadata_path: Optional[str]):
        """
        复制TTS音频文件

        Args:
            tts_metadata_path: TTS元数据JSON路径
        """
        if not tts_metadata_path or not os.path.exists(tts_metadata_path):
            return

        print(f"\n🎵 复制音频文件...")

        try:
            # 读取TTS元数据
            with open(tts_metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 复制各段音频
            audio_files = metadata.get('audio_files', [])
            for item in audio_files:
                file_path = item.get('file_path', '')
                if file_path and os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    target_path = os.path.join(self.audio_folder, filename)
                    shutil.copy2(file_path, target_path)

            # 复制元数据
            metadata_target = os.path.join(self.audio_folder, 'tts_metadata.json')
            shutil.copy2(tts_metadata_path, metadata_target)

            print(f"   ✅ {len(audio_files)} 个音频文件")

        except Exception as e:
            print(f"   ⚠️  复制音频失败: {str(e)}")

    def copy_subtitle_file(self, subtitle_file: Optional[str]):
        """
        复制字幕文件

        Args:
            subtitle_file: 字幕文件路径
        """
        if not subtitle_file or not os.path.exists(subtitle_file):
            return

        print(f"\n📝 复制字幕文件...")

        try:
            filename = os.path.basename(subtitle_file)
            # 统一命名为 subtitles.srt
            ext = Path(subtitle_file).suffix
            target_path = os.path.join(self.project_folder, f'subtitles{ext}')
            shutil.copy2(subtitle_file, target_path)

            print(f"   ✅ 字幕文件")

        except Exception as e:
            print(f"   ⚠️  复制字幕失败: {str(e)}")

    def save_composition_log(self, log_data: Dict[str, Any]):
        """
        保存合成日志

        Args:
            log_data: 日志数据
        """
        print(f"\n📋 保存合成日志...")

        log_path = os.path.join(self.project_folder, 'composition_log.txt')

        lines = []
        lines.append("═" * 60)
        lines.append("    视频合成日志".center(60))
        lines.append("═" * 60)
        lines.append("")
        lines.append(f"合成时间: {log_data.get('timestamp', 'N/A')}")
        lines.append(f"视频时长: {log_data.get('duration', 0):.1f}秒")
        lines.append(f"片段数量: {log_data.get('segments', 0)}")
        lines.append("")

        # 配置信息
        if 'config' in log_data:
            config = log_data['config']
            lines.append("视频配置:")
            lines.append(f"  分辨率: {config.get('resolution', 'N/A')}")
            lines.append(f"  帧率: {config.get('fps', 'N/A')} fps")
            lines.append(f"  编码器: {config.get('codec', 'N/A')}")
            lines.append(f"  码率: {config.get('bitrate', 'N/A')}")
            lines.append("")

        # TTS信息
        if log_data.get('use_tts_audio'):
            lines.append("音频配置:")
            lines.append(f"  使用TTS: 是")
            lines.append(f"  BGM混音: {log_data.get('bgm_enabled', False)}")
            lines.append("")

        lines.append("═" * 60)

        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        print(f"   ✅ composition_log.txt")

    def generate_metadata(
        self,
        script: Dict[str, Any],
        video_stats: Dict[str, Any]
    ):
        """
        生成项目元数据

        Args:
            script: 脚本数据
            video_stats: 视频统计信息
        """
        metadata = {
            'project_name': os.path.basename(self.project_folder),
            'video_title': script.get('title', '未命名'),
            'created_at': datetime.now().isoformat(),
            'script_metadata': script.get('metadata', {}),
            'video_stats': video_stats,
            'project_structure': {
                'video': 'video.mp4',
                'script': 'script.json',
                'materials': 'materials/',
                'audio': 'audio/',
                'reports': [
                    'material_selection_report.json',
                    'material_selection_report.txt',
                    'composition_log.txt'
                ]
            }
        }

        metadata_path = os.path.join(self.project_folder, 'project_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def _get_score_level(self, score: float) -> str:
        """获取评分等级"""
        if score >= 80:
            return "优秀"
        elif score >= 60:
            return "良好"
        else:
            return "一般"
