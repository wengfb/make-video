"""
动态模块加载器
用于加载现有的业务模块，零修改复用现有代码
"""
import importlib.util
import sys
from pathlib import Path
from typing import Type, Any


class ModuleLoader:
    """
    动态加载现有业务模块
    使用importlib.util避免命名冲突
    """

    def __init__(self, scripts_dir: str = "scripts"):
        """
        初始化模块加载器

        Args:
            scripts_dir: scripts目录路径
        """
        self.scripts_dir = Path(scripts_dir)
        if not self.scripts_dir.exists():
            raise FileNotFoundError(f"Scripts目录不存在: {self.scripts_dir}")

    def _load_module(self, module_name: str, module_path: Path) -> Any:
        """
        通用模块加载方法

        Args:
            module_name: 模块名称（用于命名空间）
            module_path: 模块文件路径

        Returns:
            加载的模块对象
        """
        if not module_path.exists():
            raise FileNotFoundError(f"模块文件不存在: {module_path}")

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载模块: {module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return module

    def load_topic_generator(self) -> Type:
        """
        加载主题生成器

        Returns:
            TopicGenerator类
        """
        module = self._load_module(
            "topic_generator",
            self.scripts_dir / "0_topic_generator" / "generator.py"
        )
        return module.TopicGenerator

    def load_topic_manager(self) -> Type:
        """
        加载主题管理器

        Returns:
            TopicManager类
        """
        module = self._load_module(
            "topic_manager",
            self.scripts_dir / "0_topic_generator" / "manager.py"
        )
        return module.TopicManager

    def load_script_generator(self) -> Type:
        """
        加载脚本生成器

        Returns:
            ScriptGenerator类
        """
        module = self._load_module(
            "script_generator",
            self.scripts_dir / "1_script_generator" / "generator.py"
        )
        return module.ScriptGenerator

    def load_material_manager(self) -> Type:
        """
        加载素材管理器

        Returns:
            MaterialManager类
        """
        module = self._load_module(
            "material_manager",
            self.scripts_dir / "2_material_manager" / "manager.py"
        )
        return module.MaterialManager

    def load_ai_image_generator(self) -> Type:
        """
        加载AI图片生成器

        Returns:
            AIImageGenerator类
        """
        module = self._load_module(
            "ai_image_generator",
            self.scripts_dir / "2_material_manager" / "ai_generator.py"
        )
        return module.AIImageGenerator

    def load_video_composer(self) -> Type:
        """
        加载视频合成器

        Returns:
            VideoComposer类
        """
        module = self._load_module(
            "video_composer",
            self.scripts_dir / "3_video_editor" / "composer.py"
        )
        return module.VideoComposer

    def load_tts_generator(self) -> Type:
        """
        加载TTS语音生成器

        Returns:
            TTSGenerator类
        """
        module = self._load_module(
            "tts_generator",
            self.scripts_dir / "4_tts_generator" / "generator.py"
        )
        return module.TTSGenerator

    def load_tts_manager(self) -> Type:
        """
        加载TTS管理器

        Returns:
            TTSManager类
        """
        module = self._load_module(
            "tts_manager",
            self.scripts_dir / "4_tts_generator" / "manager.py"
        )
        return module.TTSManager

    def load_subtitle_generator(self) -> Type:
        """
        加载字幕生成器

        Returns:
            SubtitleGenerator类
        """
        module = self._load_module(
            "subtitle_generator",
            self.scripts_dir / "4_subtitle_generator" / "generator.py"
        )
        return module.SubtitleGenerator


# 全局单例
_module_loader = None


def get_module_loader() -> ModuleLoader:
    """
    获取全局模块加载器实例

    Returns:
        ModuleLoader实例
    """
    global _module_loader
    if _module_loader is None:
        _module_loader = ModuleLoader()
    return _module_loader
