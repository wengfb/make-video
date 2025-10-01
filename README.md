# 科普视频自动化制作系统 V5.0 🎉

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.0-brightgreen.svg)](VERSION_5.0_SUMMARY.md)

AI驱动的科普视频制作工具链,从主题选择到**带语音字幕的成品视频** - **全程自动化解决方案**! 🚀

## 🎯 项目特色

- **🎨 完整工作流**: 主题生成 → 脚本创作 → 素材管理 → 视频合成，一站式自动化
- **🤖 AI驱动**: GPT-4脚本生成 + DALL-E图片生成，智能内容创作
- **🎬 专业视频制作**: 基于moviepy的视频编辑，支持转场、文字、音乐
- **📊 智能推荐**: 自动素材匹配，评分系统，使用统计
- **🔧 高度可配置**: 灵活的模板系统，丰富的配置选项
- **📚 完善文档**: 从快速开始到深度指南，覆盖所有使用场景

## ✨ V5.0 新功能 🎊

🎉 **重大更新**: 实现完整的AI语音视频生产线!

- ✅ **TTS语音合成**: 自动将脚本转为真人语音(支持Edge TTS免费/OpenAI TTS)
- ✅ **智能字幕生成**: 自动生成SRT/ASS字幕,与语音精确对齐
- ✅ **全自动AI工作流**: 从主题到带语音字幕的成品视频 - 一键完成!
- ✅ **17种中文声音**: 多种男女声可选,语速可调
- ✅ **音频后期处理**: 自动混音BGM,完美融合

**从V4.0升级**:
- ✅ **视频编辑器**: 基础视频剪辑、拼接、特效
- ✅ **智能视频合成**: 根据脚本自动生成视频
- ✅ **转场效果库**: 6种专业转场效果
- ✅ **素材智能匹配**: 自动为每个章节选择最佳素材

[查看 V5.0 完整更新说明 →](VERSION_5.0_SUMMARY.md) | [V4.0更新 →](VERSION_4.0_SUMMARY.md)

## 🚀 5分钟快速开始

### 1. 安装依赖

```bash
# 安装系统依赖（视频处理必需）
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `config/settings.json`:

```json
{
  "ai": {
    "api_key": "你的OpenAI API密钥"
  },
  "ai_image": {
    "api_key": "你的OpenAI API密钥"
  }
}
```

### 3. 运行程序

```bash
python main.py
```

选择 **菜单13**（完整工作流），体验从主题到视频的自动化生成！

[详细快速开始指南 →](QUICKSTART_V4.md)

## 📂 项目结构

```
make-video/
├── config/                      # 配置文件
│   ├── settings.json           # 主配置（API密钥、视频参数等）
│   ├── settings.example.json   # 配置示例
│   └── templates.json          # AI提示词模板
│
├── scripts/                     # 核心功能模块
│   ├── 0_topic_generator/      # ✅ 主题生成与管理（v2.0）
│   │   ├── generator.py        #    智能主题生成
│   │   └── manager.py          #    主题收藏、评分、搜索
│   │
│   ├── 1_script_generator/     # ✅ 脚本生成器（v1.0）
│   │   ├── ai_client.py        #    AI API客户端
│   │   └── generator.py        #    脚本自动生成
│   │
│   ├── 2_material_manager/     # ✅ 素材管理系统（v3.0）
│   │   ├── manager.py          #    素材CRUD、标签、分类
│   │   ├── ai_generator.py     #    AI图片生成（DALL-E）
│   │   ├── recommender.py      #    智能素材推荐
│   │   └── ui.py               #    素材管理界面
│   │
│   └── 3_video_editor/         # ✅ 视频编辑与合成（v4.0）
│       ├── editor.py           #    基础视频编辑
│       ├── composer.py         #    智能视频合成器
│       └── transitions.py      #    转场效果库
│
├── data/                        # 数据存储
│   ├── topics.json             # 主题数据
│   ├── favorites.json          # 收藏数据
│   ├── materials.json          # 素材元数据
│   └── material_tags.json      # 标签索引
│
├── materials/                   # 素材库
│   ├── images/                 # 图片素材
│   ├── videos/                 # 视频素材
│   └── audio/                  # 音频素材
│
├── output/                      # 输出目录
│   ├── scripts/                # 生成的脚本
│   └── videos/                 # 生成的视频
│
├── main.py                      # 主程序入口（CLI界面）
├── requirements.txt             # Python依赖
│
└── docs/                        # 文档
    ├── README.md               # 本文件
    ├── QUICKSTART_V4.md        # 快速开始指南
    ├── VERSION_4.0_SUMMARY.md  # v4.0更新摘要
    ├── VIDEO_EDITOR_GUIDE.md   # 视频编辑器指南
    ├── MATERIAL_MANAGER_GUIDE.md # 素材管理指南
    └── PROJECT_STATUS_V4.md    # 项目状态报告
