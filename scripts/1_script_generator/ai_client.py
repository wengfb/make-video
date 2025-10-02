"""
AI客户端封装
支持多种AI服务提供商（OpenAI, Anthropic等）
"""

import json
import os
import time
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
        elif self.provider == 'glm':
            return self._generate_glm(prompt, system_prompt)
        else:
            raise ValueError(f"不支持的AI提供商: {self.provider}")

    def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用OpenAI API (带重试机制)"""
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

        # 重试机制：最多3次，指数退避
        max_retries = 3
        retry_delays = [1, 2, 4]  # 秒

        for attempt in range(max_retries):
            try:
                # 确保URL正确拼接（去除base_url末尾的斜杠）
                base = self.base_url.rstrip('/')
                url = f'{base}/chat/completions'

                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']

            except requests.exceptions.Timeout as e:
                # 超时错误，可重试
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    print(f"\n⚠️  API请求超时，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                else:
                    raise Exception(f"API调用超时（已重试{max_retries}次）: {str(e)}")

            except requests.exceptions.ConnectionError as e:
                # 网络连接错误，可重试
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    print(f"\n⚠️  网络连接错误，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                else:
                    raise Exception(f"网络连接失败（已重试{max_retries}次）: {str(e)}")

            except requests.exceptions.HTTPError as e:
                # HTTP错误，检查是否可重试
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    # 限流或服务器错误，可重试
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        print(f"\n⚠️  API错误 ({e.response.status_code})，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                        time.sleep(delay)
                    else:
                        raise Exception(f"API调用失败（已重试{max_retries}次）: {str(e)}")
                else:
                    # 其他HTTP错误（如401认证失败），不重试
                    raise Exception(f"API调用失败: {str(e)}")

            except requests.exceptions.RequestException as e:
                # 其他请求错误
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

    def _generate_glm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        调用智谱AI GLM API (使用OpenAI兼容接口，带重试机制)

        智谱AI完全兼容OpenAI API格式，只需使用不同的base_url
        支持的模型：glm-4, glm-4-plus, glm-4-air, glm-4-flash等
        """
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

        # 重试机制：最多3次，指数退避
        max_retries = 3
        retry_delays = [1, 2, 4]  # 秒

        for attempt in range(max_retries):
            try:
                # 确保URL正确拼接（去除base_url末尾的斜杠）
                base = self.base_url.rstrip('/')
                url = f'{base}/chat/completions'

                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=120  # GLM需要更长的超时时间（特别是复杂prompt）
                )
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']

            except requests.exceptions.Timeout as e:
                # 超时错误，可重试
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    print(f"\n⚠️  GLM API请求超时，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                else:
                    raise Exception(f"GLM API调用超时（已重试{max_retries}次）: {str(e)}")

            except requests.exceptions.ConnectionError as e:
                # 网络连接错误，可重试
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    print(f"\n⚠️  网络连接错误，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                else:
                    raise Exception(f"网络连接失败（已重试{max_retries}次）: {str(e)}")

            except requests.exceptions.HTTPError as e:
                # HTTP错误，检查是否可重试
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    # 限流或服务器错误，可重试
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        print(f"\n⚠️  GLM API错误 ({e.response.status_code})，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                        time.sleep(delay)
                    else:
                        raise Exception(f"GLM API调用失败（已重试{max_retries}次）: {str(e)}")
                else:
                    # 其他HTTP错误（如401认证失败），不重试
                    raise Exception(f"GLM API调用失败: {str(e)}")

            except requests.exceptions.RequestException as e:
                # 其他请求错误
                raise Exception(f"GLM API调用失败: {str(e)}")

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
        except json.JSONDecodeError as e1:
            # 尝试提取代码块中的JSON
            try:
                if '```json' in response:
                    json_str = response.split('```json')[1].split('```')[0].strip()
                    return json.loads(json_str)
                elif '```' in response:
                    json_str = response.split('```')[1].split('```')[0].strip()
                    return json.loads(json_str)
                else:
                    # 最后尝试：查找第一个{或[，提取到最后一个}或]
                    import re
                    json_match = re.search(r'[\{\[].*[\}\]]', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        return json.loads(json_str)
                    else:
                        raise ValueError("响应中未找到JSON格式内容")
            except (json.JSONDecodeError, IndexError, ValueError) as e2:
                # 所有解析尝试失败，返回错误信息
                error_msg = f"无法解析JSON响应。原始错误: {str(e1)}\n响应内容: {response[:500]}..."
                print(f"\n❌ JSON解析失败: {error_msg}")
                raise ValueError(error_msg)
