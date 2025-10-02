#!/usr/bin/env python3
"""
GLM真实API测试
验证配置的API密钥是否有效
"""

import sys
import os
import json

# 添加当前目录到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', '1_script_generator'))
from ai_client import AIClient


def test_real_glm_api():
    """测试真实的GLM API"""

    print("=" * 60)
    print("GLM API真实测试")
    print("=" * 60)

    # 加载配置
    try:
        with open('config/settings.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        ai_config = config.get('ai', {})

        print(f"\n📋 当前配置:")
        print(f"   Provider: {ai_config.get('provider')}")
        print(f"   Model: {ai_config.get('model')}")
        print(f"   Base URL: {ai_config.get('base_url')}")
        print(f"   API Key: {ai_config.get('api_key')[:20]}...")

        # 初始化客户端
        print(f"\n🔧 初始化AIClient...")
        client = AIClient(ai_config)
        print(f"✅ 客户端初始化成功")

        # 测试简单调用
        print(f"\n🚀 测试API调用（生成简短文本）...")
        print(f"   提示词: '你好，请用一句话介绍你自己'")

        response = client.generate(
            prompt="你好，请用一句话介绍你自己",
            system_prompt="你是一个友好的AI助手"
        )

        print(f"\n✅ API调用成功！")
        print(f"📝 GLM响应:")
        print(f"   {response}")

        print("\n" + "=" * 60)
        print("🎉 恭喜！GLM配置成功，可以正常使用了！")
        print("=" * 60)

        print(f"\n💡 下一步操作:")
        print(f"   1. 运行主程序: python3 main.py")
        print(f"   2. 选择菜单1: 生成主题")
        print(f"   3. 或选择菜单7: 生成脚本")
        print(f"   4. 开始创作你的科普视频！")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print(f"\n🔍 故障排查:")
        print(f"   1. 检查API密钥是否正确")
        print(f"   2. 确认网络连接正常")
        print(f"   3. 访问 https://open.bigmodel.cn/ 确认账户状态")
        print(f"   4. 检查账户是否有可用额度")
        return False


if __name__ == '__main__':
    test_real_glm_api()
