"""
素材管理器交互界面
提供CLI交互功能
"""

from typing import Optional
from .manager import MaterialManager
from .ai_generator import AIImageGenerator
from .recommender import MaterialRecommender


def material_manager_menu(manager: MaterialManager, generator: AIImageGenerator):
    """素材管理主菜单"""
    while True:
        print("\n" + "=" * 60)
        print("🎨 素材管理")
        print("=" * 60)
        print("\n📚 素材库管理:")
        print("  1. 添加素材")
        print("  2. 浏览素材")
        print("  3. 搜索素材")
        print("  4. 查看统计")
        print("\n🎨 AI图片生成:")
        print("  5. 生成图片")
        print("  6. 根据脚本生成图片")
        print("\n🏷️  标签和分类:")
        print("  7. 查看所有标签")
        print("  8. 查看所有分类")
        print("\n  0. 返回主菜单")
        print("=" * 60)

        choice = input("\n请选择功能 (0-8): ").strip()

        if choice == '0':
            break
        elif choice == '1':
            add_material_interactive(manager)
        elif choice == '2':
            browse_materials_interactive(manager)
        elif choice == '3':
            search_materials_interactive(manager)
        elif choice == '4':
            show_material_stats(manager)
        elif choice == '5':
            generate_image_interactive(generator, manager)
        elif choice == '6':
            generate_from_script_interactive(generator, manager)
        elif choice == '7':
            show_all_tags(manager)
        elif choice == '8':
            show_all_categories(manager)
        else:
            print("\n❌ 无效的选择")


def add_material_interactive(manager: MaterialManager):
    """交互式添加素材"""
    print("\n" + "-" * 60)
    print("➕ 添加素材")
    print("-" * 60)

    # 文件路径
    file_path = input("\n文件路径: ").strip()
    if not file_path:
        print("❌ 文件路径不能为空")
        return

    # 素材类型
    print("\n素材类型:")
    print("  1. 图片 (image)")
    print("  2. 视频 (video)")
    print("  3. 音频 (audio)")
    type_choice = input("选择类型 (1-3): ").strip()

    type_map = {'1': 'image', '2': 'video', '3': 'audio'}
    material_type = type_map.get(type_choice, 'image')

    # 可选信息
    name = input("\n名称 (可选，回车跳过): ").strip() or None
    description = input("描述 (可选): ").strip() or None
    category = input("分类 (可选): ").strip() or None

    tags_input = input("标签 (用逗号分隔，可选): ").strip()
    tags = [t.strip() for t in tags_input.split(',')] if tags_input else None

    try:
        material_id = manager.add_material(
            file_path=file_path,
            material_type=material_type,
            name=name,
            description=description,
            tags=tags,
            category=category
        )
        print(f"\n✅ 素材已添加，ID: {material_id}")

    except Exception as e:
        print(f"\n❌ 添加失败: {str(e)}")


def browse_materials_interactive(manager: MaterialManager):
    """交互式浏览素材"""
    print("\n" + "-" * 60)
    print("📚 浏览素材")
    print("-" * 60)

    # 筛选选项
    print("\n筛选选项:")
    print("  1. 全部素材")
    print("  2. 仅图片")
    print("  3. 仅视频")
    print("  4. 仅音频")
    print("  5. 按分类筛选")

    filter_choice = input("\n选择 (1-5): ").strip()

    material_type = None
    category = None

    if filter_choice == '2':
        material_type = 'image'
    elif filter_choice == '3':
        material_type = 'video'
    elif filter_choice == '4':
        material_type = 'audio'
    elif filter_choice == '5':
        category = input("输入分类名称: ").strip()

    # 排序
    print("\n排序方式:")
    print("  1. 按时间 (最新)")
    print("  2. 按名称")
    print("  3. 按评分")
    print("  4. 按使用次数")

    sort_choice = input("选择 (1-4, 默认1): ").strip()
    sort_map = {'1': 'date', '2': 'name', '3': 'rating', '4': 'usage'}
    sort_by = sort_map.get(sort_choice, 'date')

    # 获取素材列表
    materials = manager.list_materials(
        material_type=material_type,
        category=category,
        sort_by=sort_by,
        limit=20
    )

    if not materials:
        print("\n暂无素材")
        return

    # 显示列表
    print(f"\n找到 {len(materials)} 个素材:\n")
    for i, mat in enumerate(materials, 1):
        rating_str = f"⭐{mat.get('rating', '-')}" if mat.get('rating') else "[未评分]"
        print(f"{i}. {mat['name']} {rating_str}")
        print(f"   类型: {mat['type']} | 分类: {mat.get('category', 'N/A')}")
        print(f"   标签: {', '.join(mat.get('tags', []))}")
        print(f"   使用次数: {mat.get('used_count', 0)}")

    # 查看详情
    detail_choice = input("\n输入编号查看详情 (直接回车返回): ").strip()
    if detail_choice.isdigit():
        idx = int(detail_choice) - 1
        if 0 <= idx < len(materials):
            show_material_detail(materials[idx], manager)


