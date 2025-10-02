# 🎬 素材自由系统 - 使用指南

## 🎯 核心功能

告别素材荒！本系统提供**四级智能素材获取策略**:

```
📁 本地素材库 (秒级)
    ↓ 不足时自动
🎥 Pexels视频 (免费,HD)
    ↓ 仍不足时
🖼️ Pexels/Unsplash图片 (免费,高质量)
    ↓ 最后手段
💰 DALL-E生成 (付费,需手动)
```

---

## 🚀 快速开始

### 1. 配置API密钥 (5分钟)

**必读**: [API配置指南](./API_SETUP_GUIDE.md)

简要步骤:
1. 访问 https://www.pexels.com/api/ 获取Pexels API密钥
2. 访问 https://unsplash.com/developers 获取Unsplash Access Key
3. 在 `config/settings.json` 中填入密钥:

```json
"pexels": {
  "api_key": "你的Pexels密钥"
},
"unsplash": {
  "access_key": "你的Unsplash密钥"
}
```

### 2. 测试API (1分钟)

```bash
# 测试Pexels视频下载
python scripts/2_material_manager/pexels_fetcher.py "space"

# 测试Unsplash图片下载
python scripts/2_material_manager/unsplash_fetcher.py "DNA"
```

### 3. 批量预缓存素材 (20分钟)

**推荐首次运行预缓存工具**,一次性下载300+常用素材:

```bash
# 快速模式(100个关键词,每个1视频+1图片)
python scripts/utils/prefetch_materials.py --quick

# 标准模式(100个关键词,每个3视频+2图片) - 推荐
python scripts/utils/prefetch_materials.py

# 只预缓存天文类别
python scripts/utils/prefetch_materials.py --category astronomy

# 只预缓存前10个关键词(测试)
python scripts/utils/prefetch_materials.py --max 10
```

**预期结果**:
- ✅ 300+ HD视频
- ✅ 200+ 高清图片
- ✅ 覆盖所有科普领域
- ✅ ~5-10GB存储

---

## 📖 使用方法

### 方法1: 自动智能获取 (推荐)

在生成视频时,系统会**自动**四级获取素材:

```bash
# 运行主程序
python main.py

# 选择: 11. 从脚本生成视频（自动）
# 或: 13. 完整工作流（主题→脚本→视频）
```

系统会:
1. 先搜索本地素材库
2. 如本地不足,自动从Pexels下载视频
3. 仍不足时,从Unsplash下载图片
4. **全程自动,无需手动**

**示例输出**:
```
🔍 分析素材需求...
   章节: 宇宙的起源
   📁 [1/4] 搜索本地素材库...
       ✓ 找到 0 个本地素材
       ⚠️  本地素材不足 (需要3个,仅0个)
   🎥 [2/4] 从Pexels搜索视频: 'space universe'...
       ⬇️  下载视频: space_universe_12345.mp4 (HD)
       ✅ 下载完成: 15.2 MB
       ✓ 从Pexels视频获取 3 个
```

### 方法2: 手动下载特定素材

```bash
# 下载"量子物理"主题视频
python scripts/2_material_manager/pexels_fetcher.py "quantum physics"

# 下载"DNA"主题图片
python scripts/2_material_manager/unsplash_fetcher.py "DNA" 5
```

### 方法3: 批量预缓存 (推荐首次使用)

```bash
# 预缓存100个热门科普关键词
python scripts/utils/prefetch_materials.py

# 选项:
#   --quick        快速模式(每个1素材)
#   --max 10       只处理前10个
#   --category     按类别(astronomy/biology/physics/technology/environment/math)
#   --videos-only  只下载视频
#   --photos-only  只下载图片
```

---

## 🗂️ 素材库结构

```
materials/
├── videos/
│   └── pexels/
│       ├── space_universe_12345.mp4
│       ├── DNA_genetics_67890.mp4
│       └── ... (300+ HD视频)
│
├── images/
│   ├── pexels/
│   │   ├── quantum_physics_11111.jpg
│   │   └── ... (100+ 图片)
│   └── unsplash/
│       ├── brain_neuroscience_22222.jpg
│       └── ... (100+ 高质量图片)
│
└── pexels_cache.json    # 搜索缓存(7天有效)
```

---

## ⚙️ 配置说明

在 `config/settings.json` 中可调整:

### Pexels配置

```json
"pexels": {
  "api_key": "你的密钥",
  "rate_limit_per_hour": 200,
  "auto_download": true,              // 是否自动下载
  "preferred_video_quality": "hd",    // hd/sd
  "preferred_photo_quality": "large2x" // original/large2x/large/medium/small
}
```

### Unsplash配置

```json
"unsplash": {
  "access_key": "你的密钥",
  "rate_limit_per_hour": 50,
  "auto_download": true,
  "preferred_quality": "regular"  // raw/full/regular/small
}
```

