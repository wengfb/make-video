# TTS语音合成系统使用指南

本指南详细介绍如何使用科普视频制作系统的TTS（Text-to-Speech）语音合成功能。

## 📋 目录

- [快速开始](#快速开始)
- [TTS提供商](#tts提供商)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [声音选择](#声音选择)
- [高级功能](#高级功能)
- [常见问题](#常见问题)

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Edge TTS（免费，推荐用于测试）
pip install edge-tts

# 或使用OpenAI TTS（需要API密钥）
pip install openai
```

### 2. 配置TTS

编辑 `config/settings.json`:

```json
{
  "tts": {
    "provider": "edge",                    // TTS提供商: "edge" 或 "openai"
    "voice": "zh-CN-XiaoxiaoNeural",      // 默认声音
    "speed": 1.0,                          // 语速 (0.25-4.0)
    "enable_bgm_mixing": true,             // 启用BGM混音
    "bgm_volume": 0.2                      // BGM相对音量
  }
}
```

### 3. 生成语音

```bash
python main.py
# 选择菜单 14: 从脚本生成TTS语音
```

## 🎙️ TTS提供商

### Edge TTS（推荐）

**优点**:
- ✅ 完全免费
- ✅ 无需API密钥
- ✅ 17种高质量中文声音
- ✅ 支持语速调节

**缺点**:
- ⚠️ 需要稳定网络连接
- ⚠️ 可能有轻微机械感

**配置**:
```json
{
  "tts": {
    "provider": "edge",
    "voice": "zh-CN-XiaoxiaoNeural"
  }
}
```

### OpenAI TTS

**优点**:
- ✅ 音质非常自然
- ✅ 专业级语音合成
- ✅ 稳定可靠

**缺点**:
- ❌ 需要付费（约$0.015/分钟）
- ❌ 需要API密钥
- ⚠️ 中文声音选择较少

**配置**:
```json
{
  "tts": {
    "provider": "openai",
    "model": "tts-1",
    "api_key": "YOUR_OPENAI_API_KEY",
    "voice": "alloy"
  }
}
```

## ⚙️ 配置说明

### 完整配置示例

```json
{
  "tts": {
    "provider": "edge",                    // TTS提供商
    "model": "tts-1",                      // OpenAI模型（仅OpenAI）
    "api_key": "",                         // OpenAI API密钥（仅OpenAI）
    "voice": "zh-CN-XiaoxiaoNeural",      // 默认声音
    "speed": 1.0,                          // 语速倍率
    "enable_bgm_mixing": true,             // 启用BGM混音
    "bgm_volume": 0.2                      // BGM音量（0.0-1.0）
  },

  "paths": {
    "audio": "./materials/audio"           // 音频输出路径
  }
}
```

### 参数说明

| 参数 | 类型 | 说明 | 默认值 |
|-----|------|------|--------|
| `provider` | string | TTS提供商：`edge` 或 `openai` | `edge` |
| `model` | string | OpenAI模型（仅OpenAI需要） | `tts-1` |
| `api_key` | string | API密钥（仅OpenAI需要） | `""` |
| `voice` | string | 声音ID | `zh-CN-XiaoxiaoNeural` |
| `speed` | float | 语速倍率（0.25-4.0） | `1.0` |
| `enable_bgm_mixing` | boolean | 是否启用BGM混音 | `true` |
| `bgm_volume` | float | BGM相对音量（0.0-1.0） | `0.2` |

## 🎯 使用方法

### 菜单14: 从脚本生成TTS语音

**功能**: 为脚本的每个章节自动生成语音文件

**步骤**:

1. 启动程序
   ```bash
   python main.py
   ```

2. 选择菜单 **14**

3. 选择脚本文件
   - 从 `output/scripts/` 目录选择

4. 等待生成
   - 系统会为每个章节生成独立音频
   - 显示实时进度

5. 完成
   - 音频保存在 `materials/audio/tts/[脚本名]/`
   - 生成元数据JSON文件供后续使用

**输出示例**:
```
materials/audio/tts/量子计算的奇妙世界/
├── section_0_hook.mp3
├── section_1_introduction.mp3
├── section_2_background.mp3
├── ...
└── metadata.json
```

### 菜单15: 管理TTS语音文件

**功能**: 查看、管理和合并TTS音频文件

**子功能**:

1. **查看所有语音**
   - 列出所有已生成的TTS音频
   - 显示时长、章节数等信息

2. **查看统计信息**
   - 总文件数
   - 总时长
   - 平均时长

3. **合并音频文件**
   - 将多个章节音频合并为单个文件
   - 自动处理间隔时间

4. **删除语音文件**
   - 清理不需要的音频文件

## 🎤 声音选择

### Edge TTS中文声音

| 声音ID | 名称 | 性别 | 风格 | 推荐场景 |
|--------|------|------|------|----------|
| `zh-CN-XiaoxiaoNeural` | 晓晓 | 女 | 温柔、清晰 | **通用推荐** |
| `zh-CN-YunxiNeural` | 云希 | 男 | 沉稳、专业 | 科技、历史 |
| `zh-CN-YunyangNeural` | 云扬 | 男 | 活力、年轻 | 娱乐、趣味 |
| `zh-CN-XiaoyiNeural` | 晓依 | 女 | 亲切、自然 | 生活、教育 |
| `zh-CN-YunjianNeural` | 云健 | 男 | 有力、激昂 | 体育、军事 |
| `zh-CN-XiaochenNeural` | 晓辰 | 女 | 知性、优雅 | 文化、艺术 |
| `zh-CN-XiaohanNeural` | 晓涵 | 女 | 温暖、治愈 | 故事、情感 |

**查看完整列表**:
```bash
# 使用edge-tts命令
edge-tts --list-voices | grep zh-CN
```

### OpenAI TTS声音

| 声音ID | 特点 | 推荐场景 |
|--------|------|----------|
| `alloy` | 中性、清晰 | 通用 |
| `echo` | 男性、沉稳 | 专业内容 |
| `fable` | 英式、温暖 | 故事叙述 |
| `onyx` | 男性、深沉 | 严肃话题 |
| `nova` | 女性、活力 | 年轻向内容 |
| `shimmer` | 女性、柔和 | 轻松主题 |

## 🔧 高级功能

### 1. 自定义语速

```json
{
  "tts": {
    "speed": 1.2    // 加快20%
  }
}
```

**推荐语速**:
- 0.8-0.9: 学习教育类（讲解详细）
- 1.0: 标准语速（推荐）
- 1.1-1.3: 快节奏内容（科技资讯）
- 1.5+: 快速回顾/总结

### 2. BGM混音

TTS生成的语音可以自动与背景音乐混合：

```json
{
  "tts": {
    "enable_bgm_mixing": true,
    "bgm_volume": 0.2    // BGM音量为TTS的20%
  },

  "video": {
    "default_bgm": "materials/audio/bgm.mp3"
  }
}
```

**工作原理**:
1. TTS语音生成后保持原音量
2. 视频合成时自动降低BGM音量
3. 确保TTS清晰可听

### 3. 批量生成

一次性为多个脚本生成TTS：

```python
# 示例：批量生成脚本
from scripts.4_tts_generator.generator import TTSGenerator

generator = TTSGenerator()

scripts = [
    "output/scripts/script1.json",
    "output/scripts/script2.json",
    "output/scripts/script3.json"
]

for script_path in scripts:
    result = generator.generate_speech_from_script(script_path)
    print(f"✓ {result['title']}: {result['total_duration']}秒")
```

### 4. 时长精确控制

TTS会自动记录每个章节的精确时长：

```json
{
  "sections": [
    {
      "section_name": "hook",
      "text": "你知道吗...",
      "audio_file": "section_0_hook.mp3",
      "duration": 12.5    // 精确时长（秒）
    }
  ]
}
```

这些时长信息会被字幕生成器使用，确保字幕与语音完美同步。

## ❓ 常见问题

### Q: Edge TTS连接失败？

**A**: Edge TTS依赖微软服务器，可能受网络影响：

```bash
# 测试连接
edge-tts --text "测试" --write-media test.mp3

# 如果失败，尝试：
# 1. 检查网络连接
# 2. 稍后重试
# 3. 切换到OpenAI TTS
```

### Q: 生成的语音有停顿？

**A**: 检查脚本文本格式：

- ✅ 使用标准标点符号（。！？）
- ✅ 避免过长的句子（建议<50字）
- ❌ 避免特殊字符和emoji

### Q: 如何更换声音？

**A**: 修改配置文件：

```json
{
  "tts": {
    "voice": "zh-CN-YunxiNeural"    // 更换为男声
  }
}
```

重新生成TTS即可。

### Q: OpenAI TTS费用如何？

**A**: 根据生成时长计费：

| 时长 | 费用（约） |
|------|----------|
| 1分钟 | $0.015 |
| 3分钟视频 | $0.045 |
| 100个3分钟视频 | $4.50 |

**建议**: 测试阶段使用Edge TTS，正式发布使用OpenAI TTS。

### Q: 如何提升TTS音质？

**A**:
1. **使用OpenAI TTS**（最有效）
2. **优化脚本文本**：
   - 使用自然口语化表达
   - 适当断句
   - 避免生僻词
3. **后期处理**：
   - 添加适当BGM
   - 使用音频压缩
   - 调整均衡器

### Q: TTS支持多语言吗？

**A**:
- Edge TTS: 支持40+语言
- OpenAI TTS: 支持多语言（但主要针对英语优化）

当前系统主要针对中文优化，其他语言支持在V6.0规划中。

### Q: 生成的音频在哪里？

**A**:
- 位置：`materials/audio/tts/[脚本名]/`
- 格式：MP3
- 元数据：同目录下的 `metadata.json`

```bash
# 查看所有TTS音频
ls materials/audio/tts/
```

## 💡 最佳实践

### 1. 选择合适的声音

- **科普教育**: 女声-晓晓、男声-云希（专业稳重）
- **轻松娱乐**: 女声-晓伊、男声-云扬（活泼亲切）
- **严肃内容**: 男声-云健（有力严肃）

### 2. 脚本优化

在生成TTS前，优化脚本文本：

```python
# ❌ 不好的文本
"量子计算机基于量子力学原理，利用量子比特（Qubit）的叠加态和纠缠特性..."

# ✅ 优化后的文本
"量子计算机，是一种神奇的计算设备。它基于量子力学原理工作。
什么是量子比特呢？简单说，它就像薛定谔的猫，可以同时处于两种状态。"
```

### 3. 测试工作流

```bash
# 1. 先测试单个章节
python main.py -> 菜单14 -> 选择测试脚本

# 2. 预览效果
# 播放生成的MP3文件

# 3. 满意后批量生成
```

### 4. 版本控制

```bash
# 保留不同版本的TTS
materials/audio/tts/
├── 量子计算_v1/
├── 量子计算_v2_男声/
└── 量子计算_final/
```

## 📚 相关文档

- [字幕生成指南](SUBTITLE_GUIDE.md)
- [视频编辑指南](VIDEO_EDITOR_GUIDE.md)
- [完整工作流示例](EXAMPLES.md)
- [V5.0更新说明](VERSION_5.0_SUMMARY.md)

## 🔗 外部资源

- [Edge TTS文档](https://github.com/rany2/edge-tts)
- [OpenAI TTS文档](https://platform.openai.com/docs/guides/text-to-speech)
- [语音合成最佳实践](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/how-to-speech-synthesis)

---

**版本**: V5.0
**最后更新**: 2025年1月

如有问题或建议，请提交Issue或联系维护者。
