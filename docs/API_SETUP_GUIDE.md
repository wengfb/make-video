# 🔑 API密钥配置指南

本文档指导你免费获取Pexels和Unsplash API密钥,解锁300万+免费素材库。

---

## 📋 目录

1. [Pexels API配置](#pexels-api配置) ⭐ 推荐优先配置
2. [Unsplash API配置](#unsplash-api配置)
3. [配置验证](#配置验证)
4. [常见问题](#常见问题)

---

## 🎥 Pexels API配置

### 为什么需要Pexels?
- ✅ **300万+免费视频和图片**
- ✅ **完全免费,无需署名**
- ✅ **HD/4K高质量**
- ✅ **每小时200次请求**

### 申请步骤 (5分钟)

#### 1. 访问Pexels官网
打开浏览器访问: https://www.pexels.com/api/

#### 2. 注册账号
- 点击 "Get Started" 或 "Sign Up"
- 使用邮箱或Google账号注册
- 验证邮箱(检查收件箱)

#### 3. 创建应用
- 登录后,点击 "Create a New App" 或 "Your Apps"
- 填写信息:
  - **App Name**: `科普视频制作系统` (或任意名称)
  - **App Description**: `Educational video production system`
  - **Platform**: `Other` (其他)
  - **Usage**: `Non-commercial` (非商业) 或 `Commercial` (商业)

#### 4. 获取API密钥
- 提交后,立即显示 **API Key**
- 复制API密钥 (格式: `563492ad6f91700001000001abcdef123456789`)

#### 5. 配置到项目
打开 `config/settings.json`,找到 `pexels` 配置块:

```json
"pexels": {
  "api_key": "粘贴你的API密钥在这里",
  "description": "Pexels API密钥 - 免费申请: https://www.pexels.com/api/",
  "rate_limit_per_hour": 200,
  "auto_download": true,
  "preferred_video_quality": "hd",
  "preferred_photo_quality": "large2x"
}
```

**示例**:
```json
"pexels": {
  "api_key": "563492ad6f91700001000001abcdef123456789",
  ...
}
```

✅ **完成！现在可以访问300万+免费视频和图片！**

---

## 📸 Unsplash API配置

### 为什么需要Unsplash?
- ✅ **500万+高质量摄影作品**
- ✅ **摄影师级别质量**
- ✅ **CC0授权,商用无忧**
- ✅ **每小时50次请求**

### 申请步骤 (5分钟)

#### 1. 访问Unsplash开发者页面
打开: https://unsplash.com/developers

#### 2. 注册Unsplash账号
- 点击 "Register as a developer"
- 使用邮箱注册或社交账号登录
- 同意开发者条款

#### 3. 创建应用
- 点击 "Your Apps" → "New Application"
- 填写信息:
  - **Application Name**: `科普视频制作系统`
  - **Description**: `AI-powered educational video production`
  - **Platform**: `Other`
  - 勾选同意条款

#### 4. 获取Access Key
- 创建成功后,进入应用详情页
- 复制 **Access Key** (不是Secret Key)
- 格式: `abcdefg123456789_xxxxxxxxxxxxxxxxx`

#### 5. 配置到项目
打开 `config/settings.json`,找到 `unsplash` 配置块:

```json
"unsplash": {
  "access_key": "粘贴你的Access Key在这里",
  "description": "Unsplash Access Key - 免费注册: https://unsplash.com/developers",
  "rate_limit_per_hour": 50,
  "auto_download": true,
  "preferred_quality": "regular"
}
```

**示例**:
```json
"unsplash": {
  "access_key": "abcdefg123456789_xxxxxxxxxxxxxxxxx",
  ...
}
```

✅ **完成！现在可以访问500万+高质量图片！**

---

## ✅ 配置验证

### 测试Pexels API

在项目根目录运行:

```bash
# 测试搜索和下载视频
python scripts/2_material_manager/pexels_fetcher.py "space"

# 预期输出:
# 🔍 搜索Pexels视频: 'space'
# ✅ 找到 5 个视频
# ⬇️  下载视频: space_12345678.mp4 (HD)
# ✅ 下载完成: 15.2 MB
```

### 测试Unsplash API

```bash
# 测试搜索和下载图片
python scripts/2_material_manager/unsplash_fetcher.py "DNA" 3

# 预期输出:
# 🔍 搜索Unsplash图片: 'DNA'
# ✅ 找到 3 张图片
# ⬇️  下载图片: DNA_abc123.jpg
# ✅ 下载完成: 2048 KB
```

### 测试智能推荐器

```bash
# 进入Python交互式环境
python

# 运行测试
>>> from scripts.2_material_manager.recommender import MaterialRecommender
>>> from scripts.2_material_manager.manager import MaterialManager
>>>
>>> manager = MaterialManager()
>>> recommender = MaterialRecommender(manager)
>>>
>>> # 测试章节素材推荐
>>> section = {
...     'section_name': '宇宙的起源',
...     'narration': '宇宙大爆炸理论...',
...     'visual_notes': '展示宇宙星空'
... }
>>>
>>> results = recommender.recommend_for_script_section(section, limit=5)
>>> print(f"找到 {len(results)} 个素材")

# 预期输出:
# 🔍 分析素材需求...
#    章节: 宇宙的起源
#    📁 [1/4] 搜索本地素材库...
#        ✓ 找到 0 个本地素材
#        ⚠️  本地素材不足 (需要3个,仅0个)
#    🎥 [2/4] 从Pexels搜索视频: 'space universe'...
#        ✓ 从Pexels视频获取 3 个
# 找到 3 个素材
```

---

## 🚀 批量预缓存素材

配置好API后,建议立即预缓存常用素材:

```bash
# 预缓存所有100个科普关键词(每个3视频+2图片)
python scripts/utils/prefetch_materials.py

# 快速模式(每个关键词1视频+1图片)
python scripts/utils/prefetch_materials.py --quick

# 只预缓存天文类别
python scripts/utils/prefetch_materials.py --category astronomy

# 只预缓存前10个关键词
python scripts/utils/prefetch_materials.py --max 10
```

**预期结果**:
- 下载 **300+ HD视频**
- 下载 **200+ 高清图片**
- 总大小 **~5-10GB**
- 耗时 **20-30分钟**

---

## ❓ 常见问题

### Q1: API密钥配置后仍提示"未配置"?
**A**: 确保:
1. `settings.json` 中API密钥在引号内
2. 没有多余空格或换行
3. 保存文件后重启程序

### Q2: 提示"API请求限制"?
**A**:
- Pexels: 每小时200次,超出后等待1小时
- Unsplash: 每小时50次,超出后等待1小时
- 使用批量预缓存工具有自动延时,避免限流

### Q3: 下载失败或超时?
**A**:
- 检查网络连接
- 使用代理(如有防火墙)
- 部分视频文件较大,延长超时时间

### Q4: API密钥安全吗?
**A**:
- ✅ API密钥仅在你的本地电脑使用
- ✅ `settings.json` 在 `.gitignore` 中,不会上传Git
- ⚠️ 不要将密钥分享给他人或公开

### Q5: 可以商用下载的素材吗?
**A**:
- ✅ Pexels: 完全免费,商用无需署名
- ✅ Unsplash: CC0授权,商用无限制
- ⚠️ 请遵守各平台的用户协议

### Q6: API有费用吗?
**A**:
- ✅ **完全免费！**
- Pexels和Unsplash都提供永久免费的API
- 无需信用卡,无隐藏费用

---

## 📞 支持

如遇到问题:

1. **检查配置文件**: `config/settings.json`
2. **查看错误日志**: 程序运行输出
3. **访问官方文档**:
   - Pexels: https://www.pexels.com/api/documentation/
   - Unsplash: https://unsplash.com/documentation

---

## 🎉 配置完成后

恭喜！现在你可以:

✅ 自动获取 **300万+免费视频**
✅ 自动获取 **500万+高清图片**
✅ **零成本**制作高质量科普视频
✅ 告别素材荒,专注内容创作

立即运行批量预缓存工具,开始你的视频创作之旅！🚀

```bash
python scripts/utils/prefetch_materials.py --quick
```
