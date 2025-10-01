#!/usr/bin/env python3
"""
素材库检查工具
检查素材库状态并提供建议
"""

import os
import json
from pathlib import Path


def check_material_directory():
    """检查素材目录"""
    print("=" * 60)
    print("📦 素材库检查工具")
    print("=" * 60)

    directories = {
        'images': 'materials/images',
        'videos': 'materials/videos',
        'audio': 'materials/audio'
    }

    total_count = 0
    results = {}

    for name, path in directories.items():
        if not os.path.exists(path):
            print(f"\n❌ {path} 目录不存在")
            results[name] = 0
            continue

        # 统计文件
        files = []
        extensions = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'videos': ['.mp4', '.avi', '.mov', '.mkv'],
            'audio': ['.mp3', '.wav', '.aac', '.flac']
        }

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions[name]:
                    files.append(file)

        count = len(files)
        results[name] = count
        total_count += count

        # 显示结果
        status = "✅" if count > 0 else "⚠️ "
        print(f"\n{status} {path}: {count} 个文件")

        if count > 0:
            # 显示前5个文件
            for i, file in enumerate(files[:5], 1):
                print(f"  {i}. {file}")
            if count > 5:
                print(f"  ... 还有 {count - 5} 个文件")

    # 总结
    print("\n" + "=" * 60)
    print(f"📊 总计: {total_count} 个素材文件")

    # 检查数据库
    print("\n📄 检查素材数据库...")
    if os.path.exists('data/materials.json'):
        try:
            with open('data/materials.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            db_count = len(data.get('materials', []))
            print(f"  ✓ 数据库中有 {db_count} 条素材记录")

            if db_count != total_count:
                print(f"  ⚠️  文件数({total_count})与数据库记录({db_count})不一致")
                print("     建议：运行菜单10（素材管理）重新索引")
        except Exception as e:
            print(f"  ❌ 读取数据库失败: {e}")
    else:
        print("  ⚠️  素材数据库不存在")
        print("     建议：运行 python init_data.py")

    # 评估和建议
    print("\n" + "=" * 60)
    print("💡 评估和建议:")

    if total_count == 0:
        print("\n❌ 素材库为空，无法生成视频")
        print("\n建议操作：")
        print("  1. 阅读 SETUP_MATERIALS.md 了解如何准备素材")
        print("  2. 从免费素材网站下载10-20张科普图片")
        print("  3. 将图片放入 materials/images/ 目录")
        print("  4. 运行 python main.py，选择菜单10添加素材")
        print("  5. 或使用菜单10的AI生成功能（需要API密钥）")

    elif total_count < 10:
        print("\n⚠️  素材数量较少，可能影响视频质量")
        print(f"\n当前: {total_count} 个素材")
        print("建议: 至少10-20个素材用于基础使用")
        print("\n快速补充素材：")
        print("  - 访问 unsplash.com 搜索科普主题")
        print("  - 下载1920x1080分辨率的图片")
        print("  - 或使用AI生成功能（菜单10）")

    elif total_count < 50:
        print("\n✅ 素材数量基本够用")
        print(f"\n当前: {total_count} 个素材")
        print("建议: 继续扩充到50+以支持更多主题")
        print("\n提示：")
        print("  - 为素材添加详细的标签")
        print("  - 覆盖多个科学领域")
        print("  - 包含一些抽象背景素材")

    else:
        print("\n🎉 素材库很丰富！")
        print(f"\n当前: {total_count} 个素材")
        print("您可以开始制作高质量视频了！")

    # 标签检查
    print("\n" + "=" * 60)
    print("🏷️  标签检查:")

    if os.path.exists('data/material_tags.json'):
        try:
            with open('data/material_tags.json', 'r', encoding='utf-8') as f:
                tags_data = json.load(f)
            tag_count = len(tags_data.get('tags', {}))

            if tag_count > 0:
                print(f"  ✓ 已有 {tag_count} 个标签")
                # 显示热门标签
                tags = tags_data.get('tags', {})
                sorted_tags = sorted(tags.items(), key=lambda x: len(x[1]), reverse=True)
                print("\n  热门标签:")
                for tag, materials in sorted_tags[:10]:
                    print(f"    - {tag}: {len(materials)} 个素材")
            else:
                print("  ⚠️  暂无标签")
                if total_count > 0:
                    print("     建议：为素材添加标签以提高推荐准确度")
        except Exception as e:
            print(f"  ❌ 读取标签失败: {e}")
    else:
        print("  ⚠️  标签数据库不存在")

    print("\n" + "=" * 60)
    print("检查完成！")
    print("=" * 60)


if __name__ == '__main__':
    check_material_directory()
