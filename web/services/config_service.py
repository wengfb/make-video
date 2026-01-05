"""
配置服务层
负责配置文件的读取、写入、验证、备份、API测试和审计日志
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import aiohttp
from openai import AsyncOpenAI


class ConfigService:
    """配置服务类"""

    def __init__(self):
        # 项目根目录
        self.project_root = Path(__file__).parent.parent.parent

        # 配置文件路径
        self.settings_path = self.project_root / "config" / "settings.json"
        self.templates_path = self.project_root / "config" / "templates.json"

        # 备份目录
        self.backup_dir = self.project_root / "config" / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # 审计日志文件
        self.audit_log_path = self.project_root / "config" / "audit.log"

        # 配置验证规则
        self._init_validation_rules()

    def _init_validation_rules(self):
        """初始化配置验证规则"""
        self.validation_rules = {
            "ai": {
                "provider": {"type": "str", "enum": ["openai", "glm", "anthropic"]},
                "model": {"type": "str"},
                "api_key": {"type": "str"},
                "base_url": {"type": "str"},
                "temperature": {"type": "float", "min": 0.0, "max": 2.0},
                "max_tokens": {"type": "int", "min": 1, "max": 128000}
            },
            "tts": {
                "provider": {"type": "str", "enum": ["edge", "openai"]},
                "model": {"type": "str"},
                "api_key": {"type": "str"},
                "voice": {"type": "str"},
                "speed": {"type": "float", "min": 0.25, "max": 4.0},
                "enable_bgm_mixing": {"type": "bool"},
                "bgm_volume": {"type": "float", "min": 0.0, "max": 1.0}
            },
            "ai_image": {
                "provider": {"type": "str", "enum": ["dalle", "cogview", "sd"]},
                "model": {"type": "str"},
                "api_key": {"type": "str"},
                "default_size": {"type": "str", "enum": ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]},
                "default_quality": {"type": "str", "enum": ["standard", "hd"]},
                "default_style": {"type": "str"}
            },
            "video": {
                "resolution": {"type": "dict"},
                "fps": {"type": "int", "min": 1, "max": 60},
                "output_format": {"type": "str", "enum": ["mp4", "avi", "mov"]},
                "codec": {"type": "str", "enum": ["libx264", "libx265", "mpeg4"]},
                "bitrate": {"type": "str"},
                "default_image_duration": {"type": "float", "min": 0.1, "max": 60.0},
                "transition_duration": {"type": "float", "min": 0.0, "max": 10.0}
            },
            "subtitle": {
                "font": {"type": "str"},
                "font_size": {"type": "int", "min": 10, "max": 100},
                "font_color": {"type": "str"},
                "bg_color": {"type": "str"},
                "bg_opacity": {"type": "float", "min": 0.0, "max": 1.0},
                "position": {"type": "str", "enum": ["top", "middle", "bottom"]}
            },
            "paths": {
                "materials": {"type": "str"},
                "templates": {"type": "str"},
                "output": {"type": "str"},
                "scripts": {"type": "str"},
                "subtitles": {"type": "str"},
                "videos": {"type": "str"},
                "audio": {"type": "str"}
            },
            "pexels": {
                "api_key": {"type": "str"},
                "rate_limit_per_hour": {"type": "int", "min": 1, "max": 1000}
            },
            "unsplash": {
                "access_key": {"type": "str"},
                "rate_limit_per_hour": {"type": "int", "min": 1, "max": 1000}
            }
        }

    # ==================== 配置读取 ====================

    def get_settings(self) -> Dict[str, Any]:
        """
        读取settings.json配置

        Returns:
            配置字典
        """
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {str(e)}")

    def get_templates(self) -> Dict[str, Any]:
        """
        读取templates.json配置

        Returns:
            配置字典
        """
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            raise ValueError(f"模板文件格式错误: {str(e)}")

    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置

        Returns:
            包含settings和templates的字典
        """
        return {
            "settings": self.get_settings(),
            "templates": self.get_templates()
        }

    # ==================== 配置更新 ====================

    def update_settings(self, updates: Dict[str, Any], backup: bool = True) -> Tuple[bool, str]:
        """
        更新settings.json配置

        Args:
            updates: 要更新的配置字典
            backup: 是否创建备份

        Returns:
            (成功状态, 消息)
        """
        try:
            # 读取当前配置
            current_config = self.get_settings()

            # 创建备份
            if backup:
                backup_id = self.backup_config("settings")
                print(f"已创建备份: {backup_id}")

            # 合并配置
            merged_config = self._deep_merge(current_config, updates)

            # 验证配置
            is_valid, errors, warnings = self.validate_settings(merged_config)
            if not is_valid:
                return False, f"配置验证失败: {', '.join(errors)}"

            # 写入配置文件
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(merged_config, f, indent=2, ensure_ascii=False)

            # 记录审计日志
            self.log_action("update", "settings", {
                "fields": list(updates.keys()),
                "backup_id": backup_id if backup else None
            })

            # 设置文件权限
            os.chmod(self.settings_path, 0o600)

            return True, "配置已更新" + (f" ({len(warnings)}个警告)" if warnings else "")

        except Exception as e:
            return False, f"更新配置失败: {str(e)}"

    def update_templates(self, updates: Dict[str, Any], backup: bool = True) -> Tuple[bool, str]:
        """
        更新templates.json配置

        Args:
            updates: 要更新的配置字典
            backup: 是否创建备份

        Returns:
            (成功状态, 消息)
        """
        try:
            # 读取当前配置
            current_config = self.get_templates()

            # 创建备份
            if backup:
                backup_id = self.backup_config("templates")
                print(f"已创建备份: {backup_id}")

            # 合并配置
            merged_config = self._deep_merge(current_config, updates)

            # 写入配置文件
            with open(self.templates_path, 'w', encoding='utf-8') as f:
                json.dump(merged_config, f, indent=2, ensure_ascii=False)

            # 记录审计日志
            self.log_action("update", "templates", {
                "fields": list(updates.keys()),
                "backup_id": backup_id if backup else None
            })

            return True, "模板配置已更新"

        except Exception as e:
            return False, f"更新模板配置失败: {str(e)}"

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """
        深度合并字典

        Args:
            base: 基础字典
            updates: 更新字典

        Returns:
            合并后的字典
        """
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # ==================== 配置验证 ====================

    def validate_settings(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        验证settings.json配置

        Args:
            config: 配置字典

        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        errors = []
        warnings = []

        # 验证各个配置区块
        for section, rules in self.validation_rules.items():
            if section not in config:
                warnings.append(f"缺少配置区块: {section}")
                continue

            section_config = config[section]
            section_errors = self._validate_section(section_config, rules, section)
            errors.extend(section_errors)

        # 检查API密钥是否配置（改为警告而非错误）
        if "ai" in config:
            api_key = config["ai"].get("api_key", "")
            if not api_key or api_key.startswith("YOUR_"):
                warnings.append("AI API密钥未配置或使用占位符，系统将无法正常工作")

        return len(errors) == 0, errors, warnings

    def validate_templates(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        验证templates.json配置

        Args:
            config: 配置字典

        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        errors = []
        warnings = []

        # 检查必需的顶级键
        required_keys = ["script_templates", "prompt_templates", "visual_templates"]
        for key in required_keys:
            if key not in config:
                errors.append(f"缺少必需的配置: {key}")

        return len(errors) == 0, errors, warnings

    def _validate_section(self, config: Dict, rules: Dict, section_name: str) -> List[str]:
        """
        验证配置区块

        Args:
            config: 配置字典
            rules: 验证规则
            section_name: 区块名称

        Returns:
            错误列表
        """
        errors = []

        for field, rule in rules.items():
            if field not in config:
                continue

            value = config[field]

            # 类型验证和自动转换
            if rule["type"] == "str":
                # 尝试转换为字符串
                if not isinstance(value, str):
                    try:
                        value = str(value)
                        config[field] = value  # 更新配置中的值
                    except:
                        errors.append(f"{section_name}.{field}: 类型错误，期望字符串")
                elif "enum" in rule and value not in rule["enum"]:
                    errors.append(f"{section_name}.{field}: 值 '{value}' 不在允许的选项中 {rule['enum']}")
            elif rule["type"] == "int":
                # 尝试将字符串转换为整数
                if isinstance(value, str):
                    try:
                        value = int(value)
                        config[field] = value  # 更新配置中的值
                    except ValueError:
                        errors.append(f"{section_name}.{field}: 无法将 '{value}' 转换为整数")
                        continue

                if not isinstance(value, int):
                    errors.append(f"{section_name}.{field}: 类型错误，期望整数")
                else:
                    if "min" in rule and value < rule["min"]:
                        errors.append(f"{section_name}.{field}: 值 {value} 小于最小值 {rule['min']}")
                    if "max" in rule and value > rule["max"]:
                        errors.append(f"{section_name}.{field}: 值 {value} 大于最大值 {rule['max']}")
            elif rule["type"] == "float":
                # 尝试将字符串转换为浮点数
                if isinstance(value, str):
                    try:
                        value = float(value)
                        config[field] = value  # 更新配置中的值
                    except ValueError:
                        errors.append(f"{section_name}.{field}: 无法将 '{value}' 转换为浮点数")
                        continue

                if not isinstance(value, (int, float)):
                    errors.append(f"{section_name}.{field}: 类型错误，期望浮点数")
                else:
                    if "min" in rule and value < rule["min"]:
                        errors.append(f"{section_name}.{field}: 值 {value} 小于最小值 {rule['min']}")
                    if "max" in rule and value > rule["max"]:
                        errors.append(f"{section_name}.{field}: 值 {value} 大于最大值 {rule['max']}")
            elif rule["type"] == "bool":
                # 尝试将字符串转换为布尔值
                if isinstance(value, str):
                    if value.lower() in ['true', '1', 'yes']:
                        value = True
                        config[field] = value
                    elif value.lower() in ['false', '0', 'no']:
                        value = False
                        config[field] = value
                    else:
                        errors.append(f"{section_name}.{field}: 无法将 '{value}' 转换为布尔值")
                        continue

                if not isinstance(value, bool):
                    errors.append(f"{section_name}.{field}: 类型错误，期望布尔值")
            elif rule["type"] == "dict":
                if not isinstance(value, dict):
                    errors.append(f"{section_name}.{field}: 类型错误，期望字典")

        return errors

    # ==================== API密钥测试 ====================

    async def test_ai_api(self, provider: str, api_key: str, base_url: str, model: str) -> Tuple[bool, str]:
        """
        测试AI API密钥

        Args:
            provider: 提供商（openai/glm/anthropic）
            api_key: API密钥
            base_url: API地址
            model: 模型名称

        Returns:
            (测试结果, 消息)
        """
        try:
            if provider == "openai":
                return await self._test_openai_api(api_key, base_url, model)
            elif provider == "glm":
                return await self._test_glm_api(api_key, base_url, model)
            elif provider == "anthropic":
                return await self._test_anthropic_api(api_key, base_url, model)
            else:
                return False, f"不支持的提供商: {provider}"
        except Exception as e:
            return False, f"API测试失败: {str(e)}"

    async def _test_openai_api(self, api_key: str, base_url: str, model: str) -> Tuple[bool, str]:
        """测试OpenAI API"""
        try:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)

            # 尝试列出模型
            response = await client.models.list()

            # 检查指定模型是否可用
            models = [m.id for m in response.data]
            if model in models:
                return True, f"API密钥有效，模型 {model} 可用"
            else:
                return True, f"API密钥有效（可用模型: {', '.join(models[:5])}...）"
        except Exception as e:
            return False, f"OpenAI API测试失败: {str(e)}"

    async def _test_glm_api(self, api_key: str, base_url: str, model: str) -> Tuple[bool, str]:
        """测试智谱AI API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # 发送测试请求
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 10
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True, f"智谱AI API密钥有效，模型 {model} 可用"
                    else:
                        error = await response.text()
                        return False, f"智谱AI API返回错误: {error}"
        except Exception as e:
            return False, f"智谱AI API测试失败: {str(e)}"

    async def _test_anthropic_api(self, api_key: str, base_url: str, model: str) -> Tuple[bool, str]:
        """测试Anthropic API"""
        # TODO: 实现Anthropic API测试
        return True, "Anthropic API测试暂未实现"

    async def test_image_api(self, provider: str, api_key: str) -> Tuple[bool, str]:
        """
        测试图片生成API密钥

        Args:
            provider: 提供商（dalle/cogview/sd）
            api_key: API密钥

        Returns:
            (测试结果, 消息)
        """
        # TODO: 实现图片API测试
        return True, f"图片API测试暂未实现 ({provider})"

    # ==================== 备份和恢复 ====================

    def backup_config(self, config_type: str) -> str:
        """
        备份配置文件

        Args:
            config_type: 配置类型（settings/templates）

        Returns:
            备份ID（文件名）
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if config_type == "settings":
            src_path = self.settings_path
        elif config_type == "templates":
            src_path = self.templates_path
        else:
            raise ValueError(f"不支持的配置类型: {config_type}")

        backup_filename = f"{config_type}.json.{timestamp}"
        backup_path = self.backup_dir / backup_filename

        shutil.copy2(src_path, backup_path)

        # 清理旧备份（保留最近10个）
        self._cleanup_old_backups(config_type)

        return backup_filename

    def restore_config(self, config_type: str, backup_id: str) -> Tuple[bool, str]:
        """
        恢复配置备份

        Args:
            config_type: 配置类型（settings/templates）
            backup_id: 备份ID（文件名）

        Returns:
            (成功状态, 消息)
        """
        try:
            backup_path = self.backup_dir / backup_id

            if not backup_path.exists():
                return False, f"备份文件不存在: {backup_id}"

            if config_type == "settings":
                target_path = self.settings_path
            elif config_type == "templates":
                target_path = self.templates_path
            else:
                return False, f"不支持的配置类型: {config_type}"

            # 创建当前配置的备份
            current_backup = self.backup_config(config_type)

            # 恢复备份
            shutil.copy2(backup_path, target_path)

            # 记录审计日志
            self.log_action("restore", config_type, {
                "backup_id": backup_id,
                "current_backup": current_backup
            })

            return True, f"已从备份 {backup_id} 恢复"

        except Exception as e:
            return False, f"恢复备份失败: {str(e)}"

    def get_backup_history(self, config_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取备份历史

        Args:
            config_type: 配置类型（settings/templates）
            limit: 返回数量限制

        Returns:
            备份列表
        """
        pattern = f"{config_type}.json.*"
        backups = []

        for backup_file in sorted(self.backup_dir.glob(pattern), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "id": backup_file.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

            if len(backups) >= limit:
                break

        return backups

    def _cleanup_old_backups(self, config_type: str, keep: int = 10):
        """
        清理旧备份

        Args:
            config_type: 配置类型
            keep: 保留数量
        """
        pattern = f"{config_type}.json.*"
        backups = sorted(self.backup_dir.glob(pattern), reverse=True)

        # 删除超过保留数量的旧备份
        for old_backup in backups[keep:]:
            old_backup.unlink()

    # ==================== 审计日志 ====================

    def log_action(self, action: str, config_type: str, details: Dict[str, Any]):
        """
        记录审计日志

        Args:
            action: 操作类型（update/test/backup/restore）
            config_type: 配置类型（settings/templates）
            details: 详细信息
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "config_type": config_type,
            "details": details
        }

        try:
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"写入审计日志失败: {str(e)}")

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取审计日志

        Args:
            limit: 返回数量限制

        Returns:
            日志列表
        """
        logs = []

        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue

                    if len(logs) >= limit:
                        break

        except FileNotFoundError:
            pass

        return logs[-limit:][::-1]  # 返回最近的日志


# ==================== 单例模式 ====================

_config_service_instance = None


def get_config_service() -> ConfigService:
    """获取配置服务实例（单例模式）"""
    global _config_service_instance
    if _config_service_instance is None:
        _config_service_instance = ConfigService()
    return _config_service_instance
