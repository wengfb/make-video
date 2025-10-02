#!/usr/bin/env python3
"""
素材库扫描器
扫描materials/目录并注册未注册的素材到materials.json
"""

import os
from pathlib import Path
from typing import List, Dict
from manager import MaterialManager


class MaterialScanner:
    """素材库扫描器类"""

    def __init__(self, materials_dir: str = "materials"):
        """
        初始化扫描器

        Args:
            materials_dir: 素材目录路径
        """
        self.materials_dir = Path(materials_dir)
        self.manager = MaterialManager()

        # 支持的文件类型
        self.image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        self.audio_exts = {'.mp3', '.wav', '.aac', '.ogg', '.m4a'}

    def scan_directory(self, directory: Path = None) -> List[Path]:
        """
        扫描目录下的所有素材文件

        Args:
            directory: 要扫描的目录，默认为materials/

        Returns:
            文件路径列表
        """
        if directory is None:
            directory = self.materials_dir

        files = []
        all_exts = self.image_exts | self.video_exts | self.audio_exts

        # 递归扫描所有子目录
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                filepath = Path(root) / filename
                ext = filepath.suffix.lower()

                # 跳过隐藏文件和特殊文件
                if filename.startswith('.') or filename == 'gitkeep':
                    continue

                # 只处理支持的文件类型
                if ext in all_exts:
                    files.append(filepath)

        return files

    def get_material_type(self, filepath: Path) -> str:
        """
        根据文件扩展名确定素材类型

        Args:
            filepath: 文件路径

        Returns:
            素材类型 (image/video/audio)
        """
        ext = filepath.suffix.lower()

        if ext in self.image_exts:
            return 'image'
        elif ext in self.video_exts:
            return 'video'
        elif ext in self.audio_exts:
            return 'audio'
        else:
            return 'unknown'

    def extract_tags_from_path(self, filepath: Path) -> List[str]:
        """
        从文件路径和文件名中提取标签

        Args:
            filepath: 文件路径

        Returns:
            标签列表
        """
        tags = []

        # 从父目录名提取标签
        parent_dirs = filepath.parts
        for part in parent_dirs:
            if part in ['materials', 'images', 'videos', 'audio', 'tts']:
                continue
            # 添加目录名作为标签
            tags.append(part)

        # 从文件名提取标签（去除ID部分）
        filename = filepath.stem  # 不含扩展名
        # 分割文件名（假设格式: keyword_id 或 keyword_phrase）
        parts = filename.split('_')

        # 提取有意义的关键词部分（通常在ID之前）
        for part in parts:
            # 跳过纯数字（可能是ID）
            if part.isdigit():
                continue
            # 添加有意义的词作为标签
            if len(part) > 2:  # 跳过太短的词
                tags.append(part)

        # 去重
        return list(set(tags))

    def find_unregistered_materials(self) -> List[Dict]:
        """
        查找未注册的素材文件

        Returns:
            未注册素材信息列表
        """
        # 扫描所有文件
        all_files = self.scan_directory()

        # 获取已注册的素材
        registered_materials = self.manager.list_materials()
        registered_paths = {m['file_path'] for m in registered_materials}

        # 找出未注册的文件
        unregistered = []
        for filepath in all_files:
            filepath_str = str(filepath)

            # 检查是否已注册
            if filepath_str not in registered_paths:
                material_type = self.get_material_type(filepath)
                tags = self.extract_tags_from_path(filepath)

                unregistered.append({
                    'file_path': filepath_str,
                    'name': filepath.stem,
                    'type': material_type,
                    'tags': tags
                })

        return unregistered

    def register_materials(self, materials: List[Dict]) -> int:
        """
        批量注册素材

        Args:
            materials: 素材信息列表

        Returns:
            成功注册的数量
        """
        count = 0

        for material in materials:
            try:
                self.manager.add_material(
                    name=material['name'],
                    file_path=material['file_path'],
                    material_type=material['type'],
                    tags=material['tags'],
                    description=f"自动扫描: {material['name']}"
                )
                count += 1
            except Exception as e:
                print(f"⚠️  注册失败 {material['name']}: {str(e)}")

        return count

    def scan_and_register_all(self, dry_run: bool = False) -> Dict:
        """
        扫描并注册所有未注册的素材（一站式）

        Args:
            dry_run: 如果为True，只显示扫描结果不实际注册

        Returns:
            扫描结果统计
        """
        print("\n🔍 正在扫描素材库...")
        print(f"📁 扫描目录: {self.materials_dir}")

        # 查找未注册的素材
        unregistered = self.find_unregistered_materials()

        # 统计
        type_counts = {'image': 0, 'video': 0, 'audio': 0, 'unknown': 0}
        for mat in unregistered:
            mat_type = mat['type']
            type_counts[mat_type] = type_counts.get(mat_type, 0) + 1

        print(f"\n📊 扫描结果:")
        print(f"   未注册素材总数: {len(unregistered)}")
        print(f"   - 图片: {type_counts['image']}")
        print(f"   - 视频: {type_counts['video']}")
        print(f"   - 音频: {type_counts['audio']}")

        if not unregistered:
            print("\n✅ 所有素材已注册！")
            return {'total': 0, 'registered': 0}

        # 显示前10个未注册的素材
        if len(unregistered) > 0:
            print(f"\n未注册素材示例 (前10个):")
            for i, mat in enumerate(unregistered[:10], 1):
                print(f"   {i}. [{mat['type']}] {mat['name']}")
                print(f"      标签: {', '.join(mat['tags'][:5])}")

        if dry_run:
            print("\n💡 这是预览模式，未实际注册。使用 dry_run=False 进行实际注册。")
            return {'total': len(unregistered), 'registered': 0}

        # 实际注册
        print(f"\n⏳ 正在注册 {len(unregistered)} 个素材...")
        registered_count = self.register_materials(unregistered)

        print(f"\n✅ 完成！成功注册 {registered_count}/{len(unregistered)} 个素材")

        return {
            'total': len(unregistered),
            'registered': registered_count,
            'by_type': type_counts
        }


def main():
    """命令行工具入口"""
    import sys

    scanner = MaterialScanner()

    # 检查命令行参数
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv

    if dry_run:
        print("🔍 预览模式: 只扫描不注册\n")

    result = scanner.scan_and_register_all(dry_run=dry_run)

    print("\n" + "=" * 60)
    print(f"📈 最终统计:")
    print(f"   扫描到的未注册素材: {result['total']}")
    print(f"   成功注册的素材: {result['registered']}")
    print("=" * 60)


if __name__ == '__main__':
    main()
