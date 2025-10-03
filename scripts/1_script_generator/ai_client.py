"""
AI客户端封装
支持多种AI服务提供商（OpenAI, Anthropic等）
"""

import json
import os
import time
import re
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

        # 重试机制：最多3次，指数退避（针对GLM限流优化延迟时间）
        max_retries = 3
        retry_delays = [3, 6, 12]  # 秒（比OpenAI更长，应对429限流）

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
                        # 429限流需要更长的等待时间
                        if e.response.status_code == 429:
                            delay = retry_delays[attempt] * 2  # 429双倍等待
                            print(f"\n⚠️  GLM API限流(429)，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                        else:
                            delay = retry_delays[attempt]
                            # 尝试获取错误详情
                            try:
                                error_detail = e.response.json()
                                print(f"\n⚠️  GLM API错误 ({e.response.status_code})，详情: {error_detail.get('error', {}).get('message', 'N/A')}")
                            except:
                                print(f"\n⚠️  GLM API错误 ({e.response.status_code})，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                        time.sleep(delay)
                    else:
                        # 最后一次失败，提供详细错误信息
                        try:
                            error_detail = e.response.json()
                            error_msg = error_detail.get('error', {}).get('message', str(e))
                        except:
                            error_msg = str(e)
                        raise Exception(f"GLM API调用失败（已重试{max_retries}次，状态码{e.response.status_code}）: {error_msg}")
                else:
                    # 其他HTTP错误（如401认证失败），不重试
                    try:
                        error_detail = e.response.json()
                        error_msg = error_detail.get('error', {}).get('message', str(e))
                    except:
                        error_msg = str(e)
                    raise Exception(f"GLM API调用失败（状态码{e.response.status_code}）: {error_msg}")

            except requests.exceptions.RequestException as e:
                # 其他请求错误
                raise Exception(f"GLM API调用失败: {str(e)}")

    def _clean_response(self, response: str) -> str:
        """
        清理AI响应中的干扰内容

        Args:
            response: 原始响应

        Returns:
            清理后的响应
        """
        # 去除BOM和零宽字符
        response = response.replace('\ufeff', '').replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')

        # 清理常见的AI说明文字模式（中英文）
        patterns_to_remove = [
            r'^好的[,，。\s]*',
            r'^明白[了]?[,，。\s]*',
            r'^以下是[^：:]*[:：\s]*',
            r'^这是[^：:]*[:：\s]*',
            r'^为您生成[^：:]*[:：\s]*',
            r'^根据您的要求[^：:]*[:：\s]*',
            r'以上[是就].*$',
            r'^Here is.*[:：\s]*',
            r'^Sure.*[:：\s]*',
            r'^Okay.*[:：\s]*',
        ]

        for pattern in patterns_to_remove:
            response = re.sub(pattern, '', response, flags=re.MULTILINE | re.IGNORECASE)

        return response.strip()

    def _extract_json_string(self, response: str) -> Optional[str]:
        """
        从响应中提取JSON字符串

        Args:
            response: 清理后的响应

        Returns:
            提取的JSON字符串，如果未找到则返回None
        """
        import re

        # 方法1: 提取```json代码块
        if '```json' in response:
            match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()

        # 方法2: 提取普通```代码块
        if '```' in response:
            match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()

        # 方法3: 提取完整的JSON对象（从第一个{到匹配的}）
        json_obj_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', response, re.DOTALL)
        if json_obj_match:
            return json_obj_match.group(0)

        # 方法4: 提取完整的JSON数组（从第一个[到匹配的]）
        json_arr_match = re.search(r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]', response, re.DOTALL)
        if json_arr_match:
            return json_arr_match.group(0)

        return None

    def _fix_json_string(self, json_str: str) -> str:
        """
        尝试修复常见的JSON格式问题

        Args:
            json_str: JSON字符串

        Returns:
            修复后的JSON字符串
        """
        import re

        # 修复1: 移除注释（单行和多行）
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

        # 修复2: 将单引号替换为双引号（但要避免字符串内的单引号）
        # 简化版本：直接替换（可能不完美，但适用于大多数情况）
        # json_str = json_str.replace("'", '"')

        # 修复3: 移除多余的逗号（如数组或对象最后一个元素后的逗号）
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        return json_str

    def _save_debug_response(self, response: str, error: str) -> str:
        """
        保存失败的响应到调试文件

        Args:
            response: 失败的响应内容
            error: 错误信息

        Returns:
            调试文件路径
        """
        debug_dir = 'debug'
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = time.strftime('%Y%m%d_%H%M%S')
        debug_file = os.path.join(debug_dir, f'failed_json_{timestamp}.txt')

        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(f"=== 错误信息 ===\n{error}\n\n")
            f.write(f"=== AI完整响应 ===\n{response}\n")

        return debug_file

    def _try_parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """
        尝试解析JSON（包含清理、提取、修复）

        Args:
            response: AI响应

        Returns:
            解析成功的JSON字典，失败返回None
        """
        # 步骤1: 清理响应
        cleaned = self._clean_response(response)

        # 步骤2: 尝试直接解析
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 步骤3: 提取JSON字符串
        json_str = self._extract_json_string(cleaned)
        if not json_str:
            return None

        # 步骤4: 尝试解析提取的JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 步骤5: 修复并再次尝试解析
        try:
            fixed_json = self._fix_json_string(json_str)
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            return None

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        生成JSON格式的内容（带重试机制）

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）

        Returns:
            解析后的JSON字典
        """
        import re

        # 第一次尝试：正常生成
        response = self.generate(prompt, system_prompt)
        parsed = self._try_parse_json(response)
        if parsed:
            return parsed

        # 第一次重试：请求AI修正格式
        print("⚠️  JSON格式有误，请求AI修正...")
        fix_prompt = f"请将以下内容修正为标准JSON格式，只返回纯JSON，不要任何说明文字、前言或后缀：\n\n{response}"
        response_fixed = self.generate(fix_prompt)
        parsed = self._try_parse_json(response_fixed)
        if parsed:
            print("✅ AI修正成功")
            return parsed

        # 第二次重试：更严格的指令
        print("⚠️  再次尝试修正...")
        strict_prompt = f"严格要求：只返回纯JSON格式数据，确保使用双引号、无注释、无多余逗号。修正此内容：\n\n{response}"
        response_strict = self.generate(strict_prompt)
        parsed = self._try_parse_json(response_strict)
        if parsed:
            print("✅ AI严格修正成功")
            return parsed

        # 所有重试失败，保存调试信息并抛出异常
        error_msg = "JSON解析失败（已重试2次AI修正）"
        debug_file = self._save_debug_response(response_strict, error_msg)

        final_error = f"{error_msg}\n调试文件已保存: {debug_file}\n响应预览: {response_strict[:300]}..."
        print(f"\n❌ {final_error}")
        raise ValueError(final_error)
