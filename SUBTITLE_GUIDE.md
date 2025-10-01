# 字幕生成系统使用指南

本指南详细介绍如何使用科普视频制作系统的字幕生成功能，包括SRT和ASS格式字幕的创建与时间轴对齐。

## 📋 目录

- [快速开始](#快速开始)
- [字幕格式](#字幕格式)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [时间轴对齐](#时间轴对齐)
- [字幕样式](#字幕样式)
- [常见问题](#常见问题)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pysrt
```

### 2. 配置字幕样式

编辑 `config/settings.json`:

```json
{
  "subtitle": {
    "font": "Arial",                // 字体
    "font_size": 48,                // 字号
    "font_color": "white",          // 字体颜色
    "bg_color": "black",            // 背景颜色
    "bg_opacity": 0.5,              // 背景透明度
    "position": "bottom",           // 位置: top/middle/bottom
    "language": "zh-CN"             // 语言
  }
}
```

### 3. 生成字幕

```bash
python main.py
# 选择菜单 16: 从脚本生成字幕
```

## 📄 字幕格式

### SRT格式（推荐）

SubRip格式，最通用的字幕格式。

**特点**:
- ✅ 兼容性极强（所有播放器支持）
- ✅ 文件小巧
- ✅ 易于编辑
- ⚠️ 样式控制有限

**示例**:
```srt
1
00:00:00,000 --> 00:00:05,500
你知道吗？量子计算机能够同时处理多个状态

2
00:00:05,500 --> 00:00:12,000
这种神奇的能力，来自于量子力学的叠加原理
```

### ASS格式（高级）

Advanced SubStation Alpha格式，支持丰富样式。

**特点**:
- ✅ 支持复杂样式（字体、颜色、位置、特效）
- ✅ 专业级字幕效果
- ⚠️ 文件较大
- ⚠️ 兼容性略差

**示例**:
```ass
[Script Info]
Title: 量子计算的奇妙世界
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, ...
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,...

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.50,Default,,0,0,0,,你知道吗？量子计算机能够同时处理多个状态
```

## ⚙️ 配置说明

### 完整配置示例

```json
{
  "subtitle": {
    "font": "Microsoft YaHei",           // 中文字体推荐
    "font_size": 48,                     // 1080p推荐48，720p推荐32
    "font_color": "white",               // 颜色：white/black/yellow/自定义
    "outline_color": "black",            // 描边颜色（ASS）
    "outline_width": 2,                  // 描边宽度（ASS）
    "bg_color": "black",                 // 背景颜色
    "bg_opacity": 0.5,                   // 背景透明度 (0.0-1.0)
    "position": "bottom",                // 位置
    "margin_v": 50,                      // 垂直边距（像素）
    "margin_h": 50,                      // 水平边距（像素）
    "language": "zh-CN",                 // 语言代码
    "max_chars_per_line": 25,           // 每行最大字符数
    "max_lines": 2                       // 最大行数
  }
}
```

### 参数说明

| 参数 | 类型 | 说明 | 推荐值 |
|-----|------|------|--------|
| `font` | string | 字体名称 | `Microsoft YaHei`（中文） |
| `font_size` | int | 字号 | `48`（1080p）/ `32`（720p） |
| `font_color` | string | 字体颜色 | `white` / `yellow` |
| `bg_color` | string | 背景颜色 | `black` |
| `bg_opacity` | float | 背景透明度 | `0.5` |
| `position` | string | 位置 | `bottom` |
| `max_chars_per_line` | int | 每行字符数 | `25` |

## 🎯 使用方法

### 菜单16: 从脚本生成字幕

**功能**: 根据脚本内容自动生成时间轴对齐的字幕文件

**步骤**:

1. 启动程序
   ```bash
   python main.py
   ```

2. 选择菜单 **16**

3. 选择脚本文件
   - 从 `output/scripts/` 目录选择

4. 选择对齐方式
   - **方式1**: 使用TTS音频对齐（推荐）
     - 精确匹配语音时长
     - 字幕与语音完美同步
   - **方式2**: 估算时长对齐
     - 基于中文语速（~2.5字/秒）
     - 适用于无TTS的场景

5. 选择字幕格式
   - **SRT**: 通用推荐
   - **ASS**: 需要高级样式

6. 等待生成
   - 系统自动分割长文本
   - 智能断句（基于标点符号）
   - 生成时间轴

7. 完成
   - 字幕保存在 `output/subtitles/`
   - 可直接用于视频合成

**输出示例**:
```
output/subtitles/
├── 量子计算的奇妙世界.srt
└── 量子计算的奇妙世界.ass
```

## ⏱️ 时间轴对齐

### 方法1: 基于TTS音频对齐（推荐）

使用已生成的TTS音频文件进行精确时间对齐。

**优点**:
- ✅ 字幕与语音完美同步
- ✅ 时长精确到毫秒
- ✅ 适合所有语速

**使用**:
```bash
# 1. 先生成TTS音频（菜单14）
python main.py -> 菜单14 -> 选择脚本

# 2. 再生成字幕（菜单16）
python main.py -> 菜单16 -> 选择同一脚本 -> 选择"使用TTS对齐"
```

**工作原理**:
```python
# 读取TTS元数据
{
  "sections": [
    {
      "section_name": "hook",
      "duration": 12.5,    # TTS实际时长
      "start_time": 0.0,
      "end_time": 12.5
    }
  ]
}

# 生成字幕
1
00:00:00,000 --> 00:00:12,500
你知道吗？量子计算机能够同时处理多个状态
```

### 方法2: 估算时长对齐

基于中文平均语速估算时间轴。

**优点**:
- ✅ 无需TTS音频
- ✅ 快速生成

**缺点**:
- ⚠️ 时间可能不精确
- ⚠️ 需要后期调整

**估算公式**:
```python
# 中文语速约2.5字/秒
duration = len(text) / 2.5

# 示例：
text = "量子计算机是一种新型计算设备"  # 14字
duration = 14 / 2.5 = 5.6秒
```

**调整建议**:
- 科普教育类：2.0字/秒（讲解详细）
- 通用内容：2.5字/秒（标准）
- 快节奏内容：3.0字/秒（科技资讯）

## 🎨 字幕样式

### SRT样式（有限）

SRT格式本身不支持样式，但播放器通常允许自定义：

**VLC播放器**:
1. 工具 → 偏好设置 → 字幕/OSD
2. 设置字体、大小、颜色等

**网络播放器**:
大多数在线播放器会使用默认样式渲染SRT字幕。

### ASS样式（丰富）

ASS格式支持完整样式控制：

**样式定义**:
```ass
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, ...

Style: Default,Microsoft YaHei,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,50,1
```

**参数说明**:
- `Fontname`: 字体名称
- `Fontsize`: 字号
- `PrimaryColour`: 主颜色（&HAABBGGRR格式）
- `OutlineColour`: 描边颜色
- `BackColour`: 背景颜色
- `Bold/Italic`: 粗体/斜体
- `Outline`: 描边宽度
- `Shadow`: 阴影深度
- `MarginL/R/V`: 左/右/垂直边距

**颜色代码**:
```
白色: &H00FFFFFF
黑色: &H00000000
黄色: &H0000FFFF
红色: &H000000FF
蓝色: &H00FF0000
绿色: &H0000FF00
```

### 自定义样式示例

**专业科普风格**:
```json
{
  "subtitle": {
    "font": "Microsoft YaHei",
    "font_size": 52,
    "font_color": "white",
    "outline_color": "black",
    "outline_width": 3,
    "bg_color": "black",
    "bg_opacity": 0.6,
    "position": "bottom",
    "margin_v": 60
  }
}
```

**轻松娱乐风格**:
```json
{
  "subtitle": {
    "font": "Comic Sans MS",
    "font_size": 48,
    "font_color": "yellow",
    "outline_color": "black",
    "outline_width": 2,
    "position": "bottom"
  }
}
```

## 🔧 高级功能

### 1. 智能文本分割

系统自动将长文本分割为多个字幕条目：

**示例**:
```python
# 原始文本（过长）
"量子计算机是一种全新的计算设备，它基于量子力学原理工作，能够利用量子比特的叠加态和纠缠特性，实现传统计算机难以完成的计算任务。"

# 自动分割（每行≤25字）
字幕1: "量子计算机是一种全新的计算设备"
字幕2: "它基于量子力学原理工作"
字幕3: "能够利用量子比特的叠加态和纠缠特性"
字幕4: "实现传统计算机难以完成的计算任务"
```

**分割规则**:
1. 按标点符号断句（。！？，；）
2. 每条字幕≤25字（可配置）
3. 最多2行（可配置）
4. 保持语义完整性

### 2. 时间轴微调

手动调整生成的字幕时间：

```python
# 使用pysrt库
import pysrt

# 加载字幕
subs = pysrt.open('output/subtitles/video.srt')

# 整体延迟0.5秒
subs.shift(seconds=0.5)

# 调整单条字幕
subs[0].start.seconds += 1
subs[0].end.seconds += 1

# 保存
subs.save('output/subtitles/video_adjusted.srt')
```

### 3. 字幕效果（ASS）

添加特殊效果：

**淡入淡出**:
```ass
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\fad(500,500)}你好，世界
```

**滚动字幕**:
```ass
Dialogue: 0,0:00:00.00,0:00:10.00,Default,,0,0,0,,{\move(1920,540,0,540)}滚动文字
```

**卡拉OK效果**:
```ass
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\k100}你{\k100}好{\k100}世{\k100}界
```

### 4. 双语字幕

生成中英双语字幕：

```srt
1
00:00:00,000 --> 00:00:05,000
量子计算的奇妙世界
The Wonderful World of Quantum Computing

2
00:00:05,000 --> 00:00:10,000
你知道吗？量子计算机与众不同
Did you know? Quantum computers are different
```

## ❓ 常见问题

### Q: 字幕不同步怎么办？

**A**: 如果字幕与视频不同步：

1. **使用TTS对齐**（最可靠）
   ```bash
   菜单14 -> 生成TTS
   菜单16 -> 选择TTS对齐
   ```

2. **手动调整**
   ```python
   import pysrt
   subs = pysrt.open('video.srt')
   subs.shift(seconds=0.5)  # 延迟0.5秒
   subs.save('video_fixed.srt')
   ```

3. **使用字幕编辑器**
   - Aegisub（推荐）
   - Subtitle Edit

### Q: 字幕显示乱码？

**A**: 编码问题，解决方法：

```bash
# 检查文件编码
file -i output/subtitles/video.srt

# 转换为UTF-8
iconv -f GBK -t UTF-8 video.srt > video_utf8.srt

# Python中确保UTF-8编码
with open('video.srt', 'r', encoding='utf-8') as f:
    content = f.read()
```

### Q: 字幕在视频中不显示？

**A**: 检查以下几点：

1. **格式是否正确**
   ```bash
   # 验证SRT格式
   python -c "import pysrt; pysrt.open('video.srt')"
   ```

2. **文件名是否匹配**
   ```
   video.mp4
   video.srt    # 文件名要一致
   ```

3. **播放器是否支持**
   - VLC：支持SRT和ASS
   - 网络播放器：通常仅支持SRT

### Q: 如何调整字幕位置？

**A**:

**SRT**: 播放器设置
- VLC: 工具 → 偏好设置 → 字幕/OSD → 位置

**ASS**: 修改样式
```ass
Style: Default,...,Alignment=2  # 底部居中
# Alignment: 1=左下 2=底部中 3=右下 4=左中 5=正中 6=右中 7=左上 8=顶部中 9=右上
```

### Q: 每行字数太多/太少？

**A**: 调整配置：

```json
{
  "subtitle": {
    "max_chars_per_line": 20,    // 减少每行字数
    "max_lines": 2               // 允许多行
  }
}
```

重新生成字幕即可。

### Q: 字幕文件太大？

**A**:
- SRT文件通常很小（<100KB）
- ASS文件较大但不超过1MB
- 如果异常大，检查是否有重复内容

```bash
# 检查文件大小
ls -lh output/subtitles/
```

## 💡 最佳实践

### 1. 选择合适的格式

| 场景 | 推荐格式 | 原因 |
|-----|---------|------|
| 通用视频 | SRT | 兼容性最好 |
| 专业制作 | ASS | 样式丰富 |
| 网络发布 | SRT | 文件小、加载快 |
| 本地播放 | ASS | 效果最佳 |

### 2. 字幕文本优化

**原则**:
- ✅ 简洁明了（删除冗余词）
- ✅ 分段清晰（按语义断句）
- ✅ 易读性优先（避免过长句子）

**示例**:
```python
# ❌ 不好的字幕
"在这个令人惊叹的视频中，我们将会一起探讨关于量子计算机的工作原理以及它在未来可能带来的巨大影响"

# ✅ 优化后的字幕
"今天我们聊聊量子计算"
"它的工作原理和未来影响"
```

### 3. 时间轴设置

**推荐时长**:
- 最短显示时间：1秒
- 最长显示时间：7秒
- 字幕间隔：0.1-0.3秒

**公式**:
```python
display_time = max(1.0, min(len(text) / 2.5, 7.0))
```

### 4. 测试工作流

```bash
# 1. 生成TTS（菜单14）
python main.py -> 14 -> 选择脚本

# 2. 生成字幕（菜单16）
python main.py -> 16 -> 选择脚本 -> TTS对齐 -> SRT

# 3. 预览字幕
# 使用VLC或其他播放器检查

# 4. 调整（如需要）
# 使用Aegisub微调时间轴

# 5. 生成视频（菜单17）
python main.py -> 17 -> 选择脚本+TTS+字幕
```

### 5. 版本管理

```bash
# 保留不同版本
output/subtitles/
├── 量子计算_v1.srt
├── 量子计算_v2_adjusted.srt
└── 量子计算_final.srt
```

## 📚 相关文档

- [TTS语音合成指南](TTS_GUIDE.md)
- [视频编辑指南](VIDEO_EDITOR_GUIDE.md)
- [完整工作流示例](EXAMPLES.md)
- [V5.0更新说明](VERSION_5.0_SUMMARY.md)

## 🔗 外部资源

- [pysrt文档](https://github.com/byroot/pysrt)
- [SRT格式规范](https://en.wikipedia.org/wiki/SubRip)
- [ASS格式规范](http://www.tcax.org/docs/ass-specs.htm)
- [Aegisub字幕编辑器](http://www.aegisub.org/)

## 🛠️ 推荐工具

- **Aegisub**: 专业字幕编辑器（支持ASS）
- **Subtitle Edit**: 字幕编辑和转换
- **VLC Media Player**: 字幕预览和测试
- **pysrt**: Python字幕处理库

---

**版本**: V5.0
**最后更新**: 2025年1月

如有问题或建议，请提交Issue或联系维护者。
