# 快速上手指南

## 5分钟快速开始

### 步骤1: 安装依赖

```bash
pip install requests
```

### 步骤2: 配置API密钥

**方法A: 修改配置文件**

编辑 `config/settings.json`：

```json
{
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "sk-xxxxxxxxxxxxxxxx",  // 在这里填入你的API密钥
    ...
  }
}
```

**方法B: 使用环境变量**（推荐）

```bash
# Linux/Mac
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"

# Windows PowerShell
$env:OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### 步骤3: 运行程序

```bash
python main.py
```

### 步骤4: 生成你的第一个脚本

在交互界面中：

1. 选择 `1` (生成视频脚本)
2. 输入主题，例如: `为什么天空是蓝色的`
3. 选择模板 `1` (科普视频模板)
4. 其他选项可以直接回车使用默认值
5. 等待AI生成
6. 输入 `Y` 保存脚本

完成！你的第一个脚本已生成在 `output/scripts/` 目录中。

## 常见问题

### Q: API调用失败怎么办？

A: 检查以下几点：
1. API密钥是否正确
2. 账户是否有余额
3. 网络是否能访问API服务器
4. 如果使用国内网络，可能需要配置代理

### Q: 如何使用不同的AI服务？

A: 修改 `config/settings.json` 中的 `provider` 和相关配置：

**使用Anthropic Claude**:
```json
{
  "ai": {
    "provider": "anthropic",
    "model": "claude-3-opus-20240229",
    "api_key": "sk-ant-xxxxx",
    "base_url": "https://api.anthropic.com/v1"
  }
}
```

### Q: 生成的脚本质量不满意？

A: 尝试以下方法：
1. 提供更详细的主题描述
2. 在"额外要求"中说明具体需求
3. 多生成几个版本，选择最好的
4. 调整 `temperature` 参数（0.3-1.0）
5. 人工编辑优化生成的脚本

### Q: 如何自定义模板？

A: 编辑 `config/templates.json`，参考现有模板添加新的模板定义。

## 下一步

- 阅读 [README.md](README.md) 了解完整功能
- 查看生成的脚本示例
- 尝试不同的模板和主题
- 等待后续模块开发（素材管理、视频剪辑等）

## 示例命令

```bash
# 命令行模式生成脚本
python main.py generate "光合作用的原理" -t popular_science

# 生成实验演示脚本
python main.py generate "水的三态变化实验" -t experiment_demo

# 指定时长和输出文件
python main.py generate "DNA双螺旋结构" -d "5min" -o dna_script.json

# 查看所有模板
python main.py templates
```

## 获取帮助

```bash
python main.py --help
python main.py generate --help
```
