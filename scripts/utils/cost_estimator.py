#!/usr/bin/env python3
"""
API成本估算和控制工具
帮助用户了解和控制API使用成本
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


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

    @staticmethod
    def track_cost(operation: str, cost: float, details: Dict[str, Any] = None):
        """
        记录实际API使用成本

        Args:
            operation: 操作类型 (topic, script, image, tts, etc.)
            cost: 实际成本
            details: 详细信息
        """
        costs_file = Path("data/costs.json")

        # 加载现有数据
        if costs_file.exists():
            with open(costs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                "total_cost": 0.0,
                "sessions": [],
                "last_updated": None
            }

        # 添加新记录
        session = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "cost": cost,
            "details": details or {}
        }

        data["sessions"].append(session)
        data["total_cost"] = round(data["total_cost"] + cost, 4)
        data["last_updated"] = datetime.now().isoformat()

        # 保存
        costs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(costs_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_total_cost() -> float:
        """
        获取累计成本

        Returns:
            总成本（美元）
        """
        costs_file = Path("data/costs.json")

        if costs_file.exists():
            with open(costs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("total_cost", 0.0)

        return 0.0

    @staticmethod
    def print_cost_summary():
        """打印成本汇总"""
        costs_file = Path("data/costs.json")

        if not costs_file.exists():
            print("\n💰 成本统计: 暂无数据")
            return

        with open(costs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("\n" + "=" * 60)
        print("💰 API成本统计")
        print("=" * 60)
        print(f"\n累计总成本: ${data['total_cost']:.4f} USD")
        print(f"记录数: {len(data['sessions'])}")

        if data['last_updated']:
            print(f"最后更新: {data['last_updated']}")

        # 按操作类型分组
        by_operation = {}
        for session in data['sessions']:
            op = session['operation']
            cost = session['cost']
            if op not in by_operation:
                by_operation[op] = {'count': 0, 'cost': 0.0}
            by_operation[op]['count'] += 1
            by_operation[op]['cost'] += cost

        if by_operation:
            print(f"\n按操作类型分类:")
            for op, stats in sorted(by_operation.items(), key=lambda x: x[1]['cost'], reverse=True):
                print(f"  {op}: {stats['count']}次, ${stats['cost']:.4f}")

        print("=" * 60)


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
