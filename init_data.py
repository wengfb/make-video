#!/usr/bin/env python3
"""
数据初始化脚本
创建必要的数据文件和目录结构
"""

import json
import os
from pathlib import Path


def init_directories():
    """初始化目录结构"""
    directories = [
        'data',
        'materials/images',
        'materials/videos',
        'materials/audio',
        'materials/audio/tts',
        'materials/fonts',
        'output/scripts',
        'output/videos',
        'output/subtitles',
        'templates'
    ]

    print("📁 创建目录结构...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")


def init_data_files():
    """初始化数据文件"""
    data_files = {
        'data/topics.json': {
            "topics": [],
            "metadata": {
                "total_count": 0,
                "created_at": "2025-01-01T00:00:00",
                "last_updated": "2025-01-01T00:00:00"
            }
        },
        'data/favorites.json': {
            "favorites": [],
            "metadata": {
                "total_count": 0
            }
        },
        'data/materials.json': {
            "materials": [],
            "metadata": {
                "total_count": 0,
                "last_updated": "2025-01-01T00:00:00"
            }
        },
        'data/material_tags.json': {
            "tags": {},
            "metadata": {
                "total_tags": 0
            }
        },
        'data/collections.json': {
            "collections": [],
            "metadata": {
                "total_count": 0
            }
        },
        'data/tts_audio.json': {
            "audio_files": [],
            "metadata": {
                "total_count": 0,
                "total_duration": 0
            }
        }
    }

    print("\n📄 创建数据文件...")
    for file_path, content in data_files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            print(f"  ✓ {file_path}")
        else:
            print(f"  ⊙ {file_path} (已存在)")


def check_config():
    """检查配置文件"""
    print("\n⚙️  检查配置文件...")

    if not os.path.exists('config/settings.json'):
        print("  ⚠️  config/settings.json 不存在")
        print("  💡 请复制 config/settings.example.json 为 config/settings.json")
        print("     并配置您的API密钥")
        return False
    else:
        print("  ✓ config/settings.json 存在")

        # 检查API密钥
        try:
            with open('config/settings.json', 'r', encoding='utf-8') as f:
                config = json.load(f)

            api_key = config.get('ai', {}).get('api_key', '')
            if not api_key or api_key == 'YOUR_API_KEY_HERE':
                print("  ⚠️  API密钥未配置")
                print("     请在 config/settings.json 中设置 ai.api_key")
                return False
            else:
                print("  ✓ API密钥已配置")

        except Exception as e:
            print(f"  ❌ 读取配置文件失败: {e}")
            return False

    return True


def create_example_data():
    """创建示例数据（可选）"""
    print("\n📝 是否创建示例数据？(y/n): ", end='')
    choice = input().strip().lower()

    if choice != 'y':
        print("  跳过示例数据创建")
        return

    # 创建示例主题
    example_topic = {
        "id": "example-001",
        "title": "量子计算的奇妙世界",
        "description": "探索量子计算的基本原理和未来应用",
        "field": "物理学",
        "audience": "大众",
        "difficulty": "medium",
        "keywords": ["量子计算", "量子比特", "叠加态", "纠缠"],
        "rating": 5,
        "created_at": "2025-01-01T00:00:00",
        "is_favorite": False
    }

    try:
        with open('data/topics.json', 'r', encoding='utf-8') as f:
            topics_data = json.load(f)

        topics_data['topics'].append(example_topic)
        topics_data['metadata']['total_count'] = 1

        with open('data/topics.json', 'w', encoding='utf-8') as f:
            json.dump(topics_data, f, ensure_ascii=False, indent=2)

        print("  ✓ 已创建示例主题")
    except Exception as e:
        print(f"  ❌ 创建示例数据失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 科普视频制作系统 - 数据初始化")
    print("=" * 60)

    # 1. 创建目录
    init_directories()

    # 2. 创建数据文件
    init_data_files()

    # 3. 检查配置
    config_ok = check_config()

    # 4. 创建示例数据（可选）
    create_example_data()

    print("\n" + "=" * 60)
    if config_ok:
        print("✅ 初始化完成！您可以运行 python main.py 启动程序")
    else:
        print("⚠️  初始化完成，但需要配置API密钥才能使用")
        print("   请编辑 config/settings.json 并设置您的OpenAI API密钥")
    print("=" * 60)


if __name__ == '__main__':
    main()
