#!/usr/bin/env python3
"""
CogView图片生成测试
"""

import sys
import os
import json

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', '2_material_manager'))
from ai_generator import AIImageGenerator


def test_cogview():
    """测试CogView图片生成"""

    print("=" * 60)
    print("CogView图片生成测试")
    print("=" * 60)

    # 加载配置
    with open('config/settings.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    image_config = config.get('ai_image', {})

    print(f"\n📋 图片生成配置:")
    print(f"   Provider: {image_config.get('provider')}")
    print(f"   Model: {image_config.get('model')}")
    print(f"   Base URL: {image_config.get('base_url')}")
    print(f"   API Key: {image_config.get('api_key', '')[:20]}...")

    try:
        # 初始化生成器
        print(f"\n🔧 初始化AIImageGenerator...")
        generator = AIImageGenerator()
        print(f"✅ 生成器初始化成功")

        # 测试生成图片
        print(f"\n🎨 测试图片生成...")
        print(f"   提示词: '一只可爱的熊猫在吃竹子，卡通风格'")

        results = generator.generate_image(
            prompt="一只可爱的熊猫在吃竹子，卡通风格",
            size="1024x1024"
        )

        print(f"\n✅ 图片生成成功！")
        print(f"📝 生成结果:")
        for i, result in enumerate(results, 1):
            if 'url' in result:
                print(f"   图片{i} URL: {result['url'][:60]}...")
            elif 'b64_json' in result:
                print(f"   图片{i}: Base64编码 (长度: {len(result['b64_json'])})")

        # 测试保存图片
        if results:
            print(f"\n💾 测试保存图片...")
            output_dir = "materials/images"
            filepath = generator.save_generated_image(
                results[0],
                output_dir,
                "test_cogview_panda.png"
            )
            print(f"✅ 图片已保存到: {filepath}")

        print("\n" + "=" * 60)
        print("🎉 CogView配置成功！")
        print("=" * 60)

        print(f"\n💡 下一步:")
        print(f"   1. 运行主程序: python3 main.py")
        print(f"   2. 选择菜单10: 素材管理")
        print(f"   3. 选择AI生成图片功能")
        print(f"   4. 使用CogView生成科普视频配图")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print(f"\n🔍 故障排查:")
        print(f"   1. 检查config/settings.json中ai_image配置")
        print(f"   2. 确认provider设置为'cogview'")
        print(f"   3. 确认API密钥正确")
        print(f"   4. 检查账户额度是否充足")


if __name__ == '__main__':
    test_cogview()
