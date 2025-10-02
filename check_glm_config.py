#!/usr/bin/env python3
"""
GLM配置检查工具
"""

import json
import requests

def check_glm_config():
    """检查GLM配置和连接"""

    print("=" * 60)
    print("GLM配置检查")
    print("=" * 60)

    # 读取配置
    with open('config/settings.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    ai_config = config.get('ai', {})

    print(f"\n✅ 配置文件读取成功")
    print(f"\n📋 当前AI配置:")
    print(f"   Provider: {ai_config.get('provider')}")
    print(f"   Model: {ai_config.get('model')}")
    print(f"   Base URL: {ai_config.get('base_url')}")
    print(f"   API Key: {ai_config.get('api_key')[:20]}... (长度: {len(ai_config.get('api_key', ''))})")
    print(f"   Temperature: {ai_config.get('temperature')}")
    print(f"   Max Tokens: {ai_config.get('max_tokens')}")

    # 检查配置完整性
    print(f"\n🔍 配置检查:")
    checks = {
        'Provider设置为glm': ai_config.get('provider') == 'glm',
        'API Key不为空': bool(ai_config.get('api_key')),
        'API Key格式正确': '.' in ai_config.get('api_key', ''),
        'Base URL正确': 'bigmodel.cn' in ai_config.get('base_url', ''),
        'Model已设置': bool(ai_config.get('model'))
    }

    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")

    if not all(checks.values()):
        print(f"\n⚠️  配置存在问题，请检查上述失败项")
        return

    print(f"\n✅ 所有配置检查通过！")

    # 429错误说明
    print(f"\n" + "=" * 60)
    print(f"关于429错误 (Too Many Requests)")
    print("=" * 60)
    print(f"""
出现429错误的可能原因：

1. 🔴 账户额度不足
   - 登录 https://open.bigmodel.cn/usercenter/apikeys
   - 检查账户余额
   - 如需充值，访问 https://open.bigmodel.cn/pricing

2. 🟡 API调用频率限制
   - GLM有调用频率限制（例如：每分钟N次）
   - 稍等1-2分钟后重试
   - 生产环境建议升级到更高等级的服务

3. 🟡 API密钥未激活
   - 访问 https://open.bigmodel.cn/usercenter/apikeys
   - 确认API密钥状态为"启用"
   - 如果刚创建，等待几分钟激活

4. 🔵 临时服务限制
   - 智谱AI可能在维护或限流
   - 稍后重试

建议操作：
1. 访问智谱AI控制台检查账户状态
2. 等待1-2分钟后重新测试
3. 如果问题持续，尝试切换到 glm-4-flash (成本更低)
""")

    print("=" * 60)
    print("配置检查完成")
    print("=" * 60)

if __name__ == '__main__':
    check_glm_config()
