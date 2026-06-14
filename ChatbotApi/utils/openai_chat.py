import json
import logging
import os
import socket

import openai

logger = logging.getLogger(__name__)


def _load_api_keys():
    raw = os.getenv("OPENAI_API_KEYS", "[]")
    try:
        keys = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"OPENAI_API_KEYS is not valid JSON: {e}") from e
    if not isinstance(keys, list) or not keys:
        raise ValueError("OPENAI_API_KEYS must be a non-empty JSON array")
    return keys


api_keys = _load_api_keys()

class OpenaiChat():
    def __init__(self):
      self.key_index = 0
      self.api_keys = api_keys
      openai.api_key = api_keys[self.key_index]["key"]
      openai.api_base = api_keys[self.key_index]["host"]

      
    async def get_response_asnyc(self,messages, is_stream=True):
        max_retries = len(self.api_keys)  # 最大重试次数等于密钥的数量
        retries = 0  # 初始化重试计数器

        while retries < max_retries:  # 只要重试次数小于最大重试次数就继续
            print(self.api_keys[self.key_index]["host"])
            try:
                openai.api_key = self.api_keys[self.key_index]["key"]
                openai.api_base = self.api_keys[self.key_index]["host"]
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    stream=is_stream,
                    timeout=8  # 设置超时为10秒
                )
                return response
            except socket.error as e:  # 捕获 socket 异常
                print(f"Socket error: {str(e)}")
                return {"error": "Socket error occurred."}
            except Exception as e:  # 捕获超时异常和其他异常
                print('line:88' + str(e))
                self.key_index = (self.key_index + 1) % len(self.api_keys)
                retries += 1  # 增加重试计数器

        # 如果所有密钥都尝试失败，返回一个错误消息
        return {"error": "All API keys failed."}

    async def generate_response_stream(self, messages):
        response = await self.get_response_asnyc(messages)  # 获取响应，可能会在速率限制时重试

        # 检查是否返回了错误消息
        if isinstance(response, dict) and "error" in response:
            logger.error(response["error"])
            current_content = "[DONE]"
            yield 'data: %s\n\n' % current_content.replace("\n", "<br/>")
            return

        async for chunk in response:
            if not isinstance(chunk, dict):  # 检查 chunk 是否是字典
                logger.error(f"Unexpected chunk type: {type(chunk)}, value: {chunk}")
                continue  # 跳过这个 chunk

            if chunk['choices'][0]["finish_reason"] is not None:
                current_content = "[DONE]"
                yield 'data: %s\n\n' % current_content.replace("\n", "<br/>")
                return
            else:
                current_content = chunk['choices'][0]['delta'].get("content", "")
                logger.info(current_content)
            yield 'data: %s\n\n' % current_content.replace("\n", "<br/>")