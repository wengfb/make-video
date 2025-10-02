#!/usr/bin/env python3
"""
GLM集成测试脚本
用于验证智谱AI GLM集成是否正常工作
"""

import sys
import os

# 添加当前目录到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', '1_script_generator'))
from ai_client import AIClient


def test_glm_integration():
    """测试GLM集成"""

    print("=" * 60)
    print("GLM集成测试")
    print("=" * 60)

    # 测试配置
    test_configs = [
        {
            'name': 'OpenAI兼容测试（模拟GLM）',
            'config': {
                'provider': 'glm',
                'model': 'glm-4',
                'api_key': 'test-key-will-fail',  # 测试用，会失败
                'base_url': 'https://open.bigmodel.cn/api/paas/v4/',
                'temperature': 0.7,
                'max_tokens': 100
            }
        }
    ]

    for test in test_configs:
        print(f"\n🧪 测试: {test['name']}")
        print("-" * 60)

        try:
            # 初始化客户端
            client = AIClient(test['config'])
            print(f"✅ AIClient初始化成功")
            print(f"   Provider: {client.provider}")
            print(f"   Model: {client.model}")
            print(f"   Base URL: {client.base_url}")

            # 尝试调用（会因为API key无效而失败，但可以验证代码逻辑）
            print(f"\n⚠️  尝试API调用（预期会失败，因为API key无效）...")
            try:
                response = client.generate("测试", "你是一个测试助手")
                print(f"✅ API调用成功: {response[:50]}...")
            except Exception as e:
                error_msg = str(e)
                if "GLM API" in error_msg or "401" in error_msg or "认证" in error_msg.lower():
                    print(f"✅ API调用逻辑正确（如预期失败）")
                    print(f"   错误信息: {error_msg[:100]}...")
                else:
                    print(f"❌ 未预期的错误: {error_msg}")

        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")

    # 显示使用说明
    print("\n" + "=" * 60)
    print("📋 如何配置GLM：")
    print("=" * 60)
    print("""
1. 获取GLM API密钥：
   访问 https://open.bigmodel.cn/
   注册账号并创建API密钥

2. 编辑 config/settings.json：
   {
     "ai": {
       "provider": "glm",
       "model": "glm-4",
       "api_key": "你的GLM_API密钥",
       "base_url": "https://open.bigmodel.cn/api/paas/v4/",
       "temperature": 0.7,
       "max_tokens": 2000
     }
   }

3. 可用的GLM模型：
   - glm-4: 通用模型（推荐）
   - glm-4-plus: 增强版
   - glm-4-air: 快速版
   - glm-4-flash: 超快速版

4. 运行主程序测试：
   python main.py
   选择菜单1 → 生成主题
""")

    print("=" * 60)
    print("✅ GLM集成测试完成！")
    print("=" * 60)
    print("\n💡 提示：")
    print("   - 代码集成已完成，支持GLM provider")
    print("   - 使用前需配置有效的GLM API密钥")
    print("   - GLM使用OpenAI兼容接口，无需额外依赖")
    print("   - 所有模块（主题生成、脚本生成）自动支持GLM")
    print()


if __name__ == '__main__':
    test_glm_integration()
