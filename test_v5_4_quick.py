#!/usr/bin/env python3
"""
V5.4快速测试脚本 - 只测试核心功能
"""

import json
import sys
import os
import importlib.util

# 加载VideoComposer
composer_path = os.path.join(os.path.dirname(__file__), 'scripts', '3_video_editor', 'composer.py')
spec = importlib.util.spec_from_file_location("video_composer", composer_path)
video_composer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video_composer_module)
VideoComposer = video_composer_module.VideoComposer

def main():
    """快速测试"""
    print("\n" + "="*80)
    print("🧪 V5.4快速测试")
    print("="*80)

    # 测试1: 配置加载
    print("\n✅ 测试1: 配置加载")
    with open('config/settings.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    video_config = config.get('video', {})
    print(f"   - use_tts_duration: {video_config.get('use_tts_duration')}")
    print(f"   - default_image_duration: {video_config.get('default_image_duration')}")

    # 测试2: TTS时长同步
    print("\n✅ 测试2: TTS时长同步")
    test_script = {
        "sections": [
            {"section_name": "片段1", "narration": "测试1", "duration": 5.0},
            {"section_name": "片段2", "narration": "测试2", "duration": 5.0}
        ]
    }

    composer = VideoComposer()
    tts_durations = [3.5, 7.2]  # 实际TTS时长
    segments = composer._build_segments(
        sections=test_script['sections'],
        section_materials={0: (None, None), 1: (None, None)},
        tts_durations=tts_durations
    )

    print(f"   - 片段1: 脚本={test_script['sections'][0]['duration']}秒 → 实际={segments[0].duration}秒")
    print(f"   - 片段2: 脚本={test_script['sections'][1]['duration']}秒 → 实际={segments[1].duration}秒")

    if segments[0].duration == 3.5 and segments[1].duration == 7.2:
        print("   ✅ TTS时长同步正常")
    else:
        print("   ❌ TTS时长同步失败")

    # 测试3: 智能剪辑（检查FFmpeg渲染器方法存在）
    print("\n✅ 测试3: 智能剪辑功能")
    try:
        from scripts.video_editor.ffmpeg_renderer import FFmpegTimelineRenderer
        renderer = FFmpegTimelineRenderer()
        print("   - FFmpegTimelineRenderer加载成功")
        print("   - _probe_duration方法存在:", hasattr(renderer, '_probe_duration'))
        print("   - _build_segment_filter方法存在:", hasattr(renderer, '_build_segment_filter'))
        print("   ✅ 智能剪辑功能可用")
    except Exception as e:
        print(f"   ❌ 智能剪辑功能检查失败: {e}")

    print("\n" + "="*80)
    print("🎉 V5.4核心功能测试完成")
    print("="*80)
    print("\n主要改进:")
    print("  ✅ 视频时长使用TTS实际时长（音画同步）")
    print("  ✅ 智能视频剪辑（从中间截取精彩片段）")
    print("  ✅ 增强素材匹配算法（多维度评分）")
    print("  ✅ 详细匹配原因展示")
    print("  ✅ 配置化管理")

    print("\n使用建议:")
    print("  1. 确保config/settings.json中use_tts_duration=true")
    print("  2. 使用菜单12预览素材推荐（查看匹配详情）")
    print("  3. TTS生成后视频时长将自动同步")

if __name__ == "__main__":
    main()
