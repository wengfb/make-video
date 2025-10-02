# Claude AI 开发说明

本文档为 Claude AI 助手提供项目上下文和开发指引。

## 📋 项目概述

**项目名称**: 科普视频自动化制作系统
**当前版本**: V5.0
**主要语言**: Python 3.8+
**架构**: 模块化CLI应用

## 🎯 项目目标

创建一个端到端的AI驱动科普视频制作系统,实现:
- 主题生成 → 脚本创作 → 素材管理 → TTS语音合成 → 字幕生成 → 视频合成的完整自动化工作流
- 降低科普视频制作门槛,提高创作效率
- 保证输出质量和一致性
- V5.0新增：从主题到带语音字幕的成品视频，全程自动化

## 🏗️ 系统架构

```
用户界面 (main.py - CLI)
    │
    ├─ 主题管理 (scripts/0_topic_generator/)
    │   ├─ generator.py - AI主题生成
    │   └─ manager.py - 主题收藏、评分、搜索
    │
    ├─ 脚本生成 (scripts/1_script_generator/)
    │   ├─ ai_client.py - AI API封装
    │   └─ generator.py - 脚本生成逻辑
    │
    ├─ 素材管理 (scripts/2_material_manager/)
    │   ├─ manager.py - 素材CRUD
    │   ├─ ai_generator.py - DALL-E图片生成
    │   ├─ recommender.py - 智能推荐
    │   └─ ui.py - 素材管理界面
    │
    ├─ 视频编辑 (scripts/3_video_editor/)
    │   ├─ editor.py - 基础视频编辑
    │   ├─ composer.py - 智能视频合成
    │   └─ transitions.py - 转场效果库
    │
    ├─ TTS语音合成 (scripts/4_tts_generator/) [V5.0新增]
    │   ├─ generator.py - TTS语音生成
    │   └─ manager.py - 语音文件管理
    │
    └─ 字幕生成 (scripts/4_subtitle_generator/) [V5.0新增]
        ├─ generator.py - 字幕生成器
        └─ aligner.py - 时间轴对齐
```

## 📁 目录结构

```
make-video/
├── config/                 # 配置文件
│   ├── settings.json       # 主配置（不要提交API密钥）
│   ├── settings.example.json  # 配置示例
│   └── templates.json      # AI提示词模板
│
├── scripts/                # 核心模块（按顺序编号）
│   ├── 0_topic_generator/
│   ├── 1_script_generator/
│   ├── 2_material_manager/
│   └── 3_video_editor/
│
├── data/                   # JSON数据存储
├── materials/              # 素材库
├── output/                 # 输出目录
│   ├── scripts/
│   └── videos/
│
├── main.py                 # CLI入口
├── requirements.txt        # Python依赖
│
└── docs/                   # 文档
    ├── README.md
    ├── QUICKSTART_V4.md
    ├── VERSION_4.0_SUMMARY.md
    ├── VIDEO_EDITOR_GUIDE.md
    ├── MATERIAL_MANAGER_GUIDE.md
    └── PROJECT_STATUS_V4.md
```

## 🔧 技术栈

### 核心依赖
- **Python**: 3.8+
- **AI服务**:
  - **OpenAI**: GPT-4 (脚本生成) + DALL-E 3 (图片生成)
  - **智谱AI (GLM)**: glm-4, glm-4-plus, glm-4-air (脚本生成) ⭐ 新增
  - **Anthropic**: Claude (可选)
- **moviepy**: 视频编辑和合成
- **FFmpeg**: 视频编解码（系统依赖）
- **Pillow**: 图像处理
- **NumPy**: 数值计算

### 数据存储
- **JSON文件**: 配置、主题、素材元数据
- **文件系统**: 素材和视频文件

### 架构模式
- 模块化设计（每个功能独立模块）
- 面向对象编程
- 依赖注入（配置文件注入）
- importlib.util动态模块加载（避免命名冲突）

## 📝 开发规范

### 代码风格
- 遵循 **PEP 8** 规范
- 使用中文注释和文档字符串
- 函数和方法必须有类型提示
- 保持95%+注释覆盖率

### 文件命名
- Python文件: 小写+下划线 (例: `ai_generator.py`)
- 配置文件: 小写+下划线 (例: `settings.json`)
- 文档文件: 大写+下划线 (例: `README.md`)

