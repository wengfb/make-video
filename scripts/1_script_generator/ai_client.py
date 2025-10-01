"""
AI客户端封装
支持多种AI服务提供商（OpenAI, Anthropic等）
"""

import json
import os
from typing import Dict, Any, Optional
import requests


class AIClient:
    """AI API客户端"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI客户端

        Args:
            config: AI配置字典，包含provider, model, api_key等
        """
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-4')
        self.api_key = config.get('api_key', os.getenv('OPENAI_API_KEY', ''))
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)

        if not self.api_key:
            raise ValueError("API key未设置！请在config/settings.json中配置api_key，或设置环境变量OPENAI_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        调用AI生成内容

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）

        Returns:
            生成的文本内容
        """
        if self.provider == 'openai':
            return self._generate_openai(prompt, system_prompt)
        elif self.provider == 'anthropic':
            return self._generate_anthropic(prompt, system_prompt)
        else:
            raise ValueError(f"不支持的AI提供商: {self.provider}")

    def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用OpenAI API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            'model': self.model,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            raise Exception(f"API调用失败: {str(e)}")

    def _generate_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用Anthropic API"""
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }

        data = {
            'model': self.model,
            'messages': [{"role": "user", "content": prompt}],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        if system_prompt:
            data['system'] = system_prompt

        try:
            response = requests.post(
                f'{self.base_url}/messages',
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result['content'][0]['text']
        except requests.exceptions.RequestException as e:
            raise Exception(f"API调用失败: {str(e)}")

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        生成JSON格式的内容

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）

        Returns:
            解析后的JSON字典
        """
        response = self.generate(prompt, system_prompt)

        # 尝试提取JSON内容（处理可能包含markdown代码块的情况）
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取代码块中的JSON
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0].strip()
                return json.loads(json_str)
            else:
                raise ValueError(f"无法解析JSON响应: {response[:200]}...")
