#!/usr/bin/env python3
"""
TTS语音生成器
支持多种TTS服务: OpenAI TTS, Edge TTS等
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio


class TTSGenerator:
    """TTS语音生成器类"""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        初始化TTS生成器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.tts_config = self.config.get("tts", {})
        self.output_dir = Path(self.config["paths"]["audio"]) / "tts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # TTS提供商
        self.provider = self.tts_config.get("provider", "openai")

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {str(e)}")
            return {}

    def generate_speech_from_script(self, script_path: str, output_name: Optional[str] = None) -> Dict:
        """
        根据脚本文件生成语音

        Args:
            script_path: 脚本JSON文件路径
            output_name: 输出文件名(不含扩展名),默认使用脚本标题

        Returns:
            包含生成结果的字典
        """
        print(f"\n🎙️  开始从脚本生成语音...")
        print(f"📄 脚本文件: {script_path}")

        try:
            # 读取脚本
            with open(script_path, 'r', encoding='utf-8') as f:
                script = json.load(f)

            # 提取所有章节的旁白
            sections = script.get("sections", [])
            if not sections:
                print("❌ 脚本中没有找到章节")
                return {"success": False, "error": "no_sections"}

            # 确定输出文件名
            if output_name is None:
                output_name = script.get("title", "untitled").replace(" ", "_")

            # 为每个章节生成语音
            audio_files = []
            total_duration = 0.0

            for i, section in enumerate(sections, 1):
                section_name = section.get("section_name", f"Section_{i}")
                narration = section.get("narration", "")

                if not narration or narration.strip() == "":
                    print(f"⚠️  章节 {i} ({section_name}) 没有旁白文字,跳过")
                    continue

                print(f"\n🔊 生成章节 {i}/{len(sections)}: {section_name}")
                print(f"📝 文字: {narration[:50]}..." if len(narration) > 50 else f"📝 文字: {narration}")

                # 生成单个章节的语音
                result = self.generate_speech(
                    text=narration,
                    output_filename=f"{output_name}_section_{i:02d}.mp3"
                )

                if result["success"]:
                    audio_files.append({
                        "section_index": i,
                        "section_name": section_name,
                        "file_path": result["file_path"],
                        "duration": result.get("duration", 0.0),
                        "text": narration
                    })
                    total_duration += result.get("duration", 0.0)
                else:
                    print(f"❌ 章节 {i} 生成失败: {result.get('error', 'unknown')}")

            if not audio_files:
                print("\n❌ 没有生成任何语音文件")
                return {"success": False, "error": "no_audio_generated"}

            # 保存音频元数据
            metadata = {
                "script_path": script_path,
                "script_title": script.get("title", ""),
                "total_sections": len(sections),
                "generated_sections": len(audio_files),
                "total_duration": total_duration,
                "audio_files": audio_files,
                "provider": self.provider,
                "voice": self.tts_config.get("voice", "default")
            }

            metadata_path = self.output_dir / f"{output_name}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            print(f"\n✅ 语音生成完成!")
            print(f"📊 总计: {len(audio_files)}/{len(sections)} 个章节")
            print(f"⏱️  总时长: {total_duration:.1f}秒")
            print(f"💾 元数据: {metadata_path}")

            return {
                "success": True,
                "metadata": metadata,
                "metadata_path": str(metadata_path),
                "audio_files": audio_files,
                "total_duration": total_duration
            }

        except Exception as e:
            print(f"\n❌ 生成语音时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def generate_speech(self, text: str, output_filename: str,
                       voice: Optional[str] = None,
                       speed: float = 1.0) -> Dict:
        """
        生成单段语音

        Args:
            text: 要转换的文字
            output_filename: 输出文件名
            voice: 声音类型(可选)
            speed: 语速(0.5-2.0)

        Returns:
            包含生成结果的字典
        """
        if self.provider == "openai":
            return self._generate_openai_tts(text, output_filename, voice, speed)
        elif self.provider == "edge":
            return self._generate_edge_tts(text, output_filename, voice, speed)
        else:
            return {"success": False, "error": f"不支持的TTS提供商: {self.provider}"}

    def _generate_openai_tts(self, text: str, output_filename: str,
                            voice: Optional[str] = None, speed: float = 1.0) -> Dict:
        """
        使用OpenAI TTS生成语音

        Args:
            text: 文字内容
            output_filename: 输出文件名
            voice: 声音(alloy, echo, fable, onyx, nova, shimmer)
            speed: 语速(0.25-4.0)
        """
        try:
            from openai import OpenAI

            # 初始化OpenAI客户端
            api_key = self.tts_config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {"success": False, "error": "未配置OpenAI API密钥"}

            client = OpenAI(api_key=api_key)

            # 设置参数
            model = self.tts_config.get("model", "tts-1")
            voice = voice or self.tts_config.get("voice", "alloy")

            # 限制语速范围
            speed = max(0.25, min(4.0, speed))

            print(f"🔊 使用OpenAI TTS (模型: {model}, 声音: {voice}, 语速: {speed}x)")

            # 调用API
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed
            )

            # 保存音频文件
            output_path = self.output_dir / output_filename
            response.stream_to_file(output_path)

            # 获取音频时长
            duration = self._get_audio_duration(str(output_path))

            print(f"✅ 生成成功: {output_path} ({duration:.1f}秒)")

            return {
                "success": True,
                "file_path": str(output_path),
                "duration": duration,
                "provider": "openai",
                "voice": voice,
                "speed": speed
            }

        except Exception as e:
            print(f"❌ OpenAI TTS生成失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _generate_edge_tts(self, text: str, output_filename: str,
                          voice: Optional[str] = None, speed: float = 1.0) -> Dict:
        """
        使用Edge TTS生成语音(免费)

        Args:
            text: 文字内容
            output_filename: 输出文件名
            voice: 声音(中文: zh-CN-XiaoxiaoNeural, zh-CN-YunxiNeural等)
            speed: 语速调整百分比
        """
        try:
            import edge_tts

            # 设置声音
            voice = voice or self.tts_config.get("voice", "zh-CN-XiaoxiaoNeural")

            # 计算语速参数 (speed: 1.0 = +0%, 1.5 = +50%, 0.5 = -50%)
            rate_percent = int((speed - 1.0) * 100)
            rate = f"{rate_percent:+d}%"

            print(f"🔊 使用Edge TTS (声音: {voice}, 语速: {rate})")

            # 输出路径
            output_path = self.output_dir / output_filename

            # 异步生成语音
            async def _generate():
                communicate = edge_tts.Communicate(text, voice, rate=rate)
                await communicate.save(str(output_path))

            # 运行异步任务
            asyncio.run(_generate())

            # 获取音频时长
            duration = self._get_audio_duration(str(output_path))

            print(f"✅ 生成成功: {output_path} ({duration:.1f}秒)")

            return {
                "success": True,
                "file_path": str(output_path),
                "duration": duration,
                "provider": "edge",
                "voice": voice,
                "speed": speed
            }

        except ImportError:
            print("❌ 未安装edge-tts库,请运行: pip install edge-tts")
            return {"success": False, "error": "edge-tts not installed"}
        except Exception as e:
            print(f"❌ Edge TTS生成失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_audio_duration(self, audio_path: str) -> float:
        """
        获取音频文件时长

        Args:
            audio_path: 音频文件路径

        Returns:
            时长(秒)
        """
        try:
            from moviepy.editor import AudioFileClip

            audio = AudioFileClip(audio_path)
            duration = audio.duration
            audio.close()

            return duration
        except Exception as e:
            print(f"⚠️  获取音频时长失败: {str(e)}")
            # 粗略估算: 中文约150字/分钟
            return 0.0

    def list_available_voices(self) -> List[str]:
        """
        列出可用的声音选项

        Returns:
            声音列表
        """
        if self.provider == "openai":
            return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        elif self.provider == "edge":
            # Edge TTS常用中文声音
            return [
                "zh-CN-XiaoxiaoNeural",  # 女声-晓晓
                "zh-CN-YunxiNeural",      # 男声-云希
                "zh-CN-YunyangNeural",    # 男声-云扬
                "zh-CN-XiaoyiNeural",     # 女声-晓伊
                "zh-CN-YunjianNeural",    # 男声-云健
                "zh-CN-XiaochenNeural",   # 女声-晓辰
                "zh-CN-XiaohanNeural",    # 女声-晓涵
                "zh-CN-XiaomengNeural",   # 女声-晓梦
                "zh-CN-XiaomoNeural",     # 女声-晓墨
                "zh-CN-XiaoqiuNeural",    # 女声-晓秋
                "zh-CN-XiaoruiNeural",    # 女声-晓睿
                "zh-CN-XiaoshuangNeural", # 女声-晓双
                "zh-CN-XiaoxuanNeural",   # 女声-晓萱
                "zh-CN-XiaoyanNeural",    # 女声-晓颜
                "zh-CN-XiaoyouNeural",    # 女声-晓悠
                "zh-CN-YunfengNeural",    # 男声-云枫
                "zh-CN-YunhaoNeural",     # 男声-云皓
            ]
        else:
            return []

    def test_tts(self, text: str = "这是一段测试语音,用于验证TTS功能是否正常工作。") -> bool:
        """
        测试TTS功能

        Args:
            text: 测试文字

        Returns:
            是否成功
        """
        print(f"\n🧪 测试TTS功能...")
        print(f"提供商: {self.provider}")

        result = self.generate_speech(text, "test_tts.mp3")

        if result["success"]:
            print(f"\n✅ TTS测试成功!")
            print(f"文件: {result['file_path']}")
            print(f"时长: {result.get('duration', 0):.1f}秒")
            return True
        else:
            print(f"\n❌ TTS测试失败: {result.get('error', 'unknown')}")
            return False


# 命令行测试
if __name__ == "__main__":
    import sys

    generator = TTSGenerator()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 测试模式
        generator.test_tts()
    elif len(sys.argv) > 1 and sys.argv[1] == "voices":
        # 列出可用声音
        print("\n可用声音列表:")
        voices = generator.list_available_voices()
        for i, voice in enumerate(voices, 1):
            print(f"  {i}. {voice}")
    elif len(sys.argv) > 1:
        # 从脚本生成
        script_path = sys.argv[1]
        generator.generate_speech_from_script(script_path)
    else:
        print("用法:")
        print("  python generator.py test              # 测试TTS功能")
        print("  python generator.py voices            # 列出可用声音")
        print("  python generator.py <script.json>     # 从脚本生成语音")
