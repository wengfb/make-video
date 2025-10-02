#!/usr/bin/env python3
"""
TTS语音管理器
管理生成的语音文件,提供查询、合并等功能
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class TTSManager:
    """TTS语音管理器类"""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        初始化TTS管理器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.audio_dir = Path(self.config["paths"]["audio"]) / "tts"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {str(e)}")
            return {"paths": {"audio": "materials/audio"}}

    def list_all_audio(self) -> List[Dict]:
        """
        列出所有生成的语音文件

        Returns:
            语音文件列表
        """
        audio_list = []

        # 查找所有元数据文件
        for metadata_file in self.audio_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # 添加文件信息
                metadata["metadata_file"] = str(metadata_file)
                metadata["created_time"] = datetime.fromtimestamp(
                    metadata_file.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")

                audio_list.append(metadata)

            except Exception as e:
                print(f"⚠️  读取元数据失败 {metadata_file}: {str(e)}")

        # 按创建时间排序
        audio_list.sort(key=lambda x: x.get("created_time", ""), reverse=True)

        return audio_list

    def get_audio_by_script(self, script_title: str) -> Optional[Dict]:
        """
        根据脚本标题查找语音

        Args:
            script_title: 脚本标题

        Returns:
            语音元数据或None
        """
        audio_list = self.list_all_audio()

        for audio in audio_list:
            if audio.get("script_title", "") == script_title:
                return audio

        return None

    def get_audio_files(self, metadata_path: str) -> List[str]:
        """
        从元数据获取所有音频文件路径

        Args:
            metadata_path: 元数据文件路径

        Returns:
            音频文件路径列表
        """
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            audio_files = metadata.get("audio_files", [])
            return [item["file_path"] for item in audio_files]

        except Exception as e:
            print(f"❌ 获取音频文件列表失败: {str(e)}")
            return []

    def merge_audio_files(self, audio_files: List[str], output_path: str,
                         crossfade: float = 0.0) -> bool:
        """
        合并多个音频文件

        Args:
            audio_files: 音频文件路径列表
            output_path: 输出文件路径
            crossfade: 交叉淡入淡出时长(秒)

        Returns:
            是否成功
        """
        try:
            from moviepy import AudioFileClip, concatenate_audioclips

            print(f"\n🔀 合并 {len(audio_files)} 个音频文件...")

            # 加载所有音频
            clips = []
            for audio_file in audio_files:
                if not os.path.exists(audio_file):
                    print(f"⚠️  文件不存在: {audio_file}")
                    continue

                clip = AudioFileClip(audio_file)
                clips.append(clip)

            if not clips:
                print("❌ 没有有效的音频文件")
                return False

            # 合并音频
            if crossfade > 0:
                # 带交叉淡入淡出
                final_audio = concatenate_audioclips(clips, method="compose")
            else:
                # 直接拼接
                final_audio = concatenate_audioclips(clips)

            # 保存
            final_audio.write_audiofile(output_path, fps=44100)

            # 清理
            for clip in clips:
                clip.close()
            final_audio.close()

            print(f"✅ 音频合并完成: {output_path}")
            print(f"⏱️  总时长: {final_audio.duration:.1f}秒")

            return True

        except Exception as e:
            print(f"❌ 合并音频失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def delete_audio(self, metadata_path: str, delete_files: bool = True) -> bool:
        """
        删除语音文件和元数据

        Args:
            metadata_path: 元数据文件路径
            delete_files: 是否同时删除音频文件

        Returns:
            是否成功
        """
        try:
            # 读取元数据
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 删除音频文件
            if delete_files:
                audio_files = metadata.get("audio_files", [])
                for item in audio_files:
                    audio_path = item.get("file_path", "")
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                        print(f"🗑️  删除: {audio_path}")

            # 删除元数据文件
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                print(f"🗑️  删除元数据: {metadata_path}")

            print("✅ 删除成功")
            return True

        except Exception as e:
            print(f"❌ 删除失败: {str(e)}")
            return False

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        audio_list = self.list_all_audio()

        total_files = len(audio_list)
        total_duration = sum(audio.get("total_duration", 0) for audio in audio_list)
        total_sections = sum(audio.get("generated_sections", 0) for audio in audio_list)

        # 统计提供商
        providers = {}
        for audio in audio_list:
            provider = audio.get("provider", "unknown")
            providers[provider] = providers.get(provider, 0) + 1

        return {
            "total_projects": total_files,
            "total_sections": total_sections,
            "total_duration": total_duration,
            "avg_duration": total_duration / total_files if total_files > 0 else 0,
            "providers": providers,
        }

    def print_audio_list(self, audio_list: Optional[List[Dict]] = None):
        """
        打印语音文件列表

        Args:
            audio_list: 语音列表(可选,默认查询所有)
        """
        if audio_list is None:
            audio_list = self.list_all_audio()

        if not audio_list:
            print("\n📭 还没有生成任何语音文件")
            return

        print(f"\n📚 已生成的语音文件 (共{len(audio_list)}个):")
        print("=" * 80)

        for i, audio in enumerate(audio_list, 1):
            print(f"\n{i}. {audio.get('script_title', '未命名')}")
            print(f"   脚本: {audio.get('script_path', 'N/A')}")
            print(f"   章节: {audio.get('generated_sections', 0)}/{audio.get('total_sections', 0)}")
            print(f"   时长: {audio.get('total_duration', 0):.1f}秒")
            print(f"   提供商: {audio.get('provider', 'unknown')} | 声音: {audio.get('voice', 'default')}")
            print(f"   创建时间: {audio.get('created_time', 'N/A')}")
            print(f"   元数据: {audio.get('metadata_file', 'N/A')}")

        print("\n" + "=" * 80)

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()

        print("\n📊 TTS语音统计:")
        print("=" * 60)
        print(f"  项目总数: {stats['total_projects']}")
        print(f"  章节总数: {stats['total_sections']}")
        print(f"  总时长: {stats['total_duration']:.1f}秒 ({stats['total_duration']/60:.1f}分钟)")
        print(f"  平均时长: {stats['avg_duration']:.1f}秒")

        if stats['providers']:
            print(f"\n  提供商分布:")
            for provider, count in stats['providers'].items():
                print(f"    - {provider}: {count}个项目")

        print("=" * 60)

    def interactive_menu(self):
        """交互式菜单"""
        while True:
            print("\n" + "=" * 60)
            print("TTS语音管理器")
            print("=" * 60)
            print("1. 查看所有语音文件")
            print("2. 查看统计信息")
            print("3. 合并音频文件")
            print("4. 删除语音文件")
            print("0. 返回")
            print("=" * 60)

            choice = input("请选择操作: ").strip()

            if choice == "1":
                self.print_audio_list()

            elif choice == "2":
                self.print_statistics()

            elif choice == "3":
                # 合并音频
                audio_list = self.list_all_audio()
                if not audio_list:
                    print("📭 还没有生成任何语音文件")
                    continue

                self.print_audio_list(audio_list)

                try:
                    index = int(input("\n请选择要合并的项目编号: ")) - 1
                    if 0 <= index < len(audio_list):
                        metadata_path = audio_list[index]["metadata_file"]
                        audio_files = self.get_audio_files(metadata_path)

                        if audio_files:
                            output_name = input("输出文件名 (不含扩展名): ").strip()
                            output_path = self.audio_dir / f"{output_name}_merged.mp3"

                            self.merge_audio_files(audio_files, str(output_path))
                        else:
                            print("❌ 没有找到音频文件")
                    else:
                        print("❌ 无效的编号")
                except ValueError:
                    print("❌ 请输入有效的数字")

            elif choice == "4":
                # 删除语音
                audio_list = self.list_all_audio()
                if not audio_list:
                    print("📭 还没有生成任何语音文件")
                    continue

                self.print_audio_list(audio_list)

                try:
                    index = int(input("\n请选择要删除的项目编号: ")) - 1
                    if 0 <= index < len(audio_list):
                        confirm = input("⚠️  确认删除? (y/n): ").strip().lower()
                        if confirm == 'y':
                            metadata_path = audio_list[index]["metadata_file"]
                            self.delete_audio(metadata_path, delete_files=True)
                    else:
                        print("❌ 无效的编号")
                except ValueError:
                    print("❌ 请输入有效的数字")

            elif choice == "0":
                break

            else:
                print("❌ 无效的选择")


# 命令行测试
if __name__ == "__main__":
    manager = TTSManager()
    manager.interactive_menu()