```

## 🎨 核心功能

### 1. 主题管理（v2.0）

```python
# 智能主题生成
- AI生成主题建议（可定制领域、受众）
- 热门趋势主题推荐
- 主题收藏和评分系统
- 主题搜索和历史记录
```

**使用场景**: 不知道做什么视频？让AI帮你找灵感！

### 2. 脚本生成（v1.0）

```python
# AI脚本创作
- 基于主题自动生成完整脚本
- 多种视频类型模板
- 章节化结构，时长控制
- 视觉元素建议
```

**使用场景**: 有了主题，AI自动写脚本，省去大量创作时间。

### 3. 素材管理（v3.0）

```python
# 素材库管理
- 素材CRUD操作（增删改查）
- 标签和分类系统
- 素材搜索和评分
- 使用统计追踪

# AI图片生成
- DALL-E 3集成
- 根据脚本生成配图
- 自动保存到素材库
```

**使用场景**: 管理你的素材库，或让AI生成所需配图。

### 4. 视频合成（v4.0）⭐ 新功能

```python
# 智能视频合成
- 基于脚本自动生成视频
- 智能素材匹配（评分系统）
- 自动文字叠加
- 背景音乐支持
- 6种专业转场效果

# 基础视频编辑
- 图片幻灯片制作
- 视频拼接、裁剪
- 音频添加
- 文字叠加
```

**使用场景**: 脚本和素材准备好，一键生成成品视频！

### 5. 完整工作流（v4.0）⭐ 新功能

```
主题生成 → 脚本创作 → 素材准备 → 视频合成
     ↓          ↓          ↓          ↓
  AI智能    AI智能     AI生成      自动合成
```

**使用场景**: 从零到视频，全程自动化！

## 📖 使用示例

### 示例1: 完整工作流（推荐）

```bash
python main.py
```

1. 选择 **13**（完整工作流）
2. 生成或选择主题（如"量子计算的奇妙世界"）
3. AI自动生成脚本（1-2分钟）
4. 系统自动匹配素材并合成视频（2-5分钟）
5. 完成！视频保存在 `output/videos/`

### 示例2: 从脚本生成视频

```bash
python main.py
```

1. 选择 **11**（从脚本生成视频）
2. 选择已有的脚本文件
3. 系统自动合成视频

### 示例3: AI生成配图素材

```bash
python main.py
```

1. 选择 **10**（素材管理）
2. 选择 **5**（生成图片）
3. 输入描述: "量子计算机芯片特写，科技风格，蓝色调"
4. 生成并自动保存到素材库

### 示例4: 预览素材推荐

```bash
python main.py
```

1. 选择 **12**（预览素材推荐）
2. 选择脚本
3. 查看每个章节的素材推荐和匹配度

## 🔧 配置说明

### 基本配置 (`config/settings.json`)

```json
{
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "你的API密钥",
    "temperature": 0.7
  },

  "ai_image": {
    "provider": "dalle",
    "model": "dall-e-3",
    "api_key": "你的API密钥",
    "default_size": "1024x1024"
  },

  "video": {
    "fps": 24,
    "resolution": [1920, 1080],
    "default_image_duration": 5.0,
    "show_narration_text": true,
    "text_size": 40
  }
}
```

[完整配置说明 →](VIDEO_EDITOR_GUIDE.md#配置说明)

## 💡 最佳实践

### 提高生成质量

1. **主题描述要具体**
   - ❌ "讲讲物理"
   - ✅ "相对论中的时间膨胀效应及其实验验证"

2. **给素材打好标签**
   - 精确的标签帮助系统更好地匹配素材
   - 使用相关关键词：主题、风格、颜色等

3. **利用AI生成素材**
   - 素材库不足时，使用DALL-E生成
   - 根据脚本章节批量生成配图

4. **预览后再合成**
   - 使用菜单12预览素材推荐
   - 检查匹配度，必要时补充素材

### 优化视频输出

1. **调整分辨率和帧率**
   ```json
   {
     "video": {
       "fps": 24,              // 24fps更快
       "resolution": [1280, 720] // 720p更快
     }
   }
   ```

2. **控制视频时长**
   - 短视频（1-3分钟）：合成更快
   - 章节时长适中：4-6秒/章

3. **使用背景音乐**
   ```json
   {
     "video": {
       "default_bgm": "materials/audio/bgm.mp3"
     }
   }
   ```

## 📊 系统要求

### 最低配置

- CPU: 双核处理器
- RAM: 4GB
- 磁盘: 10GB可用空间
- Python: 3.8+
- 系统: Windows/macOS/Linux

### 推荐配置

- CPU: 四核及以上
- RAM: 8GB及以上
- 磁盘: 50GB+ SSD
- Python: 3.10+
- GPU: 可选（用于加速）

### 必需软件

- **FFmpeg**: 视频编解码（必需）
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg

  # macOS
  brew install ffmpeg
  ```

