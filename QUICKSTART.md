# 快速开始指南（5分钟）

本指南帮助你快速运行项目并生成第一个视频。

---

## ⚡ 最快路径（已有FFmpeg和API密钥）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化
python init_data.py

# 3. 配置API密钥（编辑 config/settings.json）
# "api_key": "sk-your-key-here"

# 4. 运行程序
python main.py
```

---

## 📋 详细步骤

### 步骤1：检查系统依赖 ✓

**必需：FFmpeg**

```bash
# 检查是否已安装
ffmpeg -version

# 如果未安装：
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

### 步骤2：安装Python依赖 ✓

```bash
cd make-video
pip install -r requirements.txt
```

### 步骤3：初始化项目 ✓

```bash
python init_data.py
# 按提示操作，选择 y 创建示例数据
```

### 步骤4：配置API密钥 ✓

```bash
# 编辑 config/settings.json
# 将 "api_key": "YOUR_API_KEY_HERE" 改为你的OpenAI密钥
```

获取API密钥：https://platform.openai.com/api-keys

### 步骤5：准备素材 🎨

```bash
# 下载10-20张科普图片到 materials/images/
# 推荐网站：unsplash.com, pexels.com

# 检查素材状态
python check_materials.py
```

### 步骤6：运行程序 🚀

```bash
python main.py
```

---

## 🎬 生成第一个视频

**推荐路径**（菜单13-完整工作流）：

1. 选择菜单 13
2. 生成新主题（约$0.01）
3. 选择一个主题
4. 生成脚本（约$0.08）
5. 合成视频（3-5分钟）
6. 完成！

**总成本**: ~$0.09
**总时间**: ~5分钟

---

## ❓ 常见问题

**Q: API调用失败？**
- 检查API密钥格式（sk-开头）
- 确认账户有余额

**Q: 素材推荐为空？**
```bash
python check_materials.py  # 检查素材库
```

**Q: FFmpeg未找到？**
- 确保已安装并添加到PATH
- Windows用户重启终端

**Q: 视频合成慢？**
- 正常现象，1分钟视频需5-15分钟
- 可降低分辨率到720p/640p

---

## 📚 更多文档

- [完整README](README.md) - 详细功能说明
- [素材准备指南](SETUP_MATERIALS.md) - 如何准备素材
- [Bug修复总结](BUGFIX_SUMMARY.md) - 最近修复内容

---

**准备好了吗？开始你的第一个AI视频吧！** 🎬

```bash
python main.py
```
