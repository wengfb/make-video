"""
脚本生成器核心模块
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

# 修复相对导入问题 - 添加当前目录到系统路径
sys.path.insert(0, os.path.dirname(__file__))
from ai_client import AIClient


class ScriptGenerator:
    """视频脚本生成器"""

    def __init__(self, config_path: str = 'config/settings.json'):
        """
        初始化脚本生成器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 加载模板
        template_path = 'config/templates.json'
        with open(template_path, 'r', encoding='utf-8') as f:
            self.templates = json.load(f)

        # 初始化AI客户端
        self.ai_client = AIClient(self.config['ai'])

        # 获取脚本生成配置
        self.script_config = self.config.get('script_generator', {})

    def generate_script(
        self,
        topic: str,
        template_name: str = 'popular_science',
        duration: Optional[str] = None,
        audience: Optional[str] = None,
        custom_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成视频脚本

        Args:
            topic: 视频主题
            template_name: 使用的模板名称
            duration: 视频时长（如"3-5min"）
            audience: 目标受众
            custom_requirements: 自定义需求

        Returns:
            生成的脚本字典
        """
        # 获取模板
        if template_name not in self.templates['script_templates']:
            raise ValueError(f"模板 '{template_name}' 不存在")

        template = self.templates['script_templates'][template_name]

        # 使用配置的默认值
        duration = duration or self.script_config.get('video_length', '3-5min')
        audience = audience or self.script_config.get('target_audience', 'general_public')

        # 构建结构说明
        structure_desc = self._build_structure_description(template['structure'])

        # 构建提示词
        prompt_template = self.templates['prompt_templates']['script_generation']
        prompt = prompt_template.format(
            topic=topic,
            audience=self._translate_audience(audience),
            duration=duration,
            style=template['name'],
            structure=structure_desc
        )

        if custom_requirements:
            prompt += f"\n\n额外要求：\n{custom_requirements}"

        print(f"\n🤖 正在生成脚本...\n主题: {topic}\n模板: {template['name']}\n")

        # 调用AI生成
        try:
            script_data = self.ai_client.generate_json(prompt)

            # 添加元数据
            script_data['metadata'] = {
                'topic': topic,
                'template': template_name,
                'duration': duration,
                'audience': audience,
                'generated_at': datetime.now().isoformat(),
                'generator_version': self.config['project']['version']
            }

            return script_data

        except Exception as e:
            raise Exception(f"脚本生成失败: {str(e)}")

    def generate_hook(self, topic: str) -> str:
        """
        单独生成开场钩子

        Args:
            topic: 视频主题

        Returns:
            开场钩子文本
        """
        prompt_template = self.templates['prompt_templates']['hook_generation']
        prompt = prompt_template.format(topic=topic)

        return self.ai_client.generate(prompt)

    def generate_titles(self, script_summary: str) -> List[str]:
        """
        基于脚本生成标题选项

        Args:
            script_summary: 脚本摘要

        Returns:
            标题列表
        """
        prompt_template = self.templates['prompt_templates']['title_generation']
        prompt = prompt_template.format(script_summary=script_summary)

        response = self.ai_client.generate(prompt)

        # 解析标题列表
        titles = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # 移除序号和标记
                title = line.split('.', 1)[-1].split(')', 1)[-1].split('-', 1)[-1].strip()
                if title:
                    titles.append(title)

        return titles[:5]  # 最多返回5个

    def suggest_visuals(self, script_content: str) -> Dict[str, Any]:
        """
        为脚本内容建议视觉元素

        Args:
            script_content: 脚本内容

        Returns:
            视觉建议字典
        """
        prompt_template = self.templates['prompt_templates']['visual_suggestion']
        prompt = prompt_template.format(script_content=script_content)

        try:
            return self.ai_client.generate_json(prompt)
        except:
            # 如果返回的不是JSON，则返回文本
            response = self.ai_client.generate(prompt)
            return {'suggestions': response}

    def save_script(self, script_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        保存脚本到文件

        Args:
            script_data: 脚本数据
            filename: 文件名（可选，默认使用时间戳）

        Returns:
            保存的文件路径
        """
        output_dir = self.config['paths']['scripts']
        os.makedirs(output_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            topic = script_data.get('metadata', {}).get('topic', 'script')
            # 清理文件名中的非法字符
            topic_clean = ''.join(c for c in topic if c.isalnum() or c in (' ', '-', '_'))[:30]
            filename = f"{timestamp}_{topic_clean}.json"

        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)

        # 同时保存为易读的文本格式
        txt_filepath = filepath.replace('.json', '.txt')
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            self._write_readable_script(f, script_data)

        print(f"\n✅ 脚本已保存:")
        print(f"   JSON: {filepath}")
        print(f"   TXT:  {txt_filepath}")

        return filepath

    def _build_structure_description(self, structure: List[Dict[str, str]]) -> str:
        """构建结构描述文本"""
        lines = []
        for i, section in enumerate(structure, 1):
            lines.append(f"{i}. {section['name']} ({section['duration']})")
            lines.append(f"   {section['prompt']}")
        return '\n'.join(lines)

    def _translate_audience(self, audience: str) -> str:
        """翻译受众类型"""
        translations = {
            'general_public': '普通大众',
            'students': '学生群体',
            'professionals': '专业人士',
            'children': '儿童观众',
            'teenagers': '青少年'
        }
        return translations.get(audience, audience)

    def _write_readable_script(self, f, script_data: Dict[str, Any]):
        """将脚本写入可读的文本格式"""
        # 写入标题
        title = script_data.get('title', '未命名视频')
        f.write(f"{'='*60}\n")
        f.write(f"{title:^60}\n")
        f.write(f"{'='*60}\n\n")

        # 写入元数据
        if 'metadata' in script_data:
            meta = script_data['metadata']
            f.write(f"主题: {meta.get('topic', 'N/A')}\n")
            f.write(f"模板: {meta.get('template', 'N/A')}\n")
            f.write(f"时长: {meta.get('duration', 'N/A')}\n")
            f.write(f"生成时间: {meta.get('generated_at', 'N/A')}\n")
            f.write(f"\n{'-'*60}\n\n")

        # 写入各部分内容
        if 'sections' in script_data:
            for i, section in enumerate(script_data['sections'], 1):
                section_name = section.get('section_name', f'第{i}部分')
                duration = section.get('duration', 'N/A')
                narration = section.get('narration', '')
                visual_notes = section.get('visual_notes', '')

                f.write(f"【{section_name}】 ({duration})\n")
                f.write(f"\n旁白:\n{narration}\n")
                if visual_notes:
                    f.write(f"\n视觉提示:\n{visual_notes}\n")
                f.write(f"\n{'-'*60}\n\n")

    def list_templates(self) -> List[Dict[str, str]]:
        """
        列出所有可用的模板

        Returns:
            模板信息列表
        """
        templates = []
        for name, template in self.templates['script_templates'].items():
            templates.append({
                'name': name,
                'display_name': template['name'],
                'description': template['description']
            })
        return templates

    def generate_from_topic(self, topic: Dict[str, Any]) -> str:
        """
        从主题字典生成脚本（用于完整工作流）

        Args:
            topic: 主题字典，包含title, description等字段

        Returns:
            脚本JSON文件路径
        """
        # 提取主题信息
        topic_title = topic.get('title', '')
        topic_desc = topic.get('description', '')
        topic_field = topic.get('field', '')

        # 构建自定义要求
        custom_req = f"主题描述: {topic_desc}"
        if topic_field:
            custom_req += f"\n领域: {topic_field}"

        # 生成脚本
        script = self.generate_script(
            topic=topic_title,
            template_name='popular_science',
            custom_requirements=custom_req
        )

        # 保存脚本
        filepath = self.save_script(script)

        return filepath
