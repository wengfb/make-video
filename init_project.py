#!/usr/bin/env python3
"""
项目初始化脚本
创建必要的目录结构和数据文件
"""

import os
import json
from pathlib import Path


def init_project():
    """初始化项目目录结构和数据文件"""
    print("🚀 开始初始化项目...")
    print("=" * 60)

    # 定义目录结构
    directories = [
        "data",
        "materials/images",
        "materials/videos",
        "materials/audio",
        "materials/audio/tts",
        "output/scripts",
        "output/videos",
        "output/subtitles",
        "config"
    ]

    # 创建目录
    print("\n📁 创建目录结构...")
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ 创建: {directory}")
        else:
            print(f"  ⏭️  已存在: {directory}")

    # 初始化数据文件
    print("\n📄 初始化数据文件...")
    data_files = {
        "data/topics.json": [],
        "data/materials.json": [],
        "data/tags.json": [],
        "data/collections.json": [],
        "data/costs.json": {
            "total_cost": 0.0,
            "sessions": [],
            "last_updated": None
        }
    }

    for file_path, initial_data in data_files.items():
        path = Path(file_path)
        if not path.exists():
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            print(f"  ✅ 创建: {file_path}")
        else:
            print(f"  ⏭️  已存在: {file_path}")

    # 检查配置文件
    print("\n⚙️  检查配置文件...")
    config_path = Path("config/settings.json")
    example_config_path = Path("config/settings.example.json")

    if not config_path.exists():
        if example_config_path.exists():
            print(f"  ⚠️  未找到 config/settings.json")
            print(f"  💡 请复制 config/settings.example.json 为 config/settings.json")
            print(f"     并配置您的 API 密钥")
        else:
            print(f"  ❌ 缺少配置文件模板")
    else:
        print(f"  ✅ 配置文件已存在")

        # 验证配置文件格式
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 检查关键配置项
            api_key = config.get('ai', {}).get('api_key', '')
            if api_key == 'YOUR_API_KEY_HERE' or not api_key:
                print(f"  ⚠️  请配置您的 OpenAI API 密钥")
            else:
                print(f"  ✅ API 密钥已配置")

        except json.JSONDecodeError:
            print(f"  ❌ 配置文件格式错误，请检查 JSON 语法")
        except Exception as e:
            print(f"  ⚠️  配置文件验证失败: {str(e)}")

    # 创建 .gitignore (如果不存在)
    print("\n📝 检查 .gitignore...")
    gitignore_path = Path(".gitignore")
    gitignore_content = """# 配置文件 (包含API密钥)
config/settings.json

# 数据文件
data/
materials/
output/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 系统文件
.DS_Store
Thumbs.db
"""

    if not gitignore_path.exists():
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print(f"  ✅ 创建 .gitignore")
    else:
        print(f"  ⏭️  .gitignore 已存在")

    # 完成
    print("\n" + "=" * 60)
    print("✅ 项目初始化完成!")
    print("\n📋 下一步:")
    print("  1. 配置 config/settings.json 中的 API 密钥")
    print("  2. 安装依赖: pip install -r requirements.txt")
    print("  3. 检查依赖: python scripts/utils/dependency_checker.py")
    print("  4. 运行程序: python main.py")
    print("\n💡 提示: 首次运行建议先生成一些测试素材")
    print("=" * 60)


def check_initialization():
    """
    检查项目是否已初始化

    Returns:
        bool: 如果已初始化返回True，否则返回False
    """
    required_dirs = ["data", "materials", "output"]
    required_files = ["data/topics.json", "data/materials.json"]

    # 检查目录
    for directory in required_dirs:
        if not Path(directory).exists():
            return False

    # 检查文件
    for file_path in required_files:
        if not Path(file_path).exists():
            return False

    return True


if __name__ == "__main__":
    init_project()
