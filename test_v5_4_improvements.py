#!/usr/bin/env python3
"""
V5.4改进测试脚本
测试视频时长同步、智能剪辑、素材匹配等功能
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

# 使用importlib动态加载模块（避免命名冲突）
import importlib.util

# 加载VideoComposer
composer_path = os.path.join(os.path.dirname(__file__), 'scripts', '3_video_editor', 'composer.py')
spec = importlib.util.spec_from_file_location("video_composer", composer_path)
video_composer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video_composer_module)
VideoComposer = video_composer_module.VideoComposer

def test_material_recommendations():
    """测试素材推荐功能"""
    print("\n" + "="*80)
    print("📋 测试1: 素材推荐功能")
    print("="*80)

    # 加载测试脚本
    script_path = '/home/wengfb/make-video/output/scripts/20251002_213924_黑洞如何扭曲时空爱因斯坦的宇宙魔法.json'

    if not os.path.exists(script_path):
        print("❌ 测试脚本不存在，跳过测试")
        return False

    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)

    # 创建VideoComposer实例
    composer = VideoComposer()

    # 测试素材推荐预览
    try:
        recommendations = composer.preview_material_recommendations(script)
        print(f"\n✅ 素材推荐测试通过")
        print(f"   - 推荐了 {len(recommendations)} 个章节的素材")
        return True
    except Exception as e:
        print(f"❌ 素材推荐测试失败: {str(e)}")
        return False


def test_tts_duration_sync():
    """测试TTS时长同步"""
    print("\n" + "="*80)
    print("📋 测试2: TTS时长同步")
    print("="*80)

    # 创建测试脚本和TTS元数据
    test_script = {
        "title": "测试视频-TTS时长同步",
        "sections": [
            {
                "section_name": "片段1",
                "narration": "这是第一段测试语音",
                "visual_notes": "测试场景",
                "duration": 5.0  # 脚本中的时长
            },
            {
                "section_name": "片段2",
                "narration": "这是第二段测试语音",
                "visual_notes": "测试场景2",
                "duration": 5.0
            }
        ]
    }

    # 模拟TTS元数据（实际时长不同）
    test_tts_metadata = {
        "audio_files": [
            {
                "file_path": "/home/wengfb/make-video/materials/audio/test1.mp3",
                "duration": 3.5  # 实际TTS时长
            },
            {
                "file_path": "/home/wengfb/make-video/materials/audio/test2.mp3",
                "duration": 7.2  # 实际TTS时长
            }
        ]
    }

    # 保存测试文件
    test_tts_path = '/tmp/test_tts_metadata.json'
    with open(test_tts_path, 'w', encoding='utf-8') as f:
        json.dump(test_tts_metadata, f, ensure_ascii=False, indent=2)

    composer = VideoComposer()

    # 测试_build_segments方法
    try:
        section_materials = {
            0: (None, None),
            1: (None, None)
        }

        # 提取TTS时长
        tts_durations = [item['duration'] for item in test_tts_metadata['audio_files']]

        segments = composer._build_segments(
            sections=test_script['sections'],
            section_materials=section_materials,
            tts_durations=tts_durations
        )

        print(f"\n✅ TTS时长同步测试通过")
        print(f"   片段1: 脚本时长={test_script['sections'][0]['duration']}秒, "
              f"实际使用={segments[0].duration}秒 (TTS={tts_durations[0]}秒)")
        print(f"   片段2: 脚本时长={test_script['sections'][1]['duration']}秒, "
              f"实际使用={segments[1].duration}秒 (TTS={tts_durations[1]}秒)")

        # 验证是否使用了TTS时长
        if segments[0].duration == tts_durations[0] and segments[1].duration == tts_durations[1]:
            print("   ✅ 确认使用TTS时长而非脚本时长")
            return True
        else:
            print("   ⚠️  未正确使用TTS时长")
            return False

    except Exception as e:
        print(f"❌ TTS时长同步测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_tts_path):
            os.remove(test_tts_path)


def test_config_loading():
    """测试配置加载"""
    print("\n" + "="*80)
    print("📋 测试3: 配置加载")
    print("="*80)

    try:
        with open('config/settings.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 检查新配置项
        video_config = config.get('video', {})

        checks = [
            ('use_tts_duration', video_config.get('use_tts_duration')),
            ('default_image_duration', video_config.get('default_image_duration')),
            ('show_narration_text', video_config.get('show_narration_text', True)),
        ]

        print("\n✅ 配置文件加载成功")
        for key, value in checks:
            print(f"   - {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("🧪 V5.4改进功能测试套件")
    print("="*80)

    results = []

    # 测试1: 配置加载
    results.append(("配置加载", test_config_loading()))

    # 测试2: TTS时长同步
    results.append(("TTS时长同步", test_tts_duration_sync()))

    # 测试3: 素材推荐
    results.append(("素材推荐", test_material_recommendations()))

    # 总结
    print("\n" + "="*80)
    print("📊 测试结果总结")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！V5.4改进功能正常工作")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