### 智能获取策略

```json
"smart_material_fetch": {
  "enable": true,              // 启用智能获取
  "auto_download": true,       // 自动下载
  "prefer_videos": true,       // 优先视频(+50分)
  "min_local_results": 3,      // 本地素材不足3个时触发外部获取
  "fallback_to_dalle": false,  // 是否降级到DALL-E(付费)
  "cache_duration_days": 7     // 搜索缓存有效期
}
```

---

## 📊 素材统计

查看当前素材库状态:

```python
# Python交互式环境
python

>>> from scripts.2_material_manager.pexels_fetcher import PexelsFetcher
>>> fetcher = PexelsFetcher()
>>> stats = fetcher.get_stats()
>>> print(stats)

# 输出:
# {
#   'video_count': 312,
#   'photo_count': 205,
#   'total_count': 517,
#   'video_size_mb': 4523.5,
#   'photo_size_mb': 856.2,
#   'total_size_mb': 5379.7
# }
```

---

## 🎨 支持的关键词 (100个)

系统内置100个科普关键词,覆盖6大类别:

### 🌌 天文宇宙 (15个)
space universe, galaxy stars, planet earth, solar system, black hole...

### 🧬 生物医学 (20个)
DNA genetics, cell biology, brain neuroscience, virus pathogen...

### ⚛️ 物理化学 (20个)
quantum physics, atom molecule, chemistry lab, nuclear energy...

### 🤖 科技工程 (20个)
artificial intelligence, robot technology, machine learning...

### 🌍 环境自然 (15个)
ocean sea, forest trees, climate weather, ecosystem wildlife...

### 📐 数学工程 (10个)
mathematics geometry, fractal pattern, engineering blueprint...

**完整列表**: 查看 `scripts/utils/prefetch_materials.py`

---

## 💡 使用技巧

### 1. 中英文关键词自动映射

系统智能将中文脚本映射为英文关键词:

| 中文关键词 | 自动映射英文 |
|---------|------------|
| 宇宙 | space universe |
| DNA/基因 | DNA genetics |
| 大脑 | brain neuroscience |
| 量子 | quantum physics |
| 人工智能 | artificial intelligence |

**35+常用科普词汇内置映射**,见 `recommender.py:_extract_english_keyword()`

### 2. 视频素材优先

配置 `prefer_videos: true` 后:
- 视频素材匹配分数 **+50分**
- 同等条件下优先推荐视频
- 让你的作品更生动

### 3. 缓存机制

- 搜索结果缓存 **7天**
- 避免重复API调用
- 提升推荐速度
- 节省API配额

### 4. API配额管理

| API | 限制 | 重置 |
|-----|------|-----|
| Pexels | 200次/小时 | 每小时重置 |
| Unsplash | 50次/小时 | 每小时重置 |

**建议**: 首次运行预缓存工具,后续直接使用缓存素材

---

## ❓ 常见问题

### Q: 素材下载失败?
**A**: 检查:
1. 网络连接
2. API密钥是否正确
3. 是否超出API限制(等待1小时)

### Q: 如何删除缓存重新下载?
**A**: 删除缓存文件:
```bash
rm materials/pexels_cache.json
rm materials/unsplash_cache.json
```

### Q: 视频太大占用空间?
**A**: 调整质量:
```json
"preferred_video_quality": "sd"  // 改为标清
```

### Q: 可以禁用某个来源吗?
**A**: 在 `settings.json` 中:
```json
"smart_material_fetch": {
  "enable": true,
  // 留空API密钥即可禁用该来源
}
```

### Q: 下载的素材可商用吗?
**A**:
- ✅ Pexels: 完全免费,商用无需署名
- ✅ Unsplash: CC0授权,商用无限制

---

## 🎉 成功案例

配置前:
```
❌ 素材库: 0个视频, 0张图片
❌ 视频制作: 需要手动找素材,耗时2小时+
❌ 视频质量: 静态图片堆砌,无生命力
```

配置后:
```
✅ 素材库: 300+ HD视频, 200+ 高清图片
✅ 视频制作: 全自动,10分钟完成
✅ 视频质量: 动态视频为主,专业级别
✅ 成本: 完全免费
```

---

## 📞 技术支持

遇到问题?

1. 查看 [API配置指南](./API_SETUP_GUIDE.md)
2. 查看程序输出的错误信息
3. 检查 `config/settings.json` 配置

---

## 🚀 下一步

1. ✅ 配置API密钥
2. ✅ 测试API连接
3. ✅ 运行批量预缓存
4. ✅ 开始创作视频

**立即开始**:
```bash
python scripts/utils/prefetch_materials.py --quick
```

祝你创作愉快！🎬
