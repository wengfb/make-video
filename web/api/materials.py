"""
素材管理API路由
提供素材上传、查询、管理等功能
"""
from fastapi import APIRouter, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from web.services.material_service import get_material_service


# 创建路由器
router = APIRouter(prefix="/api/materials", tags=["素材管理"])

# ==================== 数据模型 ====================


class UpdateMaterialRequest(BaseModel):
    """更新素材请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    rating: Optional[int] = None


# ==================== API端点 ====================


@router.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    material_type: str = Form(...),
    name: str = Form(None),
    description: str = Form(""),
    tags: str = Form(""),
    category: str = Form("general")
):
    """
    上传素材文件

    支持图片、视频、音频文件上传
    """
    import tempfile
    import shutil
    import uuid

    try:
        # 保存到临时文件
        suffix = Path(file.filename).suffix
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

        with temp_file as buffer:
            shutil.copyfileobj(file.file, buffer)

        temp_path = temp_file.name
        temp_path.close()

        # 解析标签
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        # 使用MaterialManager添加素材
        material_service = get_material_service()

        material_id = material_service.add_material(
            file_path=temp_path,
            material_type=material_type,
            name=name or file.filename,
            description=description,
            tags=tag_list,
            category=category,
            copy_file=True
        )

        return {
            "success": True,
            "message": "素材上传成功",
            "material_id": material_id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"上传失败: {str(e)}"
        }


@router.get("/")
async def list_materials(
    material_type: Optional[str] = Query(None, description="素材类型"),
    category: Optional[str] = Query(None, description="分类"),
    tags: Optional[str] = Query(None, description="标签（逗号分隔）"),
    limit: int = Query(100, ge=1, le=500, description="返回数量")
):
    """
    获取素材列表

    支持按类型、分类、标签筛选
    """
    try:
        material_service = get_material_service()

        # 解析标签
        tag_list = [t.strip() for t in tags.split(",")] if tags else None

        materials = material_service.list_materials(
            material_type=material_type,
            category=category,
            tags=tag_list,
            limit=limit
        )

        # 添加URL路径
        for material in materials:
            file_path = material.get("file_path", "")
            if file_path:
                # 转换为相对路径用于访问
                rel_path = file_path.replace("\\", "/")
                if "materials/" in rel_path:
                    material["url"] = "/" + rel_path
                else:
                    material["url"] = None

        return {
            "success": True,
            "materials": materials,
            "count": len(materials)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/{material_id}")
async def get_material(material_id: str):
    """
    获取素材详情

    Args:
        material_id: 素材ID

    Returns:
        素材详情
    """
    try:
        material_service = get_material_service()
        material = material_service.get_material(material_id)

        if not material:
            return {
                "success": False,
                "error": "素材不存在"
            }

        return {
            "success": True,
            "material": material
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.put("/{material_id}")
async def update_material(
    material_id: str,
    request: UpdateMaterialRequest
):
    """
    更新素材信息

    Args:
        material_id: 素材ID
        request: 更新请求

    Returns:
        更新结果
    """
    try:
        material_service = get_material_service()

        success = material_service.update_material(
            material_id=material_id,
            name=request.name,
            description=request.description,
            tags=request.tags,
            category=request.category,
            rating=request.rating
        )

        if success:
            return {
                "success": True,
                "message": "素材更新成功"
            }
        else:
            return {
                "success": False,
                "error": "素材不存在或更新失败"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/{material_id}")
async def delete_material(material_id: str):
    """
    删除素材

    Args:
        material_id: 素材ID

    Returns:
        删除结果
    """
    try:
        material_service = get_material_service()
        success = material_service.delete_material(material_id)

        if success:
            return {
                "success": True,
                "message": "素材删除成功"
            }
        else:
            return {
                "success": False,
                "error": "素材不存在或删除失败"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/search/{keyword}")
async def search_materials(
    keyword: str,
    limit: int = Query(50, ge=1, le=200, description="返回数量")
):
    """
    搜索素材

    Args:
        keyword: 搜索关键词
        limit: 返回数量

    Returns:
        搜索结果
    """
    try:
        material_service = get_material_service()
        materials = material_service.search_materials(keyword, limit=limit)

        return {
            "success": True,
            "materials": materials,
            "count": len(materials)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/categories/list")
async def list_categories():
    """
    获取所有素材分类

    Returns:
        分类列表
    """
    try:
        material_service = get_material_service()
        categories = material_service.get_categories()

        return {
            "success": True,
            "categories": categories
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/tags/list")
async def list_tags():
    """
    获取所有标签

    Returns:
        标签列表
    """
    try:
        material_service = get_material_service()
        tags = material_service.get_all_tags()

        return {
            "success": True,
            "tags": tags
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/stats/summary")
async def get_statistics():
    """
    获取素材统计信息

    Returns:
        统计数据
    """
    try:
        material_service = get_material_service()
        stats = material_service.get_statistics()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
