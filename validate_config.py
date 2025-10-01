#!/usr/bin/env python3
"""
配置验证脚本
检查配置文件的完整性和正确性
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class ConfigValidator:
    """配置验证器"""

    def __init__(self, config_path: str = 'config/settings.json'):
        self.config_path = config_path
        self.config = {}
        self.errors = []
        self.warnings = []

    def validate(self) -> bool:
        """执行验证，返回是否通过"""
        print("=" * 60)
        print("🔍 配置文件验证")
        print("=" * 60)

        # 1. 检查文件存在
        if not self._check_file_exists():
            return False

        # 2. 检查JSON格式
        if not self._check_json_format():
            return False

        # 3. 检查必需字段
        self._check_required_fields()

        # 4. 检查API配置
        self._check_api_config()

        # 5. 检查路径配置
        self._check_paths_config()

        # 6. 检查视频配置
        self._check_video_config()

        # 7. 检查TTS配置
        self._check_tts_config()

        # 8. 检查字幕配置
        self._check_subtitle_config()

        # 9. 显示结果
        self._display_results()

        return len(self.errors) == 0

    def _check_file_exists(self) -> bool:
        """检查配置文件是否存在"""
        if not os.path.exists(self.config_path):
            print(f"\n❌ 配置文件不存在: {self.config_path}")
            print(f"\n💡 请复制示例配置文件:")
            print(f"   cp config/settings.example.json config/settings.json")
            return False

        print(f"\n✓ 配置文件存在: {self.config_path}")
        return True

    def _check_json_format(self) -> bool:
        """检查JSON格式"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print("✓ JSON格式正确")
            return True
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON格式错误: {e}")
            self.errors.append(f"JSON格式错误: {e}")
            return False
        except Exception as e:
            print(f"\n❌ 读取配置文件失败: {e}")
            self.errors.append(f"读取失败: {e}")
            return False

    def _check_required_fields(self):
        """检查必需字段"""
        print("\n📋 检查必需字段...")

        required_sections = ['project', 'ai', 'video', 'paths']

        for section in required_sections:
            if section not in self.config:
                self.errors.append(f"缺少必需配置节: {section}")
                print(f"  ❌ 缺少: {section}")
            else:
                print(f"  ✓ {section}")

    def _check_api_config(self):
        """检查API配置"""
        print("\n🤖 检查AI配置...")

        ai_config = self.config.get('ai', {})

        # 检查API密钥
        api_key = ai_config.get('api_key', '')
        if not api_key:
            self.warnings.append("AI API密钥未设置")
            print("  ⚠️  API密钥未设置（可使用环境变量OPENAI_API_KEY）")
        elif api_key == 'YOUR_API_KEY_HERE':
            self.errors.append("API密钥未替换示例值")
            print("  ❌ API密钥仍是示例值，请替换为实际密钥")
        else:
            print(f"  ✓ API密钥已设置 ({api_key[:10]}...)")

        # 检查模型
        model = ai_config.get('model', '')
        if not model:
            self.warnings.append("AI模型未设置")
            print("  ⚠️  模型未设置")
        else:
            print(f"  ✓ 模型: {model}")

        # 检查图片生成配置
        ai_image = self.config.get('ai_image', {})
        image_api_key = ai_image.get('api_key', '')
        if not image_api_key or image_api_key == 'YOUR_DALLE_API_KEY_HERE':
            self.warnings.append("DALL-E API密钥未设置")
            print("  ⚠️  DALL-E API密钥未设置（图片生成功能不可用）")

    def _check_paths_config(self):
        """检查路径配置"""
        print("\n📁 检查路径配置...")

        paths = self.config.get('paths', {})

        required_paths = [
            'materials',
            'output',
            'scripts',
            'videos',
            'subtitles',
            'audio'
        ]

        for path_key in required_paths:
            if path_key not in paths:
                self.warnings.append(f"路径配置缺少: {path_key}")
                print(f"  ⚠️  缺少路径配置: {path_key}")
            else:
                path_value = paths[path_key]
                # 创建目录（如果不存在）
                try:
                    Path(path_value).mkdir(parents=True, exist_ok=True)
                    print(f"  ✓ {path_key}: {path_value}")
                except Exception as e:
                    self.errors.append(f"无法创建目录 {path_value}: {e}")
                    print(f"  ❌ 无法创建目录 {path_value}: {e}")

    def _check_video_config(self):
        """检查视频配置"""
        print("\n🎬 检查视频配置...")

        video = self.config.get('video', {})

        # 检查分辨率
        resolution = video.get('resolution', {})
        if isinstance(resolution, dict):
            width = resolution.get('width', 0)
            height = resolution.get('height', 0)
            if width > 0 and height > 0:
                print(f"  ✓ 分辨率: {width}x{height}")
            else:
                self.errors.append("视频分辨率配置无效")
                print(f"  ❌ 分辨率配置无效")
        else:
            self.warnings.append("视频分辨率格式不正确")
            print("  ⚠️  分辨率配置格式不正确")

        # 检查帧率
        fps = video.get('fps', 0)
        if fps > 0 and fps <= 120:
            print(f"  ✓ 帧率: {fps} fps")
        else:
            self.warnings.append(f"帧率配置异常: {fps}")
            print(f"  ⚠️  帧率配置异常: {fps}")

        # 检查编码器
        codec = video.get('codec', '')
        if codec:
            print(f"  ✓ 编码器: {codec}")
        else:
            self.warnings.append("视频编码器未设置")
            print("  ⚠️  编码器未设置")

    def _check_tts_config(self):
        """检查TTS配置"""
        print("\n🎙️  检查TTS配置...")

        tts = self.config.get('tts', {})

        if not tts:
            self.warnings.append("TTS配置缺失（V5.0功能不可用）")
            print("  ⚠️  TTS配置缺失")
            return

        # 检查提供商
        provider = tts.get('provider', '')
        if provider in ['edge', 'openai']:
            print(f"  ✓ TTS提供商: {provider}")
        else:
            self.errors.append(f"TTS提供商配置无效: {provider}")
            print(f"  ❌ TTS提供商无效: {provider}")

        # 检查声音
        voice = tts.get('voice', '')
        if voice:
            print(f"  ✓ 声音: {voice}")
        else:
            self.warnings.append("TTS声音未设置")
            print("  ⚠️  声音未设置")

        # 检查语速
        speed = tts.get('speed', 1.0)
        if 0.25 <= speed <= 4.0:
            print(f"  ✓ 语速: {speed}x")
        else:
            self.warnings.append(f"语速配置超出范围: {speed}")
            print(f"  ⚠️  语速超出范围(0.25-4.0): {speed}")

        # 如果使用OpenAI，检查API密钥
        if provider == 'openai':
            api_key = tts.get('api_key', '')
            if not api_key:
                self.warnings.append("OpenAI TTS API密钥未设置")
                print("  ⚠️  OpenAI TTS需要API密钥")

    def _check_subtitle_config(self):
        """检查字幕配置"""
        print("\n📝 检查字幕配置...")

        subtitle = self.config.get('subtitle', {})

        if not subtitle:
            self.warnings.append("字幕配置缺失（V5.0功能不可用）")
            print("  ⚠️  字幕配置缺失")
            return

        # 检查字体
        font = subtitle.get('font', '')
        if font:
            print(f"  ✓ 字体: {font}")
        else:
            self.warnings.append("字幕字体未设置")
            print("  ⚠️  字体未设置")

        # 检查字号
        font_size = subtitle.get('font_size', 0)
        if 10 <= font_size <= 200:
            print(f"  ✓ 字号: {font_size}")
        else:
            self.warnings.append(f"字号配置异常: {font_size}")
            print(f"  ⚠️  字号异常: {font_size}")

        # 检查位置
        position = subtitle.get('position', '')
        if position in ['top', 'middle', 'bottom']:
            print(f"  ✓ 位置: {position}")
        else:
            self.warnings.append(f"字幕位置配置无效: {position}")
            print(f"  ⚠️  位置无效: {position}")

    def _display_results(self):
        """显示验证结果"""
        print("\n" + "=" * 60)
        print("📊 验证结果")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ 配置文件完全正确！")
        elif not self.errors:
            print("\n✅ 配置文件基本正确，但有一些警告")
        else:
            print("\n❌ 配置文件有错误，需要修复")

        print("=" * 60)


def main():
    """主函数"""
    validator = ConfigValidator()
    success = validator.validate()

    if success:
        print("\n✅ 验证通过！可以运行程序了")
        print("   运行: python main.py")
        sys.exit(0)
    else:
        print("\n❌ 验证失败！请修复配置文件后重试")
        print("   编辑: config/settings.json")
        sys.exit(1)


if __name__ == '__main__':
    main()
