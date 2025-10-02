#!/usr/bin/env python3
"""
测试视频生成功能
使用最近生成的脚本来测试视频合成
"""

import os
import json
import sys
import importlib.util

def load_module(module_name, file_path):
    """动态加载模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_video_generation():
    """测试视频生成"""

    print("=" * 70)
    print("🎬 测试视频生成功能")
    print("=" * 70)

    # 查找最新的脚本文件
    script_dir = 'output/scripts'
    script_files = [f for f in os.listdir(script_dir) if f.endswith('.json')]

    if not script_files:
        print("❌ 没有找到脚本文件")
        return False

    # 使用最新的脚本
    script_files.sort(reverse=True)
    script_file = os.path.join(script_dir, script_files[0])

    print(f"\n📄 使用脚本: {script_files[0]}")

    # 读取脚本
    with open(script_file, 'r', encoding='utf-8') as f:
        script = json.load(f)

    print(f"   标题: {script.get('title', '未命名')}")
    print(f"   章节数: {len(script.get('sections', []))}")
    print(f"   预计时长: {script.get('total_duration', 'N/A')}秒")

    # 初始化VideoComposer
    print("\n⏳ 初始化视频合成器...")
    composer_module = load_module(
        'composer',
        'scripts/3_video_editor/composer.py'
    )

    composer = composer_module.VideoComposer('config/settings.json')
    print("   ✅ 视频合成器已初始化")

    # 测试合成信息
    print("\n📊 获取合成信息...")
    try:
        info = composer.get_composition_info(script)
        print(f"   标题: {info['title']}")
        print(f"   总章节数: {info['total_sections']}")
        print(f"   预计时长: {info['estimated_duration']:.1f}秒")
        print(f"   预计文件大小: {info['estimated_file_size_mb']}MB")
    except Exception as e:
        print(f"   ⚠️  获取合成信息失败: {str(e)}")

    # 测试素材推荐预览
    print("\n🔍 预览素材推荐...")
    try:
        recommendations = composer.preview_material_recommendations(script)
        print(f"   ✅ 为 {len(recommendations)} 个章节生成了素材推荐")

        # 显示第一个章节的推荐
        if recommendations:
            first_rec = recommendations[0]
            print(f"\n   示例 - {first_rec['section_name']}:")
            if first_rec['recommendations']:
                top_rec = first_rec['recommendations'][0]
                print(f"      推荐: {top_rec['name']}")
                print(f"      匹配度: {top_rec['match_score']:.0f}%")
    except Exception as e:
        print(f"   ⚠️  素材推荐预览失败: {str(e)}")

    # 测试实际视频合成（简短版本）
    print("\n🎬 开始视频合成测试...")
    print("   提示: 这可能需要几分钟时间...")

    # 创建一个简短版本的脚本（只使用前2个章节）
    short_script = script.copy()
    short_script['sections'] = script['sections'][:2]
    short_script['title'] = f"{script.get('title', '测试视频')}_短版测试"

    print(f"   使用前 {len(short_script['sections'])} 个章节进行测试")

    try:
        video_path = composer.compose_from_script(
            script=short_script,
            auto_select_materials=True,
            output_filename=f"test_video_{script_files[0].replace('.json', '.mp4')}"
        )

        print(f"\n✅ 视频生成成功!")
        print(f"   输出路径: {video_path}")

        # 检查文件是否存在
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path) / (1024 * 1024)
            print(f"   文件大小: {file_size:.2f}MB")
            return True
        else:
            print(f"   ⚠️  视频文件未找到")
            return False

    except Exception as e:
        print(f"\n❌ 视频生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🧪 视频生成功能测试")
    print("=" * 70 + "\n")

    success = test_video_generation()

    print("\n" + "=" * 70)
    if success:
        print("✅ 测试通过!")
    else:
        print("❌ 测试失败")
    print("=" * 70 + "\n")

    sys.exit(0 if success else 1)
