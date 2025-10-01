#!/usr/bin/env python3
"""
依赖检查工具
检查系统环境和必要依赖是否满足
"""

import sys
import subprocess
import importlib.util


class DependencyChecker:
    """依赖检查器"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def check_python_version(self, min_version=(3, 8)):
        """
        检查Python版本

        Args:
            min_version: 最低版本要求 (major, minor)
        """
        current = sys.version_info[:2]
        if current < min_version:
            self.errors.append(
                f"Python版本过低: 当前{current[0]}.{current[1]}, "
                f"需要>={min_version[0]}.{min_version[1]}"
            )
            return False
        return True

    def check_package(self, package_name, import_name=None, required=True):
        """
        检查Python包是否安装

        Args:
            package_name: pip包名
            import_name: 导入名称(如果与包名不同)
            required: 是否必需
        """
        import_name = import_name or package_name

        spec = importlib.util.find_spec(import_name)
        if spec is None:
            msg = f"缺少依赖: {package_name}"
            if required:
                self.errors.append(msg)
                return False
            else:
                self.warnings.append(msg)
                return False
        return True

    def check_ffmpeg(self):
        """检查FFmpeg是否安装"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        self.errors.append(
            "FFmpeg未安装。请安装:\n"
            "  Ubuntu/Debian: sudo apt-get install ffmpeg\n"
            "  macOS: brew install ffmpeg\n"
            "  Windows: 从 https://ffmpeg.org/download.html 下载"
        )
        return False

    def check_all(self):
        """执行完整的依赖检查"""
        print("🔍 检查系统环境...")
        print("=" * 60)

        # 1. Python版本
        print("\n📌 Python版本:")
        if self.check_python_version():
            print(f"  ✅ Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")

        # 2. 核心依赖
        print("\n📌 核心依赖:")
        core_packages = [
            ('openai', 'openai', True),
            ('requests', 'requests', True),
            ('numpy', 'numpy', True),
        ]

        for pkg_name, import_name, required in core_packages:
            if self.check_package(pkg_name, import_name, required):
                print(f"  ✅ {pkg_name}")

        # 3. 视频处理依赖
        print("\n📌 视频处理:")
        video_packages = [
            ('moviepy', 'moviepy', True),
            ('imageio', 'imageio', True),
            ('Pillow', 'PIL', True),
        ]

        for pkg_name, import_name, required in video_packages:
            if self.check_package(pkg_name, import_name, required):
                print(f"  ✅ {pkg_name}")

        # 4. TTS依赖
        print("\n📌 TTS语音合成:")
        tts_packages = [
            ('edge-tts', 'edge_tts', False),
        ]

        for pkg_name, import_name, required in tts_packages:
            if self.check_package(pkg_name, import_name, required):
                print(f"  ✅ {pkg_name} (可选)")

        # 5. 字幕依赖
        print("\n📌 字幕生成:")
        subtitle_packages = [
            ('pysrt', 'pysrt', False),
        ]

        for pkg_name, import_name, required in subtitle_packages:
            if self.check_package(pkg_name, import_name, required):
                print(f"  ✅ {pkg_name} (可选)")

        # 6. FFmpeg
        print("\n📌 系统工具:")
        if self.check_ffmpeg():
            print("  ✅ FFmpeg")

        # 输出结果
        print("\n" + "=" * 60)

        if self.errors:
            print("\n❌ 发现错误:")
            for error in self.errors:
                print(f"  • {error}")

            print("\n💡 修复建议:")
            print("  1. 安装缺少的依赖:")
            print("     pip install -r requirements.txt")
            print("  2. 安装FFmpeg (如缺失)")
            return False

        if self.warnings:
            print("\n⚠️  警告 (可选依赖):")
            for warning in self.warnings:
                print(f"  • {warning}")
            print("\n部分功能可能不可用,但核心功能正常。")

        print("\n✅ 环境检查通过!")
        return True


def quick_check():
    """快速检查 - 仅检查核心依赖"""
    checker = DependencyChecker()

    # 核心包
    packages = ['openai', 'requests', 'numpy', 'moviepy']

    for pkg in packages:
        import_name = 'PIL' if pkg == 'Pillow' else pkg
        if not checker.check_package(pkg, import_name, True):
            return False

    return len(checker.errors) == 0


if __name__ == "__main__":
    checker = DependencyChecker()
    success = checker.check_all()
    sys.exit(0 if success else 1)