def show_material_detail(material: dict, manager: MaterialManager):
    """显示素材详情"""
    print("\n" + "=" * 60)
    print("📋 素材详情")
    print("=" * 60)

    print(f"\nID: {material['id']}")
    print(f"名称: {material['name']}")
    print(f"类型: {material['type']}")
    print(f"分类: {material.get('category', 'N/A')}")
    print(f"描述: {material.get('description', 'N/A')}")
    print(f"标签: {', '.join(material.get('tags', []))}")
    print(f"文件路径: {material['file_path']}")
    print(f"文件大小: {material['file_size']} 字节")
    print(f"使用次数: {material.get('used_count', 0)}")

    rating = material.get('rating')
    print(f"评分: {'⭐' * rating if rating else '未评分'}")

    # 操作菜单
    print("\n" + "-" * 60)
    print("操作:")
    print("  1. 评分")
    print("  2. 更新信息")
    print("  3. 删除")
    print("  0. 返回")

    action = input("\n请选择: ").strip()

    if action == '1':
        rating_input = input("评分 (1-5): ").strip()
        if rating_input.isdigit():
            manager.update_material(material['id'], rating=int(rating_input))

    elif action == '2':
        name = input(f"新名称 (当前: {material['name']}, 回车跳过): ").strip()
        description = input("新描述 (回车跳过): ").strip()
        category = input(f"新分类 (当前: {material.get('category')}, 回车跳过): ").strip()

        manager.update_material(
            material['id'],
            name=name if name else None,
            description=description if description else None,
            category=category if category else None
        )

    elif action == '3':
        confirm = input("确认删除? (y/N): ").strip().lower()
        if confirm == 'y':
            manager.delete_material(material['id'])


def search_materials_interactive(manager: MaterialManager):
    """交互式搜索素材"""
    print("\n" + "-" * 60)
    print("🔍 搜索素材")
    print("-" * 60)

    keyword = input("\n请输入关键词: ").strip()
    if not keyword:
        return

    results = manager.search_materials(keyword)

    if results:
        print(f"\n找到 {len(results)} 个相关素材:\n")
        for i, mat in enumerate(results, 1):
            print(f"{i}. {mat['name']}")
            print(f"   类型: {mat['type']} | 分类: {mat.get('category', 'N/A')}")
            print(f"   标签: {', '.join(mat.get('tags', []))}")

        detail_choice = input("\n输入编号查看详情 (直接回车返回): ").strip()
        if detail_choice.isdigit():
            idx = int(detail_choice) - 1
            if 0 <= idx < len(results):
                show_material_detail(results[idx], manager)
    else:
        print(f"\n未找到包含「{keyword}」的素材")


def show_material_stats(manager: MaterialManager):
    """显示素材统计"""
    print("\n" + "-" * 60)
    print("📊 素材库统计")
    print("-" * 60)

    stats = manager.get_statistics()

    print(f"\n总素材数: {stats['total_materials']}")
    print(f"总大小: {stats['total_size_mb']} MB")
    print(f"标签数: {stats['total_tags']}")

    print("\n按类型分布:")
    for mat_type, info in stats['by_type'].items():
        size_mb = round(info['size'] / (1024 * 1024), 2)
        print(f"  {mat_type}: {info['count']} 个 ({size_mb} MB)")

    if stats['categories']:
        print("\n按分类分布:")
        for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")


