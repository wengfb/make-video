#!/usr/bin/env python3
"""
批量标签重构脚本（V5.5）
重构现有素材的标签系统，从长短语标签改为智能拆分标签

使用方法:
    python3 scripts/tools/rebuild_material_tags.py [--dry-run]

选项:
    --dry-run: 只显示将要进行的更改，不实际修改
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# 导入MaterialManager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '2_material_manager'))
from manager import MaterialManager


class MaterialTagsRebuilder:
    """素材标签重构器"""

    def __init__(self):
        self.manager = MaterialManager()
        self.stats = {
            'total': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }

    def _generate_smart_tags(self, keyword: str, material_type: str) -> List[str]:
        """
        生成智能标签（与recommender.py中的方法相同）
        """
        tags = []

        # 1. 拆分为独立单词
        words = [w.strip().lower() for w in keyword.split() if w.strip()]
        tags.extend(list(set(words)))

        # 2. 添加双词组合
        if len(words) >= 2:
            for i in range(len(words) - 1):
                combined = f"{words[i]}_{words[i+1]}"
                tags.append(combined)

        # 3. 添加合并词
        if len(words) >= 2:
            tags.append(''.join(words[:2]))

        # 4. 自动分类标签
        category_keywords = {
            'astronomy': ['space', 'star', 'galaxy', 'planet', 'asteroid', 'comet', 'nebula',
                         'black', 'hole', 'sun', 'moon', 'cosmos', 'universe', 'stellar'],
            'biology': ['brain', 'neuron', 'cell', 'DNA', 'gene', 'protein', 'organism',
                       'bacteria', 'virus', 'blood', 'heart', 'organ', 'tissue'],
            'physics': ['atom', 'quantum', 'particle', 'energy', 'wave', 'field',
                       'relativity', 'gravity', 'force', 'motion'],
            'chemistry': ['molecule', 'chemical', 'reaction', 'element', 'compound',
                         'bond', 'acid', 'base'],
            'environment': ['climate', 'weather', 'earth', 'ocean', 'forest', 'pollution',
                           'ecosystem', 'carbon', 'greenhouse', 'renewable'],
            'technology': ['computer', 'robot', 'AI', 'digital', 'network', 'data',
                          'algorithm', 'software']
        }

        matched_categories = []
        for category, keywords_list in category_keywords.items():
            if any(kw in keyword.lower() for kw in keywords_list):
                matched_categories.append(category)
                tags.append(category)

        if matched_categories:
            tags.append('science')

        # 5. 添加视觉特征标签
        visual_keywords = {
            'animation': ['animation', 'animated', 'motion'],
            'abstract': ['abstract', 'pattern', 'texture'],
            'macro': ['macro', 'microscopic', 'close-up', 'micro'],
            'aerial': ['aerial', 'drone', 'bird-eye', 'top-view'],
            'timelapse': ['timelapse', 'time-lapse', 'fast']
        }

        for feature, feature_keywords in visual_keywords.items():
            if any(kw in keyword.lower() for kw in feature_keywords):
                tags.append(feature)

        # 6. 添加类型标签
        tags.append(material_type)

        # 7. 去重并返回
        return list(set(tags))

    def _extract_original_keyword(self, old_tags: List[str]) -> str:
        """
        从旧标签中提取原始搜索关键词

        Args:
            old_tags: 旧标签列表

        Returns:
            原始搜索关键词
        """
        # 跳过无意义标签
        skip_tags = ['pexels', 'HD', 'unsplash', 'hd', 'video', 'image']

        for tag in old_tags:
            if tag and tag.lower() not in skip_tags:
                return tag

        return "science education"  # 默认

    def rebuild_single_material(self, material: Dict[str, Any], dry_run: bool = False) -> bool:
        """
        重构单个素材的标签

        Args:
            material: 素材数据
            dry_run: 是否为干运行

        Returns:
            是否成功
        """
        material_id = material.get('id')
        material_name = material.get('name', 'N/A')
        material_type = material.get('type', 'image')
        old_tags = material.get('tags', [])

        # 提取原始关键词
        original_keyword = self._extract_original_keyword(old_tags)

        # 生成新标签
        new_tags = self._generate_smart_tags(original_keyword, material_type)

        # 显示对比
        print(f"\n素材: {material_name}")
        print(f"  类型: {material_type}")
        print(f"  原始关键词: {original_keyword}")
        print(f"  旧标签 ({len(old_tags)}): {old_tags[:3]}...")
        print(f"  新标签 ({len(new_tags)}): {new_tags[:10]}...")

        if dry_run:
            print("  [DRY-RUN] 跳过实际更新")
            return True

        # 实际更新
        try:
            self.manager.update_material(material_id, tags=new_tags)
            print("  ✅ 更新成功")
            return True
        except Exception as e:
            print(f"  ❌ 更新失败: {str(e)}")
            return False

    def rebuild_all(self, dry_run: bool = False):
        """
        重构所有素材的标签

        Args:
            dry_run: 是否为干运行（不实际修改）
        """
        print("="*80)
        print("📦 素材标签批量重构工具 V5.5")
        print("="*80)

        if dry_run:
            print("\n⚠️  DRY-RUN模式：只显示更改，不实际修改")

        # 备份数据
        if not dry_run:
            print("\n💾 备份当前数据...")
            backup_path = self._backup_materials()
            print(f"   备份文件: {backup_path}")

        # 加载所有素材
        materials = self.manager.list_materials()
        self.stats['total'] = len(materials)

        print(f"\n📊 找到 {self.stats['total']} 个素材")
        print(f"   开始重构标签...\n")

        # 逐个处理
        for i, material in enumerate(materials, 1):
            print(f"\n[{i}/{self.stats['total']}]", end=' ')

            # 检查是否已经是新格式
            old_tags = material.get('tags', [])
            if self._is_new_format(old_tags):
                print(f"素材 {material.get('name', 'N/A')} - 已是新格式，跳过")
                self.stats['skipped'] += 1
                continue

            # 重构标签
            success = self.rebuild_single_material(material, dry_run)

            if success:
                self.stats['updated'] += 1
            else:
                self.stats['errors'] += 1

        # 显示统计
        self._print_summary(dry_run)

    def _is_new_format(self, tags: List[str]) -> bool:
        """
        判断标签是否已经是新格式

        新格式特征:
        - 没有"pexels"、"HD"标签
        - 有多个独立单词标签
        - 有分类标签（astronomy等）
        """
        if 'pexels' in tags or 'HD' in tags:
            return False

        # 有下划线组合词
        if any('_' in tag for tag in tags):
            return True

        # 有分类标签
        category_tags = ['astronomy', 'biology', 'physics', 'chemistry',
                         'environment', 'technology', 'science']
        if any(cat in tags for cat in category_tags):
            return True

        return False

    def _backup_materials(self) -> str:
        """
        备份materials.json

        Returns:
            备份文件路径
        """
        materials_path = 'data/materials.json'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'data/materials.json.backup_{timestamp}_tag_rebuild'

        with open(materials_path, 'r', encoding='utf-8') as f:
            data = f.read()

        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(data)

        return backup_path

    def _print_summary(self, dry_run: bool):
        """打印统计摘要"""
        print("\n" + "="*80)
        print("📊 重构完成统计")
        print("="*80)
        print(f"总素材数: {self.stats['total']}")
        print(f"已更新: {self.stats['updated']}")
        print(f"已跳过: {self.stats['skipped']} (已是新格式)")
        print(f"失败: {self.stats['errors']}")

        if dry_run:
            print("\n⚠️  这是DRY-RUN模式，未实际修改数据")
            print("   移除--dry-run参数以执行实际更新")
        else:
            print("\n✅ 标签重构完成！")

            if self.stats['updated'] > 0:
                print("\n💡 建议:")
                print("   1. 检查data/materials.json确认更新")
                print("   2. 测试素材推荐功能")
                print("   3. 如有问题，可从备份恢复")


def main():
    """主函数"""
    # 检查命令行参数
    dry_run = '--dry-run' in sys.argv

    # 创建重构器并执行
    rebuilder = MaterialTagsRebuilder()
    rebuilder.rebuild_all(dry_run=dry_run)


if __name__ == "__main__":
    main()