- **ImageMagick**: 文字渲染（可选）
  ```bash
  # Ubuntu/Debian
  sudo apt-get install imagemagick

  # macOS
  brew install imagemagick
  ```

## 🎯 开发路线图

### ✅ V1.0 - 脚本生成（已完成）
- [x] AI脚本生成器
- [x] 多模板支持
- [x] 配置系统

### ✅ V2.0 - 主题管理（已完成）
- [x] 智能主题生成
- [x] 主题收藏和评分
- [x] 主题搜索

### ✅ V3.0 - 素材管理（已完成）
- [x] 素材库管理
- [x] AI图片生成
- [x] 智能推荐

### ✅ V4.0 - 视频合成（已完成）
- [x] 视频编辑器
- [x] 智能视频合成
- [x] 转场效果
- [x] 完整工作流

### 🔮 V5.0 - 计划中
- [ ] 语音合成（TTS）
- [ ] 字幕生成
- [ ] 性能优化
- [ ] Web界面

[查看详细路线图 →](PROJECT_STATUS_V4.md)

## 📚 文档导航

| 文档 | 说明 |
|-----|------|
| [QUICKSTART_V4.md](QUICKSTART_V4.md) | 5分钟快速开始 |
| [VERSION_4.0_SUMMARY.md](VERSION_4.0_SUMMARY.md) | v4.0完整更新说明 |
| [VIDEO_EDITOR_GUIDE.md](VIDEO_EDITOR_GUIDE.md) | 视频编辑器详细指南 |
| [MATERIAL_MANAGER_GUIDE.md](MATERIAL_MANAGER_GUIDE.md) | 素材管理详细指南 |
| [PROJECT_STATUS_V4.md](PROJECT_STATUS_V4.md) | 项目状态报告 |
| [EXAMPLES.md](EXAMPLES.md) | 使用示例集合 |

## 🐛 常见问题

### Q: 视频合成很慢怎么办？

**A**:
1. 降低分辨率: `"resolution": [1280, 720]`
2. 降低帧率: `"fps": 24`
3. 减少章节数或缩短时长

### Q: 提示"找不到FFmpeg"？

**A**:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows: 下载FFmpeg并添加到PATH
```

### Q: 素材匹配不准确？

**A**:
1. 使用菜单12预览推荐
2. 给素材添加更精确的标签
3. 使用自定义素材映射

### Q: API调用失败？

**A**:
1. 检查API密钥是否正确
2. 检查网络连接
3. 确认OpenAI账户有余额

[更多常见问题 →](VIDEO_EDITOR_GUIDE.md#常见问题)

## 💰 成本估算

基于OpenAI API定价（2025年）:

| 操作 | 单次成本 | 100次/月 |
|-----|---------|----------|
| 主题生成 | ~$0.02 | ~$2 |
| 脚本生成 | ~$0.10 | ~$10 |
| 图片生成 | ~$0.04 | ~$4 |
| **合计** | ~$0.16 | ~$16 |

*实际成本可能因使用模式而异*

## ⚠️ 注意事项

1. **API费用控制**: AI调用产生费用，建议设置配额限制
2. **内容审核**: AI生成内容需人工审核准确性和合规性
3. **版权问题**: 确保使用的素材有合法授权
4. **密钥安全**: 不要将含密钥的配置文件上传到公开仓库

## 🤝 贡献指南

欢迎贡献代码、报告问题、提出建议！

1. Fork 本项目
2. 创建特性分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送到分支: `git push origin feature/AmazingFeature`
5. 提交Pull Request

## 🙏 致谢

感谢以下开源项目:

- [OpenAI](https://openai.com/) - GPT和DALL-E API
- [moviepy](https://github.com/Zulko/moviepy) - 视频处理
- [FFmpeg](https://ffmpeg.org/) - 视频编解码
- [Pillow](https://python-pillow.org/) - 图像处理

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- 提交 [Issue](https://github.com/yourusername/make-video/issues)
- 发送邮件: your.email@example.com

---

## 🎉 开始创作

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py

# 选择菜单13，体验完整工作流！
```

**用AI的力量，让科普视频制作变得简单而高效！** 🚀✨

---

**最后更新**: V4.0 (2025年1月)