### 模块导入
由于多个模块有重名文件(generator.py),使用importlib.util加载:

```python
import importlib.util

spec = importlib.util.spec_from_file_location(
    "module_name",
    "path/to/module.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

### 错误处理
- 所有AI调用必须有try-except
- 文件操作必须检查路径存在性
- 提供用户友好的错误消息

### 配置管理
- 所有可配置项放在`config/settings.json`
- 提供`settings.example.json`示例
- 支持环境变量覆盖(如OPENAI_API_KEY)

## 🔑 关键设计决策

### 1. 模块编号
模块按工作流顺序编号(0-3),便于理解执行顺序:
- 0: 主题生成（第一步）
- 1: 脚本生成（第二步）
- 2: 素材管理（第三步）
- 3: 视频编辑（第四步）

### 2. JSON数据存储
选择JSON而非数据库:
- ✅ 轻量级,易于备份和版本控制
- ✅ 人类可读,便于调试
- ✅ 无需额外依赖
- ⚠️ 不适合大规模数据（v5.0可能改用数据库）

### 3. 素材匹配算法
使用评分系统(0-100分):
```
总分 = 类型匹配(30) + 标签重叠(30) + 关键词(30) + 评分加成(10) + 使用历史(10)
```

### 4. VideoComposer设计
- 智能模式: 自动推荐素材
- 手动模式: 用户指定素材映射
- 预览模式: 不实际合成,只显示推荐

## 📊 数据结构

### 主题数据结构
```json
{
  "id": "uuid",
  "title": "主题标题",
  "description": "主题描述",
  "field": "领域",
  "audience": "目标受众",
  "difficulty": "难度",
  "keywords": ["关键词"],
  "rating": 5,
  "created_at": "时间戳"
}
```

### 脚本数据结构
```json
{
  "title": "脚本标题",
  "sections": [
    {
      "section_name": "章节名",
      "duration": 5.0,
      "narration": "旁白文字",
      "visual_notes": "视觉提示"
    }
  ],
  "total_duration": 30.0,
  "metadata": {}
}
```

### 素材数据结构
```json
{
  "id": "uuid",
  "name": "素材名称",
  "type": "image|video|audio",
  "file_path": "路径",
  "tags": ["标签"],
  "category": "分类",
  "rating": 5,
  "used_count": 0,
  "created_at": "时间戳"
}
```

## 🚀 开发工作流

### 添加新功能
1. **规划**: 确定功能属于哪个模块
2. **实现**: 在对应模块添加功能
3. **集成**: 在main.py添加菜单选项
4. **测试**: 手动测试所有路径
5. **文档**: 更新相关文档

### 修复Bug
1. **定位**: 确定问题所在模块
2. **重现**: 找到最小复现步骤
3. **修复**: 修改代码并测试
4. **验证**: 确保不影响其他功能
5. **记录**: 在代码注释中说明

### 发布新版本
1. **更新版本号**: main.py中的横幅
2. **更新文档**: 创建VERSION_X.X_SUMMARY.md
3. **更新README**: 反映新功能
4. **更新requirements.txt**: 如有新依赖
5. **测试**: 完整测试所有功能

## 🔮 未来规划

### ✅ V5.0 功能（已完成）
- [x] 语音合成（TTS）- 将旁白转为语音（支持OpenAI TTS和Edge TTS）
- [x] 字幕生成 - SRT/ASS格式,时间轴对齐
- [x] 完整AI工作流 - 从主题到带语音字幕的成品视频
- [x] 17种中文TTS声音选择
- [x] 音频后期处理（BGM混音）

### V6.0+ 功能（计划中）
- [ ] 多语言支持 - 自动翻译和多语言配音
- [ ] 性能优化 - 多线程,GPU加速
- [ ] Web界面 - 替代CLI
- [ ] 本地AI模型 - 减少API依赖
- [ ] 数据库存储 - 替代JSON

### 技术债务
- [ ] 添加单元测试（当前仅手动测试）
- [ ] 异步IO支持（提高API调用效率）
- [ ] 日志系统（当前使用print）
- [ ] 配置验证（JSON schema）
- [ ] 错误追踪（Sentry等）

## ⚠️ 已知限制

### 技术限制
1. **视频处理速度**: 长视频合成耗时较长（受moviepy性能限制）
2. **中文文字渲染**: 依赖ImageMagick，配置复杂
3. **内存使用**: 处理大文件时内存占用高
4. **API依赖**: OpenAI服务不可用时系统无法工作

### 设计限制
1. **单用户**: 当前不支持多用户和权限管理
2. **本地运行**: 未考虑分布式部署
3. **同步处理**: 一次处理一个任务
4. **JSON存储**: 不适合大规模数据

## 🐛 常见问题

### 导入错误
**问题**: `ImportError: No module named 'xxx'`
**解决**:
```bash
pip install -r requirements.txt
```

### FFmpeg错误
**问题**: `FileNotFoundError: ffmpeg not found`
**解决**:
```bash
sudo apt-get install ffmpeg  # Ubuntu
brew install ffmpeg          # macOS
```

### API调用失败
**问题**: `openai.error.AuthenticationError` 或 API认证错误
**解决**:
- 检查`config/settings.json`中的`api_key`
- 确认`provider`设置正确 (openai/glm/anthropic)
- GLM用户需在 https://open.bigmodel.cn/ 获取API Key
- 确认`base_url`配置正确：
  - OpenAI: `https://api.openai.com/v1`
  - GLM: `https://open.bigmodel.cn/api/paas/v4/`

