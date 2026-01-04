"""
素材服务
封装MaterialManager，提供Web界面使用的业务逻辑
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from web.utils.module_loader import get_module_loader


class MaterialService:
    """素材服务类"""

    def __init__(self):
        """初始化素材服务"""
        self.loader = get_module_loader()

        # 动态加载MaterialManager
        MaterialManager = self.loader.load_material_manager()

        self.manager = MaterialManager()

    def add_material(
        self,
        file_path: str,
        material_type: str,
        name: str = None,
        description: str = "",
        tags: List[str] = None,
        category: str = "general",
        copy_file: bool = True
    ) -> str:
        """
        添加素材

        Args:
            file_path: 文件路径
            material_type: 素材类型（image/video/audio）
            name: 素材名称
            description: 描述
            tags: 标签列表
            category: 分类
            copy_file: 是否复制文件到素材库

        Returns:
            素材ID
        """
        try:
            material_id = self.manager.add_material(
                file_path=file_path,
                material_type=material_type,
                name=name,
                description=description,
                tags=tags or [],
                category=category,
                metadata={},
                copy_file=copy_file
            )

            return material_id

        except Exception as e:
            raise Exception(f"添加素材失败: {str(e)}")

    def get_material(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        获取素材详情

        Args:
            material_id: 素材ID

        Returns:
            素材信息
        """
        return self.manager.get_material(material_id)

    def list_materials(
        self,
        material_type: str = None,
        category: str = None,
        tags: List[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出素材

        Args:
            material_type: 素材类型过滤
            category: 分类过滤
            tags: 标签过滤
            limit: 返回数量限制

        Returns:
            素材列表
        """
        materials = self.manager.list_materials(
            material_type=material_type,
            category=category
        )

        # 标签过滤
        if tags:
            materials = [
                m for m in materials
                if any(tag in m.get("tags", []) for tag in tags)
            ]

        # 限制数量
        materials = materials[:limit]

        return materials

    def search_materials(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索素材

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制

        Returns:
            搜索结果
        """
        return self.manager.search_materials(keyword, limit=limit)

    def update_material(
        self,
        material_id: str,
        name: str = None,
        description: str = None,
        tags: List[str] = None,
        category: str = None,
        rating: int = None
    ) -> bool:
        """
        更新素材信息

        Args:
            material_id: 素材ID
            name: 新名称
            description: 新描述
            tags: 新标签
            category: 新分类
            rating: 新评分

        Returns:
            是否更新成功
        """
        try:
            material = self.manager.get_material(material_id)

            if not material:
                return False

            # 更新字段
            if name is not None:
                material["name"] = name
            if description is not None:
                material["description"] = description
            if tags is not None:
                material["tags"] = tags
            if category is not None:
                material["category"] = category
            if rating is not None:
                material["rating"] = rating

            # 保存更新
            self.manager.update_material(material_id, material)

            return True

        except Exception as e:
            print(f"更新素材失败: {e}")
            return False

    def delete_material(self, material_id: str) -> bool:
        """
        删除素材

        Args:
            material_id: 素材ID

        Returns:
            是否删除成功
        """
        try:
            return self.manager.delete_material(material_id)
        except Exception as e:
            print(f"删除素材失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取素材统计信息

        Returns:
            统计数据
        """
        return self.manager.get_statistics()

    def get_categories(self) -> List[str]:
        """
        获取所有素材分类

        Returns:
            分类列表
        """
        materials = self.list_materials()
        categories = set(m.get("category", "general") for m in materials)
        return sorted(list(categories))

    def get_all_tags(self) -> List[str]:
        """
        获取所有标签

        Returns:
            标签列表
        """
        materials = self.list_materials()
        all_tags = set()
        for material in materials:
            all_tags.update(material.get("tags", []))

        return sorted(list(all_tags))


# 全局单例
_material_service = None


def get_material_service() -> MaterialService:
    """
    获取全局素材服务实例

    Returns:
        MaterialService实例
    """
    global _material_service
    if _material_service is None:
        _material_service = MaterialService()
    return _material_service
