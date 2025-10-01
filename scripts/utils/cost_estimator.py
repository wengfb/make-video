#!/usr/bin/env python3
"""
API成本估算和控制工具
帮助用户了解和控制API使用成本
"""


class CostEstimator:
    """API成本估算器"""

    # OpenAI API 价格 (2025年1月)
    PRICES = {
        'gpt-4': {
            'input': 0.03 / 1000,   # $0.03 per 1K tokens
            'output': 0.06 / 1000,  # $0.06 per 1K tokens
        },
        'gpt-3.5-turbo': {
            'input': 0.0005 / 1000,
            'output': 0.0015 / 1000,
        },
        'dall-e-3': {
            'standard-1024': 0.040,  # $0.040 per image
            'standard-1792': 0.080,  # $0.080 per image
            'hd-1024': 0.080,
            'hd-1792': 0.120,
        },
        'tts-1': {
            'per_char': 0.000015,  # $0.015 per 1M characters
        },
        'tts-1-hd': {
            'per_char': 0.000030,
        }
    }

    @classmethod
    def estimate_topic_generation(cls, count: int = 10, model: str = 'gpt-4') -> float:
        """
        估算主题生成成本

        Args:
            count: 生成数量
            model: 使用的模型

        Returns:
            预估成本（美元）
        """
        # 粗略估算: 每个主题约500 tokens输入 + 300 tokens输出
        input_tokens = count * 500
        output_tokens = count * 300

        prices = cls.PRICES.get(model, cls.PRICES['gpt-4'])
        cost = input_tokens * prices['input'] + output_tokens * prices['output']

        return round(cost, 4)

    @classmethod
    def estimate_script_generation(cls, sections: int = 5, model: str = 'gpt-4') -> float:
        """
        估算脚本生成成本

        Args:
            sections: 脚本章节数
            model: 使用的模型

        Returns:
            预估成本（美元）
        """
        # 粗略估算: 约1000 tokens输入 + sections*200 tokens输出
        input_tokens = 1000
        output_tokens = sections * 200

        prices = cls.PRICES.get(model, cls.PRICES['gpt-4'])
        cost = input_tokens * prices['input'] + output_tokens * prices['output']

        return round(cost, 4)

    @classmethod
    def estimate_image_generation(cls, count: int = 1, quality: str = 'standard',
                                  size: str = '1024x1024') -> float:
        """
        估算图片生成成本

        Args:
            count: 图片数量
            quality: 质量 (standard/hd)
            size: 尺寸 (1024x1024/1792x1024)

        Returns:
            预估成本（美元）
        """
        size_key = size.replace('x', '-')
        price_key = f"{quality}-{size_key}" if quality == 'hd' else f"standard-1024"

        if '1792' in size:
            price_key = f"{quality}-1792"

        price = cls.PRICES['dall-e-3'].get(price_key, 0.040)
        cost = count * price

        return round(cost, 4)

    @classmethod
    def estimate_tts_generation(cls, text_length: int, model: str = 'tts-1') -> float:
        """
        估算TTS语音生成成本

        Args:
            text_length: 文本字符数
            model: TTS模型 (tts-1/tts-1-hd)

        Returns:
            预估成本（美元）
        """
        price = cls.PRICES[model]['per_char']
        cost = text_length * price

        return round(cost, 4)

    @classmethod
    def estimate_full_workflow(cls, image_count: int = 5, use_openai_tts: bool = False,
                               script_length: int = 1000) -> dict:
        """
        估算完整工作流成本

        Args:
            image_count: AI生成图片数量
            use_openai_tts: 是否使用OpenAI TTS（False则免费Edge TTS）
            script_length: 脚本字符数

        Returns:
            成本详情字典
        """
        costs = {
            'topic_generation': cls.estimate_topic_generation(count=5),
            'script_generation': cls.estimate_script_generation(sections=5),
            'image_generation': cls.estimate_image_generation(count=image_count) if image_count > 0 else 0,
            'tts_generation': cls.estimate_tts_generation(script_length) if use_openai_tts else 0,
        }

        costs['total'] = sum(costs.values())

        return costs

    @classmethod
    def print_cost_estimate(cls, operation: str, **kwargs) -> float:
        """
        打印成本估算

        Args:
            operation: 操作类型
            **kwargs: 操作参数

        Returns:
            预估成本
        """
        if operation == 'topic':
            cost = cls.estimate_topic_generation(**kwargs)
            print(f"\n💰 成本估算: 主题生成")
            print(f"   预估成本: ${cost:.4f} USD")

        elif operation == 'script':
            cost = cls.estimate_script_generation(**kwargs)
            print(f"\n💰 成本估算: 脚本生成")
            print(f"   预估成本: ${cost:.4f} USD")

        elif operation == 'image':
            cost = cls.estimate_image_generation(**kwargs)
            count = kwargs.get('count', 1)
            print(f"\n💰 成本估算: AI图片生成")
            print(f"   图片数量: {count}")
            print(f"   单价: ${cost/count:.4f}")
            print(f"   总成本: ${cost:.4f} USD")

        elif operation == 'workflow':
            costs = cls.estimate_full_workflow(**kwargs)
            print(f"\n💰 成本估算: 完整工作流")
            print(f"   主题生成: ${costs['topic_generation']:.4f}")
            print(f"   脚本生成: ${costs['script_generation']:.4f}")
            if costs['image_generation'] > 0:
                print(f"   图片生成: ${costs['image_generation']:.4f}")
            if costs['tts_generation'] > 0:
                print(f"   语音合成: ${costs['tts_generation']:.4f}")
            print(f"   ---")
            print(f"   总计: ${costs['total']:.4f} USD")
            cost = costs['total']

        else:
            cost = 0.0

        return cost

    @classmethod
    def confirm_cost(cls, cost: float, operation: str = "此操作") -> bool:
        """
        显示成本并请求用户确认

        Args:
            cost: 预估成本
            operation: 操作描述

        Returns:
            用户是否确认
        """
        if cost == 0:
            return True

        print(f"\n⚠️  {operation} 预估成本: ${cost:.4f} USD")
        print(f"   (实际费用可能略有不同)")

        choice = input(f"\n是否继续? (Y/n): ").strip().lower()

        return choice != 'n'


# 命令行测试
if __name__ == '__main__':
    estimator = CostEstimator()

    print("=" * 60)
    print("📊 API成本估算工具")
    print("=" * 60)

    # 测试各种操作的成本
    estimator.print_cost_estimate('topic', count=10)
    estimator.print_cost_estimate('script', sections=5)
    estimator.print_cost_estimate('image', count=5, quality='standard')
    estimator.print_cost_estimate('workflow', image_count=5, use_openai_tts=False)

    print("\n" + "=" * 60)
