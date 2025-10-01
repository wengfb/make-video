# 素材管理器使用指南

## 🎨 功能概述

素材管理系统是视频制作流程的核心支撑，提供：

1. **素材库管理** - 图片、视频、音频的统一管理
2. **智能分类** - 标签和分类系统
3. **快速搜索** - 关键词和标签搜索
4. **AI图片生成** - 集成DALL-E等AI绘图服务
5. **智能推荐** - 根据脚本推荐合适素材

## 🚀 快速开始

### 基础使用

```python
from scripts.2_material_manager import MaterialManager

# 初始化
manager = MaterialManager()

# 添加素材
material_id = manager.add_material(
    file_path="/path/to/image.png",
    material_type="image",
    name="光的折射示意图",
    tags=["物理", "光学", "实验"],
    category="物理学"
)

# 搜索素材
results = manager.search_materials("光学")

# 查看统计
stats = manager.get_statistics()
```

## 📖 详细功能说明

### 1. 素材管理基础

#### 添加素材

```python
material_id = manager.add_material(
    file_path="path/to/file.jpg",      # 源文件路径
    material_type="image",              # 类型: image/video/audio
    name="素材名称",                     # 可选，默认使用文件名
    description="详细描述",              # 可选
    tags=["标签1", "标签2"],            # 可选
    category="分类名称",                 # 可选
    metadata={"author": "张三"}          # 可选，额外元数据
)
```

**支持的素材类型**:
- `image` - 图片（JPG, PNG, GIF等）
- `video` - 视频（MP4, MOV, AVI等）
- `audio` - 音频（MP3, WAV, AAC等）

**自动处理**:
- 文件自动复制到素材库
- 生成唯一ID
- 记录文件信息（大小、扩展名）
- 创建时间戳

#### 查看素材

```python
# 获取单个素材
material = manager.get_material(material_id)

# 列出所有素材
all_materials = manager.list_materials()

# 筛选列表
images = manager.list_materials(
    material_type="image",              # 按类型
    category="物理学",                   # 按分类
    tags=["实验", "演示"],              # 按标签
    sort_by="rating",                   # 排序: date/name/size/rating/usage
    limit=20                            # 限制数量
)
```

#### 更新素材

```python
manager.update_material(
    material_id=material_id,
    name="新名称",
    description="新描述",
    tags=["新标签列表"],
    category="新分类",
    rating=5                            # 1-5星评分
)
```

#### 删除素材

```python
manager.delete_material(
    material_id=material_id,
    delete_file=True                    # 是否同时删除文件
)
```

### 2. 标签系统

#### 添加标签

```python
# 为素材添加标签
manager.add_tags_to_material(material_id, ["新标签1", "新标签2"])

# 移除标签
manager.remove_tags_from_material(material_id, ["旧标签"])
```

#### 查看标签统计

```python
# 获取所有标签及使用次数
tags = manager.get_all_tags()

# 输出示例:
# [
#   {"name": "物理", "count": 15, "created_at": "...", "last_used": "..."},
#   {"name": "化学", "count": 10, ...},
#   ...
# ]
```

### 3. 分类系统

#### 查看分类

```python
categories = manager.get_categories()

# 输出示例:
# {
#   "物理学": 25,
#   "化学": 18,
#   "生物学": 12,
#   "uncategorized": 5
# }
```

### 4. 搜索功能

#### 关键词搜索

```python
# 搜索名称、描述和标签
results = manager.search_materials("量子")

# 自定义搜索范围
results = manager.search_materials(
    keyword="实验",
    search_in=["name", "tags"]          # 只搜索名称和标签
)
```

### 5. AI图片生成

#### 基础生成

```python
from scripts.2_material_manager import AIImageGenerator

# 初始化
generator = AIImageGenerator()

# 生成图片
images = generator.generate_image(
    prompt="一个展示光的折射的科学插图",
    size="1024x1024",                   # 尺寸
    quality="standard",                 # standard/hd
    style="vivid",                      # vivid/natural
    n=1                                 # 生成数量
)

# 保存图片
for img in images:
    filepath = generator.save_generated_image(
        image_data=img,
        output_dir="materials/images"
    )
```

#### 根据脚本生成

```python
# 为脚本章节生成配图
script_section = {
    "section_name": "光的折射",
    "narration": "光从空气进入水中时会发生折射...",
    "visual_notes": "需要展示光线在水面的弯曲"
}

images = generator.generate_from_script(
    script_section=script_section,
    image_count=2
)
```

#### 批量生成建议

```python
# 为整个脚本生成图片提示词
script = {...}  # 完整脚本数据
suggestions = generator.suggest_prompts_for_script(script)

# 输出示例:
# [
#   {
#     "section": "开场钩子",
#     "prompt": "...",
#     "visual_notes": "..."
#   },
#   ...
# ]
```

### 6. 智能素材推荐

#### 为脚本推荐素材

```python
from scripts.2_material_manager import MaterialRecommender

# 初始化
recommender = MaterialRecommender(manager)

# 为单个章节推荐
script_section = {...}
recommended = recommender.recommend_for_script_section(
    script_section=script_section,
    limit=5
)

# 为整个脚本推荐
script = {...}
all_recommendations = recommender.recommend_for_full_script(script)

# 输出示例:
# {
#   "开场钩子": [material1, material2, ...],
#   "主题介绍": [material3, material4, ...],
#   ...
# }
```

#### 分析素材覆盖度

