# 视频编辑器使用指南

## 📖 目录

1. [概述](#概述)
2. [基础使用](#基础使用)
3. [智能视频合成](#智能视频合成)
4. [转场效果](#转场效果)
5. [高级功能](#高级功能)
6. [配置说明](#配置说明)
7. [常见问题](#常见问题)

---

## 概述

视频编辑器模块（`3_video_editor`）提供了完整的视频制作能力,从基础的视频剪辑到智能的脚本驱动视频合成。

### 核心模块

```
scripts/3_video_editor/
├── editor.py        # 基础视频编辑功能
├── composer.py      # 智能视频合成器
└── transitions.py   # 转场效果库
```

### 依赖要求

```bash
# Python包
pip install moviepy imageio imageio-ffmpeg Pillow numpy

# 系统依赖
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# ImageMagick (可选,用于文字效果)
sudo apt-get install imagemagick  # Ubuntu
brew install imagemagick           # macOS
```

---

## 基础使用

### 1. VideoEditor - 基础视频编辑

#### 创建图片幻灯片

```python
from scripts.3_video_editor.editor import VideoEditor

editor = VideoEditor()

# 创建简单幻灯片
video_path = editor.create_simple_video(
    images=[
        'materials/images/intro.jpg',
        'materials/images/scene1.jpg',
        'materials/images/scene2.jpg'
    ],
    durations=[3, 5, 4],  # 每张图显示时长（秒）
    output_filename='my_slideshow.mp4',
    fps=24
)

print(f"视频已生成: {video_path}")
```

#### 为视频添加音频

```python
# 添加背景音乐
video_with_audio = editor.add_audio_to_video(
    video_path='output/videos/my_video.mp4',
    audio_path='materials/audio/background.mp3',
    output_filename='video_with_music.mp4'
)
```

#### 添加文字叠加

```python
# 在视频上添加文字
video_with_text = editor.add_text_overlay(
    video_path='output/videos/my_video.mp4',
    text='量子计算的奇妙世界',
    position=(50, 50),      # 左上角坐标
    fontsize=60,
    color='white',
    duration=5              # 文字显示5秒
)
```

#### 裁剪视频

```python
# 提取视频片段
trimmed = editor.trim_video(
    video_path='output/videos/long_video.mp4',
    start_time=10.5,        # 从10.5秒开始
    end_time=25.0,          # 到25秒结束
    output_filename='excerpt.mp4'
)
```

#### 拼接多个视频

```python
# 合并视频
combined = editor.concatenate_videos(
    video_paths=[
        'output/videos/part1.mp4',
        'output/videos/part2.mp4',
        'output/videos/part3.mp4'
    ],
    output_filename='complete.mp4'
)
```

#### 获取视频信息

```python
info = editor.get_video_info('output/videos/my_video.mp4')

print(f"时长: {info['duration']}秒")
print(f"帧率: {info['fps']}")
print(f"分辨率: {info['width']}x{info['height']}")
print(f"是否有音频: {info['has_audio']}")
```

---

## 智能视频合成

### VideoComposer - 从脚本生成视频

VideoComposer是最强大的功能,能根据脚本自动生成完整视频。

### 基本用法

```python
from scripts.3_video_editor.composer import VideoComposer
import json

# 初始化合成器
composer = VideoComposer()

# 加载脚本
with open('output/scripts/my_script.json', 'r', encoding='utf-8') as f:
    script = json.load(f)

# 自动合成视频
video_path = composer.compose_from_script(
    script=script,
    auto_select_materials=True,  # 自动匹配素材
    output_filename='final_video.mp4'
)

print(f"视频已生成: {video_path}")
```

### 工作原理

1. **解析脚本**: 读取所有章节信息
2. **素材匹配**: 为每个章节智能推荐素材
3. **创建片段**: 根据素材类型创建视频片段
4. **添加文字**: 在片段上叠加旁白文字
5. **拼接合成**: 合并所有片段
6. **添加音频**: 添加背景音乐（如果配置）
7. **导出视频**: 输出最终视频文件

### 素材匹配评分

系统使用智能评分算法匹配素材:

```python
匹配度 = 类型匹配(30分) + 标签重叠(30分) + 关键词(30分) + 评分加成(10分) + 使用历史(10分)
```

**示例**:

脚本章节:
```json
{
  "section_name": "量子叠加原理",
  "narration": "量子叠加是量子力学的核心概念...",
  "visual_notes": "展示薛定谔的猫实验示意图",
  "duration": 8
}
```

素材库中有:
- `materials/quantum_cat.jpg` - 标签: [量子, 薛定谔的猫, 实验]
- `materials/atom.jpg` - 标签: [原子, 物理]

评分结果:
- `quantum_cat.jpg`: **85分** (类型匹配+标签高度重叠+关键词匹配)
- `atom.jpg`: **45分** (类型匹配+部分关键词)

系统选择 `quantum_cat.jpg`

### 预览素材推荐

在实际合成前预览推荐:

```python
recommendations = composer.preview_material_recommendations(script)

# 输出示例:
# 1. 引言
#    1) 量子芯片特写 (匹配度: 92%)
#    2) 计算机演进 (匹配度: 78%)
# 2. 第一章
#    1) 薛定谔的猫 (匹配度: 85%)
#    ...
```

### 自定义素材映射

如果自动匹配不满意,可手动指定:

```python
# 为每个章节指定素材
material_mapping = {
    0: 'materials/images/custom_intro.jpg',    # 第0章
    1: 'materials/videos/quantum_demo.mp4',    # 第1章
    2: 'materials/images/superposition.png',   # 第2章
    # ...
}

video_path = composer.compose_with_custom_materials(
    script=script,
    material_mapping=material_mapping,
    output_filename='custom_video.mp4'
)
```

### 获取合成信息

不实际合成,只预览信息:

```python
info = composer.get_composition_info(script)

print(f"标题: {info['title']}")
print(f"章节数: {info['total_sections']}")
print(f"预估时长: {info['estimated_duration']}秒")
print(f"预估文件大小: {info['estimated_file_size_mb']} MB")

for section in info['sections']:
    print(f"  {section['index']}. {section['name']} ({section['duration']}秒)")
```

---

## 转场效果

### TransitionLibrary - 专业转场效果

```python
from scripts.3_video_editor.transitions import TransitionLibrary
from moviepy.editor import ImageClip
```

### 淡入淡出

```python
# 淡入
clip = ImageClip('image.jpg').set_duration(5)
clip_with_fade = TransitionLibrary.fade_in(clip, duration=1.0)

# 淡出
clip_with_fade = TransitionLibrary.fade_out(clip, duration=1.0)
```

### 滑动效果

```python
# 从左侧滑入
clip = TransitionLibrary.slide_in(
    clip,
    direction='left',  # 'left', 'right', 'top', 'bottom'
    duration=1.5
)
```

### 缩放效果

```python
# 放大进入
clip = TransitionLibrary.zoom_in(
    clip,
    duration=2.0,
    zoom_ratio=1.5  # 最大放大到1.5倍
)

# 缩小进入
clip = TransitionLibrary.zoom_out(
    clip,
    duration=2.0,
    zoom_ratio=1.5  # 从1.5倍缩小到正常
)
```

### 旋转效果

```python
# 旋转进入
clip = TransitionLibrary.rotate_in(
    clip,
    duration=1.0,
    angle=360  # 旋转角度
)
```

### 批量应用转场

```python
clips = [clip1, clip2, clip3, clip4]

# 为所有片段应用淡入淡出
processed_clips = TransitionLibrary.apply_transition_sequence(
    clips,
    transition_type='fade',    # 'fade', 'slide', 'zoom', 'rotate', 'none'
    transition_duration=1.0
)

# 拼接
from moviepy.editor import concatenate_videoclips
final = concatenate_videoclips(processed_clips)
```

### 获取转场信息

```python
# 获取所有可用转场
transitions = TransitionLibrary.get_available_transitions()
# ['fade', 'slide', 'zoom', 'rotate', 'wipe', 'none']

# 获取详细信息
info = TransitionLibrary.get_transition_info()
print(info['fade']['name'])         # '淡入淡出'
print(info['fade']['description'])  # '片段通过渐变透明度平滑过渡'
print(info['fade']['suitable_for']) # '通用，适合大多数场景'
```

---

## 高级功能

### 自定义视频配置

编辑 `config/settings.json`:

```json
{
  "video": {
    "fps": 30,                           // 帧率
    "codec": "libx264",                  // 视频编码
    "audio_codec": "aac",                // 音频编码
    "resolution": [1920, 1080],          // 分辨率
    "default_image_duration": 5.0,       // 图片默认时长
    "transition_duration": 1.5,          // 转场时长
    "show_narration_text": true,         // 显示文字
    "text_size": 50,                     // 文字大小
    "default_bgm": "materials/audio/bgm.mp3",  // 背景音乐
    "estimated_bitrate_mb_per_min": 8.0  // 码率（用于估算大小）
  }
}
```

### 处理不同素材类型

```python
# 视频合成器自动识别素材类型

# 图片素材
material = 'materials/images/photo.jpg'
# → 创建ImageClip,设置持续时间

# 视频素材
material = 'materials/videos/clip.mp4'
# → 创建VideoFileClip
# → 如果视频太短,自动循环播放
# → 如果视频太长,裁剪到需要的长度
```

### 错误处理

```python
try:
    video_path = composer.compose_from_script(script)
except ImportError as e:
    print("moviepy未安装，请运行: pip install moviepy")
except FileNotFoundError as e:
    print(f"素材文件不存在: {e}")
except Exception as e:
    print(f"合成失败: {e}")
    import traceback
    traceback.print_exc()
```

### 性能优化建议

1. **使用合适的分辨率**
   ```json
   "resolution": [1280, 720]  // 720p (更快)
   "resolution": [1920, 1080] // 1080p (更慢但更清晰)
   ```

2. **调整帧率**
   ```json
   "fps": 24  // 电影标准 (较快)
   "fps": 30  // 常用标准 (平衡)
   "fps": 60  // 高帧率 (较慢)
   ```

3. **素材预处理**
   - 统一素材分辨率
   - 压缩过大的图片
   - 转换素材为相同格式

4. **批处理建议**
   - 一次处理一个视频
   - 避免同时运行多个合成任务
   - 合成大视频时关闭其他程序

---

## 配置说明

### 完整配置示例

```json
{
  "video": {
    "fps": 24,
    "codec": "libx264",
    "audio_codec": "aac",
    "resolution": [1920, 1080],
    "default_image_duration": 5.0,
    "transition_duration": 1.0,
    "show_narration_text": true,
    "text_size": 40,
    "default_bgm": "",
    "estimated_bitrate_mb_per_min": 5.0
  },
  "paths": {
    "videos": "./output/videos",
    "materials": "./materials"
  }
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `fps` | int | 24 | 视频帧率 |
| `codec` | string | libx264 | 视频编码器 |
| `audio_codec` | string | aac | 音频编码器 |
| `resolution` | array | [1920,1080] | 视频分辨率 |
| `default_image_duration` | float | 5.0 | 图片默认显示时长(秒) |
| `transition_duration` | float | 1.0 | 转场效果时长(秒) |
| `show_narration_text` | bool | true | 是否显示旁白文字 |
| `text_size` | int | 40 | 文字大小 |
| `default_bgm` | string | "" | 默认背景音乐路径 |
| `estimated_bitrate_mb_per_min` | float | 5.0 | 码率(MB/分钟) |

---

## 常见问题

### Q1: 视频合成很慢怎么办?

**A**:
1. 降低分辨率: `"resolution": [1280, 720]`
2. 降低帧率: `"fps": 24`
3. 减少章节数或时长
4. 使用更小的素材文件

### Q2: 文字显示乱码

**A**:
1. 确保安装ImageMagick
2. 配置ImageMagick支持中文字体
3. 或者设置 `"show_narration_text": false` 关闭文字

### Q3: 素材匹配不准确

**A**:
1. 使用 `preview_material_recommendations()` 预览
2. 给素材添加更精确的标签
3. 使用 `compose_with_custom_materials()` 手动指定

### Q4: 没有找到FFmpeg

**A**:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 1. 下载FFmpeg: https://ffmpeg.org/download.html
# 2. 解压到C:\ffmpeg
# 3. 添加C:\ffmpeg\bin到PATH环境变量
```

### Q5: 视频没有音频

**A**:
1. 检查是否配置了 `default_bgm`
2. 确认BGM文件路径正确
3. 使用 `add_audio_to_video()` 手动添加

### Q6: 内存不足错误

**A**:
1. 减少视频长度
2. 降低分辨率
3. 一次处理一个章节
4. 关闭其他程序释放内存

### Q7: 如何添加字幕?

**A**:
v4.0暂不支持SRT字幕,但可以使用 `add_text_overlay()`:

```python
# 为每个章节手动添加文字
for i, section in enumerate(sections):
    video = editor.add_text_overlay(
        video,
        text=section['narration'][:50],  # 限制长度
        duration=section['duration'],
        position=('center', 'bottom')
    )
```

字幕功能计划在v5.0实现。

### Q8: 能否导出其他格式?

**A**:
修改输出文件名后缀:

```python
video_path = composer.compose_from_script(
    script,
    output_filename='video.avi'  # .avi, .mov, .mkv等
)
```

moviepy支持多种格式,但建议使用.mp4以获得最佳兼容性。

---

## 📚 相关文档

- [完整文档](README.md)
- [快速开始](QUICKSTART.md)
- [v4.0更新说明](VERSION_4.0_SUMMARY.md)
- [素材管理指南](MATERIAL_MANAGER_GUIDE.md)

---

## 🎬 视频制作流程总结

```
1. 准备素材
   ↓
2. 生成或编写脚本
   ↓
3. (可选) 预览素材推荐
   ↓
4. 自动合成视频
   ↓
5. (可选) 手动调整
   ↓
6. 导出最终视频
```

**祝您制作出精彩的科普视频！** 🎉
