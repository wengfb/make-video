"""
脚本服务
封装ScriptGenerator，提供Web界面使用的业务逻辑
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from web.utils.module_loader import get_module_loader
from web.services.task_manager import get_task_manager


class ScriptService:
    """脚本服务类"""

    def __init__(self):
        """初始化脚本服务"""
        self.loader = get_module_loader()

        # 动态加载ScriptGenerator
        ScriptGenerator = self.loader.load_script_generator()
        self.generator = ScriptGenerator()

    def generate_script_async(
        self,
        task_id: str,
        topic: str,
        template_name: str = "popular_science",
        duration: str = "3-5min",
        audience: str = "general_public",
        custom_requirements: str = ""
    ) -> None:
        """
        异步生成脚本（后台任务）

        Args:
            task_id: 任务ID
            topic: 主题（可以是主题ID或主题标题）
            template_name: 模板名称
            duration: 视频时长
            audience: 目标受众
            custom_requirements: 自定义要求
        """
        task_manager = get_task_manager()

        def progress_callback(progress: int, message: str):
            """进度回调函数"""
            task_manager.update_progress(task_id, progress, message)

        try:
            progress_callback(5, "初始化AI客户端...")

            # 准备参数
            params = {
                "topic": topic,
                "template_name": template_name,
                "duration": duration,
                "audience": audience,
                "custom_requirements": custom_requirements if custom_requirements else None
            }

            progress_callback(10, "分析主题...")

            # 调用ScriptGenerator生成脚本
            script = self.generator.generate_script(**params)

            progress_callback(80, "保存脚本...")

            # 保存脚本到文件
            script_path = self.generator.save_script(script)

            progress_callback(100, "脚本生成完成")

            # 标记任务完成
            task_manager.complete_task(task_id, {
                "script": script,
                "script_path": script_path,
                "title": script.get("title", ""),
                "total_duration": script.get("total_duration", 0),
                "section_count": len(script.get("sections", []))
            })

        except Exception as e:
            # 任务失败
            error_msg = f"生成脚本失败: {str(e)}"
            progress_callback(0, error_msg)
            task_manager.fail_task(task_id, str(e))

    def generate_from_topic_async(
        self,
        task_id: str,
        topic_data: Dict[str, Any],
        template_name: str = "popular_science",
        custom_requirements: str = ""
    ) -> None:
        """
        从主题字典异步生成脚本

        Args:
            task_id: 任务ID
            topic_data: 主题数据字典
            template_name: 模板名称
            custom_requirements: 自定义要求
        """
        task_manager = get_task_manager()

        def progress_callback(progress: int, message: str):
            """进度回调函数"""
            task_manager.update_progress(task_id, progress, message)

        try:
            progress_callback(5, "读取主题信息...")

            # 调用generate_from_topic
            script = self.generator.generate_from_topic(
                topic=topic_data,
                template_name=template_name,
                custom_requirements=custom_requirements if custom_requirements else None
            )

            progress_callback(80, "保存脚本...")

            # 保存脚本
            script_path = self.generator.save_script(script)

            progress_callback(100, "脚本生成完成")

            # 标记任务完成
            task_manager.complete_task(task_id, {
                "script": script,
                "script_path": script_path,
                "title": script.get("title", ""),
                "total_duration": script.get("total_duration", 0),
                "section_count": len(script.get("sections", []))
            })

        except Exception as e:
            # 任务失败
            error_msg = f"生成脚本失败: {str(e)}"
            progress_callback(0, error_msg)
            task_manager.fail_task(task_id, str(e))

    def get_script(self, script_path: str) -> Optional[Dict[str, Any]]:
        """
        从文件读取脚本

        Args:
            script_path: 脚本文件路径

        Returns:
            脚本数据
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取脚本失败: {e}")
            return None

    def list_scripts(self, scripts_dir: str = "output/scripts") -> List[Dict[str, Any]]:
        """
        列出所有脚本

        Args:
            scripts_dir: 脚本目录

        Returns:
            脚本信息列表
        """
        scripts = []
        scripts_path = Path(scripts_dir)

        if not scripts_path.exists():
            return scripts

        for script_file in scripts_path.glob("*.json"):
            try:
                script = self.get_script(str(script_file))
                if script:
                    scripts.append({
                        "path": str(script_file),
                        "name": script_file.stem,
                        "title": script.get("title", script_file.stem),
                        "duration": script.get("total_duration", 0),
                        "section_count": len(script.get("sections", [])),
                        "template": script.get("metadata", {}).get("template", "unknown"),
                        "created_at": script.get("metadata", {}).get("generated_at", "")
                    })
            except Exception as e:
                print(f"读取脚本 {script_file} 失败: {e}")

        # 按创建时间倒序排序
        scripts.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return scripts

    def delete_script(self, script_path: str) -> bool:
        """
        删除脚本文件

        Args:
            script_path: 脚本文件路径

        Returns:
            是否删除成功
        """
        try:
            Path(script_path).unlink()
            return True
        except Exception as e:
            print(f"删除脚本失败: {e}")
            return False

    def list_templates(self) -> List[str]:
        """
        获取可用的脚本模板列表

        Returns:
            模板名称列表
        """
        # 返回可用的模板列表（从config/templates.json读取）
        try:
            import json
            templates_path = Path("config/templates.json")
            if templates_path.exists():
                with open(templates_path, 'r', encoding='utf-8') as f:
                    templates_data = json.load(f)
                    # 返回脚本模板的键列表
                    if "script_templates" in templates_data:
                        return list(templates_data["script_templates"].keys())
        except Exception as e:
            print(f"读取模板文件失败: {e}")

        # 返回默认模板列表
        return [
            "popular_science",
            "experiment_demo",
            "concept_explanation"
        ]

    def save_script(self, script: Dict[str, Any], filename: str = None) -> str:
        """
        保存脚本到文件

        Args:
            script: 脚本数据
            filename: 文件名（可选）

        Returns:
            保存的文件路径
        """
        try:
            if filename:
                # 保存到指定文件
                script_path = Path("output/scripts") / f"{filename}.json"
                script_path.parent.mkdir(exist_ok=True)

                with open(script_path, 'w', encoding='utf-8') as f:
                    json.dump(script, f, ensure_ascii=False, indent=2)

                return str(script_path)
            else:
                # 使用默认保存方法
                return self.generator.save_script(script)
        except Exception as e:
            raise Exception(f"保存脚本失败: {str(e)}")


# 全局单例
_script_service = None


def get_script_service() -> ScriptService:
    """
    获取全局脚本服务实例

    Returns:
        ScriptService实例
    """
    global _script_service
    if _script_service is None:
        _script_service = ScriptService()
    return _script_service
