"""
素材管理器核心模块
负责素材的存储、检索、分类和管理
"""

import json
import os
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
from pathlib import Path


class MaterialManager:
    """素材管理器"""

    def __init__(self, data_dir: str = 'data', materials_dir: str = 'materials'):
        """
        初始化素材管理器

        Args:
            data_dir: 数据存储目录
            materials_dir: 素材存储目录
        """
        self.data_dir = data_dir
        self.materials_dir = materials_dir

        # 数据文件
        self.materials_db = os.path.join(data_dir, 'materials.json')
        self.tags_db = os.path.join(data_dir, 'tags.json')
        self.collections_db = os.path.join(data_dir, 'collections.json')

        # 素材类型目录
        self.image_dir = os.path.join(materials_dir, 'images')
        self.video_dir = os.path.join(materials_dir, 'videos')
        self.audio_dir = os.path.join(materials_dir, 'audio')

        # 初始化
        self._init_directories()
        self._init_databases()

    def _init_directories(self):
        """初始化目录结构"""
        for directory in [self.data_dir, self.image_dir, self.video_dir, self.audio_dir]:
            os.makedirs(directory, exist_ok=True)

    def _init_databases(self):
        """初始化数据库文件"""
        for db_file in [self.materials_db, self.tags_db, self.collections_db]:
            if not os.path.exists(db_file):
                with open(db_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)

    def add_material(
        self,
        file_path: str,
        material_type: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        添加素材到素材库

        Args:
            file_path: 源文件路径
            material_type: 素材类型 (image/video/audio)
            name: 素材名称
            description: 描述
            tags: 标签列表
            category: 分类
            metadata: 额外元数据

        Returns:
            素材ID
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 确定目标目录
        type_dirs = {
            'image': self.image_dir,
            'video': self.video_dir,
            'audio': self.audio_dir
        }

        if material_type not in type_dirs:
            raise ValueError(f"不支持的素材类型: {material_type}")

        target_dir = type_dirs[material_type]

        # 生成素材ID和文件名
        material_id = self._generate_material_id(file_path)
        file_ext = Path(file_path).suffix
        new_filename = f"{material_id}{file_ext}"
        target_path = os.path.join(target_dir, new_filename)

        # 复制文件
        shutil.copy2(file_path, target_path)

        # 获取文件信息
        file_stat = os.stat(target_path)

        # 创建素材记录
        material = {
            'id': material_id,
            'name': name or Path(file_path).stem,
            'type': material_type,
            'file_path': target_path,
            'file_name': new_filename,
            'file_size': file_stat.st_size,
            'file_ext': file_ext,
            'description': description or '',
            'tags': tags or [],
            'category': category or 'uncategorized',
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'used_count': 0,
            'rating': None
        }

        # 保存到数据库
        materials = self._load_json(self.materials_db)
        materials.append(material)
        self._save_json(self.materials_db, materials)

        # 更新标签索引
        if tags:
            self._update_tags(tags)

        print(f"✅ 素材已添加: {material['name']} (ID: {material_id})")
        return material_id

    def get_material(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        获取素材详情

        Args:
            material_id: 素材ID

        Returns:
            素材信息字典
        """
        materials = self._load_json(self.materials_db)
        for material in materials:
            if material['id'] == material_id:
                return material
        return None

    def list_materials(
        self,
        material_type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = 'date',
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        列出素材

        Args:
            material_type: 筛选类型
            category: 筛选分类
            tags: 筛选标签（包含任一标签即可）
            sort_by: 排序方式 (date/name/size/rating/usage)
            limit: 数量限制

        Returns:
            素材列表
        """
        materials = self._load_json(self.materials_db)

        # 筛选
        if material_type:
            materials = [m for m in materials if m['type'] == material_type]

        if category:
            materials = [m for m in materials if m['category'] == category]

        if tags:
            materials = [m for m in materials
                        if any(tag in m.get('tags', []) for tag in tags)]

        # 排序
        if sort_by == 'date':
            materials.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == 'name':
            materials.sort(key=lambda x: x.get('name', ''))
        elif sort_by == 'size':
            materials.sort(key=lambda x: x.get('file_size', 0), reverse=True)
        elif sort_by == 'rating':
            materials.sort(key=lambda x: x.get('rating') or 0, reverse=True)
        elif sort_by == 'usage':
            materials.sort(key=lambda x: x.get('used_count', 0), reverse=True)

        # 限制数量
        if limit:
            materials = materials[:limit]

        return materials

    def search_materials(
        self,
        keyword: str,
        search_in: List[str] = ['name', 'description', 'tags']
    ) -> List[Dict[str, Any]]:
        """
        搜索素材

        Args:
            keyword: 关键词
            search_in: 搜索范围

        Returns:
            匹配的素材列表
        """
        materials = self._load_json(self.materials_db)
        keyword_lower = keyword.lower()
        results = []

        for material in materials:
            match = False

            if 'name' in search_in and keyword_lower in material.get('name', '').lower():
                match = True

            if 'description' in search_in and keyword_lower in material.get('description', '').lower():
                match = True

            if 'tags' in search_in:
                tags_str = ' '.join(material.get('tags', [])).lower()
                if keyword_lower in tags_str:
                    match = True

            if match:
                results.append(material)

        return results

    def update_material(
        self,
        material_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        rating: Optional[int] = None
    ) -> bool:
        """
        更新素材信息

        Args:
            material_id: 素材ID
            name: 新名称
            description: 新描述
            tags: 新标签列表
            category: 新分类
            rating: 评分 (1-5)

        Returns:
            是否成功
        """
        materials = self._load_json(self.materials_db)

        for i, material in enumerate(materials):
            if material['id'] == material_id:
                if name is not None:
                    material['name'] = name
                if description is not None:
                    material['description'] = description
                if tags is not None:
                    material['tags'] = tags
                    self._update_tags(tags)
                if category is not None:
                    material['category'] = category
                if rating is not None:
                    if 1 <= rating <= 5:
                        material['rating'] = rating
                    else:
                        print("⚠️  评分必须在1-5之间")
                        return False

                material['updated_at'] = datetime.now().isoformat()
                materials[i] = material
                self._save_json(self.materials_db, materials)

                print(f"✅ 素材已更新: {material['name']}")
                return True

        print(f"❌ 未找到素材: {material_id}")
        return False

    def delete_material(self, material_id: str, delete_file: bool = True) -> bool:
        """
        删除素材

        Args:
            material_id: 素材ID
            delete_file: 是否同时删除文件

        Returns:
            是否成功
        """
        materials = self._load_json(self.materials_db)

        for i, material in enumerate(materials):
            if material['id'] == material_id:
                # 删除文件
                if delete_file and os.path.exists(material['file_path']):
                    os.remove(material['file_path'])
                    print(f"🗑️  文件已删除: {material['file_path']}")

                # 从数据库删除
                materials.pop(i)
                self._save_json(self.materials_db, materials)

                print(f"✅ 素材已删除: {material['name']}")
                return True

        print(f"❌ 未找到素材: {material_id}")
        return False

    def add_tags_to_material(self, material_id: str, tags: List[str]) -> bool:
        """
        为素材添加标签

        Args:
            material_id: 素材ID
            tags: 标签列表

        Returns:
            是否成功
        """
        material = self.get_material(material_id)
        if not material:
            return False

        current_tags = set(material.get('tags', []))
        current_tags.update(tags)

        return self.update_material(material_id, tags=list(current_tags))

    def remove_tags_from_material(self, material_id: str, tags: List[str]) -> bool:
        """
        从素材移除标签

        Args:
            material_id: 素材ID
            tags: 要移除的标签列表

        Returns:
            是否成功
        """
        material = self.get_material(material_id)
        if not material:
            return False

        current_tags = set(material.get('tags', []))
        current_tags.difference_update(tags)

        return self.update_material(material_id, tags=list(current_tags))

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """
        获取所有标签及其使用统计

        Returns:
            标签列表
        """
        return self._load_json(self.tags_db)

    def get_categories(self) -> Dict[str, int]:
        """
        获取所有分类及素材数量

        Returns:
            分类字典 {分类名: 数量}
        """
        materials = self._load_json(self.materials_db)
        categories = {}

        for material in materials:
            category = material.get('category', 'uncategorized')
            categories[category] = categories.get(category, 0) + 1

        return categories

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取素材库统计信息

        Returns:
            统计数据
        """
        materials = self._load_json(self.materials_db)

        total_size = sum(m.get('file_size', 0) for m in materials)
        type_stats = {}

        for material in materials:
            mat_type = material.get('type', 'unknown')
            if mat_type not in type_stats:
                type_stats[mat_type] = {'count': 0, 'size': 0}
            type_stats[mat_type]['count'] += 1
            type_stats[mat_type]['size'] += material.get('file_size', 0)

        return {
            'total_materials': len(materials),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_type': type_stats,
            'categories': self.get_categories(),
            'total_tags': len(self.get_all_tags()),
            'last_updated': datetime.now().isoformat()
        }

    def increment_usage(self, material_id: str):
        """
        增加素材使用次数

        Args:
            material_id: 素材ID
        """
        materials = self._load_json(self.materials_db)

        for i, material in enumerate(materials):
            if material['id'] == material_id:
                material['used_count'] = material.get('used_count', 0) + 1
                materials[i] = material
                self._save_json(self.materials_db, materials)
                break

    def _generate_material_id(self, file_path: str) -> str:
        """生成素材ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"mat_{timestamp}_{file_hash}"

    def _update_tags(self, tags: List[str]):
        """更新标签索引"""
        tag_db = self._load_json(self.tags_db)
        tag_dict = {tag['name']: tag for tag in tag_db}

        for tag in tags:
            if tag in tag_dict:
                tag_dict[tag]['count'] += 1
                tag_dict[tag]['last_used'] = datetime.now().isoformat()
            else:
                tag_dict[tag] = {
                    'name': tag,
                    'count': 1,
                    'created_at': datetime.now().isoformat(),
                    'last_used': datetime.now().isoformat()
                }

        tag_list = sorted(tag_dict.values(), key=lambda x: x['count'], reverse=True)
        self._save_json(self.tags_db, tag_list)

    def _load_json(self, file_path: str) -> List:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, file_path: str, data: List):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