### 模块导入冲突
**问题**: 多个`generator.py`导致导入错误
**解决**: 使用importlib.util动态加载（已在main.py实现）

## 📚 关键文件说明

### config/settings.json
- 主配置文件,包含所有可配置项
- **重要**: 不要提交到Git（包含API密钥）
- 使用`settings.example.json`作为模板

### config/templates.json
- AI提示词模板
- 包含主题生成、脚本生成、图片生成的提示词
- 可自定义扩展

### main.py
- CLI入口和主菜单
- 使用importlib.util动态加载各模块（避免命名冲突）
- 包含13个菜单功能

### scripts/*/generator.py
- 各模块的核心生成逻辑
- 注意: 多个模块有同名文件,需注意导入

### scripts/*/manager.py
- 数据管理逻辑（CRUD）
- 主题管理器、素材管理器

## 🔍 调试技巧

### 启用详细日志
在代码中添加:
```python
import traceback
try:
    # 代码
except Exception as e:
    print(f"错误: {str(e)}")
    traceback.print_exc()
```

### 检查API调用
```python
# 在ai_client.py中添加
print(f"API请求: {prompt[:100]}...")
print(f"API响应: {response[:100]}...")
```

### 验证配置加载
```python
import json
with open('config/settings.json') as f:
    config = json.load(f)
    print(json.dumps(config, indent=2, ensure_ascii=False))
```

### 测试素材匹配
使用菜单12（预览素材推荐）查看匹配详情和评分

## 💡 开发建议

### 对于Claude AI助手

1. **理解上下文**:
   - 项目处于v4.0,已实现完整工作流
   - 下一步是v5.0（语音、字幕、性能优化）

2. **代码风格**:
   - 使用中文注释
   - 保持与现有代码一致的风格
   - 添加类型提示

3. **文档同步**:
   - 添加新功能时,同步更新相关文档
   - 创建新版本时,编写VERSION_X.X_SUMMARY.md

4. **测试指引**:
   - 提供详细的测试步骤
   - 说明预期输出和可能的错误

5. **用户体验**:
   - 提供友好的错误消息
   - 添加进度提示（如"⏳ 正在生成..."）
   - 使用emoji增强可读性

## 📞 维护者信息

**主要维护**: Claude AI + 用户协作开发
**开发周期**: 2024 Q4 - 2025 Q1
**当前状态**: ✅ V4.0已完成,运行稳定

## 🎯 核心原则

1. **用户友好**: CLI界面清晰,错误提示友好
2. **模块化**: 各模块独立,易于扩展
3. **可配置**: 通过配置文件控制行为
4. **文档完善**: 从快速开始到深度指南全覆盖
5. **AI驱动**: 充分利用AI能力,减少人工工作

---

**此文档旨在帮助Claude AI理解项目结构和开发规范,以便更好地协助开发和维护。**

**最后更新**: 2025年1月 (V5.0)