```python
coverage = recommender.analyze_material_coverage(script)

# 输出示例:
# {
#   "total_sections": 7,
#   "fully_covered": 3,
#   "partially_covered": 2,
#   "not_covered": 2,
#   "coverage_rate": 42.86,
#   "details": [...]
# }
```

#### 建议缺失素材

```python
missing = recommender.suggest_missing_materials(script)

# 输出示例:
# [
#   {
#     "section": "核心内容",
#     "visual_requirement": "需要DNA双螺旋结构图",
#     "suggestion_type": "missing",
#     "action": "建议使用AI生成或手动添加素材"
#   },
#   ...
# ]
```

### 7. 统计和分析

```python
stats = manager.get_statistics()

# 输出示例:
# {
#   "total_materials": 150,
#   "total_size": 524288000,
#   "total_size_mb": 500.0,
#   "by_type": {
#     "image": {"count": 100, "size": 300000000},
#     "video": {"count": 30, "size": 200000000},
#     "audio": {"count": 20, "size": 24288000}
#   },
#   "categories": {"物理学": 50, "化学": 40, ...},
#   "total_tags": 45
# }
```

## 💡 使用场景

### 场景1: 建立素材库

```python
# 批量导入素材
import os

materials_dir = "/path/to/your/materials"
for filename in os.listdir(materials_dir):
    if filename.endswith(('.jpg', '.png')):
        file_path = os.path.join(materials_dir, filename)

        # 根据文件名自动分类
        if "物理" in filename:
            category = "物理学"
            tags = ["物理"]
        elif "化学" in filename:
            category = "化学"
            tags = ["化学"]
        else:
            category = "其他"
            tags = []

        manager.add_material(
            file_path=file_path,
            material_type="image",
            category=category,
            tags=tags
        )
```

### 场景2: 为脚本准备素材

```python
# 1. 查看脚本需要什么素材
script = {...}  # 你的脚本数据
missing = recommender.suggest_missing_materials(script)

# 2. 为缺失的素材生成图片
for item in missing:
    if item['visual_requirement']:
        images = generator.generate_image(
            prompt=item['visual_requirement']
        )

        for img in images:
            # 保存并添加到素材库
            filepath = generator.save_generated_image(
                img,
                "materials/images"
            )

            manager.add_material(
                file_path=filepath,
                material_type="image",
                tags=[item['section'], "AI生成"],
                category="AI生成素材"
            )
```

### 场景3: 素材评分和管理

```python
# 使用后评分
material_id = "..."
manager.update_material(material_id, rating=5)

# 增加使用计数
manager.increment_usage(material_id)

# 查看最常用的素材
popular_materials = manager.list_materials(
    sort_by="usage",
    limit=10
)
```

## 🎯 最佳实践

### 1. 命名规范

建议使用描述性的名称:
```
✅ 好: "光的折射_实验演示_水杯"
❌ 差: "IMG_1234"
```

### 2. 标签策略

使用层次化的标签:
```python
tags = [
    "物理学",          # 领域
    "光学",            # 子领域
    "折射",            # 具体概念
    "实验",            # 类型
    "演示"             # 用途
]
```

### 3. 分类体系

建议的分类:
- 按学科: 物理学、化学、生物学...
- 按类型: 插图、照片、图表、动画...
- 按来源: 原创、AI生成、网络素材...
- 按用途: 片头、正文、片尾...

### 4. 定期维护

```python
# 删除未使用的素材
all_materials = manager.list_materials()
for material in all_materials:
    if material['used_count'] == 0:
        # 检查是否超过3个月未使用
        # 考虑删除

# 更新标签
# 定期检查和优化标签体系
```

## ⚙️ 配置说明

### settings.json 配置

```json
{
  "ai_image": {
    "provider": "dalle",                    // AI服务: dalle/stable-diffusion
    "model": "dall-e-3",                   // 模型
    "api_key": "your-api-key",             // API密钥
    "default_size": "1024x1024",           // 默认尺寸
    "default_quality": "standard",         // 质量: standard/hd
    "default_style": "educational...",     // 默认风格描述
  },

  "material_manager": {
    "auto_tag": true,                      // 自动标签
    "auto_categorize": true,               // 自动分类
    "default_category": "uncategorized",   // 默认分类
    "max_file_size_mb": 100               // 最大文件大小
  }
}
```

## 📁 数据存储

素材数据存储在:

```
data/
├── materials.json      # 素材元数据
├── tags.json          # 标签索引
└── collections.json   # 集合（未来功能）

materials/
├── images/            # 图片文件
├── videos/            # 视频文件
└── audio/             # 音频文件
```

## ❓ 常见问题

### Q: 如何批量导入素材？

A: 编写脚本遍历目录，调用`add_material()`

### Q: AI生成的图片质量如何？

A: 取决于:
1. 提示词质量
2. 模型选择（DALL-E 3 > DALL-E 2）
3. quality参数（hd > standard）

### Q: 素材推荐的准确度？

A: 基于:
1. 标签匹配
2. 关键词匹配
3. 使用历史
4. 评分

### Q: 支持哪些图片格式？

A: 常见格式都支持，包括JPG, PNG, GIF, WebP等

### Q: 如何备份素材库？

A: 备份两个目录:
1. `data/` - 元数据
2. `materials/` - 实际文件

## 🔮 未来功能

- [ ] 素材集合/播放列表
- [ ] 批量编辑
- [ ] 素材版本管理
- [ ] 云存储集成
- [ ] 视频缩略图生成
- [ ] 音频波形预览

---

**下一步**: 了解如何将素材整合到视频制作流程中