def generate_image_interactive(generator: AIImageGenerator, manager: MaterialManager):
    """交互式生成图片"""
    print("\n" + "-" * 60)
    print("🎨 AI图片生成")
    print("-" * 60)

    prompt = input("\n请输入图片描述: ").strip()
    if not prompt:
        print("❌ 描述不能为空")
        return

    # 生成参数
    print("\n尺寸:")
    print("  1. 1024x1024 (方形)")
    print("  2. 1792x1024 (横向)")
    print("  3. 1024x1792 (竖向)")

    size_choice = input("选择尺寸 (1-3, 默认1): ").strip()
    size_map = {'1': '1024x1024', '2': '1792x1024', '3': '1024x1792'}
    size = size_map.get(size_choice, '1024x1024')

    count_input = input("\n生成数量 (1-3, 默认1): ").strip()
    count = int(count_input) if count_input.isdigit() else 1
    count = min(count, 3)

    try:
        print(f"\n⏳ 正在生成图片（可能需要1-2分钟）...")

        images = generator.generate_image(
            prompt=prompt,
            size=size,
            n=count
        )

        print(f"\n✅ 成功生成 {len(images)} 张图片")

        # 保存并添加到素材库
        save = input("\n是否保存到素材库? (Y/n): ").strip().lower()
        if save != 'n':
            for i, img in enumerate(images, 1):
                filepath = generator.save_generated_image(
                    img,
                    "materials/images",
                    filename=f"ai_gen_{i}.png"
                )

                # 添加到素材库
                manager.add_material(
                    file_path=filepath,
                    material_type='image',
                    name=f"AI生成: {prompt[:30]}",
                    description=f"完整提示词: {prompt}",
                    tags=["AI生成", "DALL-E"],
                    category="AI生成素材"
                )

            print(f"\n💾 已保存并添加到素材库")

    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")


def generate_from_script_interactive(generator: AIImageGenerator, manager: MaterialManager):
    """根据脚本生成图片（简化版）"""
    print("\n" + "-" * 60)
    print("📝 根据脚本生成图片")
    print("-" * 60)

    print("\n请输入脚本章节信息:")
    section_name = input("章节名称: ").strip()
    narration = input("旁白内容: ").strip()
    visual_notes = input("视觉提示: ").strip()

    if not (narration or visual_notes):
        print("❌ 旁白或视觉提示至少需要一个")
        return

    script_section = {
        'section_name': section_name or '未命名章节',
        'narration': narration,
        'visual_notes': visual_notes
    }

    count_input = input("\n生成数量 (1-3, 默认2): ").strip()
    count = int(count_input) if count_input.isdigit() else 2

    try:
        images = generator.generate_from_script(script_section, count)

        if images:
            print(f"\n✅ 成功生成 {len(images)} 张图片")

            save = input("\n是否保存到素材库? (Y/n): ").strip().lower()
            if save != 'n':
                for i, img in enumerate(images, 1):
                    filepath = generator.save_generated_image(
                        img,
                        "materials/images"
                    )

                    manager.add_material(
                        file_path=filepath,
                        material_type='image',
                        name=f"{section_name} - 配图{i}",
                        description=visual_notes or narration[:100],
                        tags=[section_name, "脚本配图"],
                        category="脚本素材"
                    )

                print(f"\n💾 已保存并添加到素材库")

    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")


def show_all_tags(manager: MaterialManager):
    """显示所有标签"""
    print("\n" + "-" * 60)
    print("🏷️  所有标签")
    print("-" * 60)

    tags = manager.get_all_tags()

    if tags:
        print(f"\n共 {len(tags)} 个标签:\n")
        for i, tag in enumerate(tags, 1):
            print(f"{i}. {tag['name']} (使用 {tag['count']} 次)")
    else:
        print("\n暂无标签")


def show_all_categories(manager: MaterialManager):
    """显示所有分类"""
    print("\n" + "-" * 60)
    print("📁 所有分类")
    print("-" * 60)

    categories = manager.get_categories()

    if categories:
        print(f"\n共 {len(categories)} 个分类:\n")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count} 个素材")
    else:
        print("\n暂无分类")
