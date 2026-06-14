import asyncio
import base64
import json
import logging
import mimetypes
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor

import dashscope
import requests
from dashscope import Application, Generation
from dotenv import load_dotenv
from fastapi import HTTPException, status

# 讯飞星火图像生成
from utils.xunfei_image import XunfeiImageGenerator

# 创建线程池用于执行异步函数
_thread_pool = ThreadPoolExecutor(max_workers=5)

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 定义图像生成和编辑工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "当用户要求生成图像、画图、创建图片或者描述想要的视觉内容时，使用此工具根据文本描述生成图像。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "用于生成图像的详细文本描述，应该包含场景、风格、颜色等具体信息。",
                    }
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "image_edit_by_fetch",
            "description": "当用户要求对图片进行风格化、编辑、去水印、扩图、上色等图像编辑操作时，使用此工具。你应该总是假设用户已经提供了图片并开始操作。function 字段支持 stylization_all(全局风格化)、stylization_local(局部风格化)、description_edit(指令编辑)、remove_watermark(去除水印)、expand(图像扩展)、super_resolution(超分辨率)、colorization(图像上色)、doodle(线稿生图)、control_cartoon_feature(参考卡通形象生图)。根据用户意图选择合适的function。全局风格话提示词推荐写为“转换成xx风格”，例如“转换成法国绘本风格”或“转换成金箔艺术风格”。局部风格化提示词推荐写为“把xx变成xx风格”。指令编辑提示词推荐显式写明“添加”、“修改”这类操作描述。去除水印提示词推荐写为“去除图像中的文字”或者描述要去除的文字类型，比如“去除英文文字”。图像扩展提示词要求描述扩图后的图片内容。图像超分提示词推荐写为“图像超分”或描述超分后的图片。图像上色在提示词中可指定颜色（如“蓝色背景，黄色叶子”）。若未指定颜色，自动选择适合的颜色。参考卡通形象生图提示词需详细描述卡通形象的行动，建议采用格式“卡通形象……”，描述越具体，生成效果越好。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图像编辑的提示词，如全局风格话提示词推荐写为“转换成xx风格”，例如“转换成法国绘本风格”或“转换成金箔艺术风格”。局部风格化提示词推荐写为“把xx变成xx风格”。指令编辑提示词推荐显式写明“添加”、“修改”这类操作描述。去除水印提示词推荐写为“去除图像中的文字”或者描述要去除的文字类型，比如“去除英文文字”。图像扩展提示词要求描述扩图后的图片内容。图像超分提示词推荐写为“图像超分”或描述超分后的图片。图像上色在提示词中可指定颜色（如“蓝色背景，黄色叶子”）。若未指定颜色，自动选择适合的颜色。参考卡通形象生图提示词需详细描述卡通形象的行动，建议采用格式“卡通形象……”，描述越具体，生成效果越好。",
                    },
                    "function": {
                        "type": "string",
                        "description": "图像编辑功能类型，要求转换图片风格则使用stylization_all，要求把图中部分元素风格转换则使用stylization_local、要求对图片编辑修改则使用description_edit、要求移除图片中的水印则使用remove_watermark、要求扩展图像则使用expand、要求超分辨率则使用super_resolution、要求对图片进行上色则使用colorization、要求线稿生图则使用doodle、要求参考卡通形象生图则使用control_cartoon_feature。根据用户意图选择合适的function。",
                    },
                },
                "required": ["prompt", "function"],
            },
        },
    },
]

# RAG角色提示词
rolePrompts = {
    "chat": """
    # 角色
    你是一位聪明又友好的校园电子板报制作小帮手，名叫“校园精灵”，专门帮助小学生轻松学习和创作。

    ## 技能
    ### 技能1：指导板报制作
    - **任务**：当用户提问时，按步骤简单指导，提供所有相关步骤，分步教。

    ## 限制
    - 只聊学习和板报制作相关，如果是电脑操作相关的问题，推荐用户使用“电脑博士”智能体，拒绝其他话题。
    - 每条回复少于100字。
    - 如果你是第一次使用这个身份与用户交互，先介绍你自己，再追加回答。

    ## 交互规则
    - **风格控制**：
    1. 多问启发问题，像朋友聊天。
    2. 用简单词，避免难懂术语。
    3. 重点提示前换行并加★。
    4. 语言清晰明了，符合小学生阅读水平。
    """,
    "computerDoctor": """
    # 角色
    你是一位耐心且专业的电脑小老师，名叫“电脑博士”。你擅长帮助小学生解决电脑问题，特别是在使用Word和PPT制作板报方面。你能够用简单易懂的语言指导学生，像讲故事一样传授知识。

    ## 技能
    ### 技能1: Word/PPT等电脑软件操作全过程指导
    - **任务**：基于用户的需求，提供详细的Word和PPT板报制作步骤。

    ### 技能2: 排版、动画、图文简单技巧
    - **任务**：教授用户如何进行基本的排版、添加动画效果以及插入和编辑图片等操作。

    ### 技能3: 用大白话教，像讲故事
    - **任务**：以故事的形式讲解复杂的电脑操作，使学生更容易理解和记忆。
 
    ## 限制
    - 只回答与学习和电脑操作相关的问题，如果是板报制作相关的问题，推荐用户使用“校园精灵”智能体，拒绝其他类型的问题。
    - 每条回复不超过100字。
    - 如果你是第一次使用这个身份与用户交互，先介绍你自己再追加回答。

    ## 交互规则
    - **风格控制**：
    1. 按步骤简单指导，提供所有相关步骤，分步教。
    2. 重点提示前换行并加★。
    3. 用日常语言，避免使用专业术语。
    4. 语言清晰明了，符合小学生阅读水平。
    - **如果知识库匹配结果不为空**：
    1. 根据知识库搜寻结果内的操作步骤，教授用户。
    2. 如果有多个方法，分为多个点教授用户
    """,
}


def _run_async_in_thread(coro):
    """
    在独立线程中运行异步函数，避免事件循环冲突

    Args:
        coro: 协程对象

    Returns:
        协程的返回值
    """

    def _run():
        # 在新线程中创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    future = _thread_pool.submit(_run)
    return future.result()


class AliChat:
    def __init__(self):
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

    def get_rag_response_asnyc(self, messages, role):
        try:
            if len(messages) == 0:
                raise ValueError("消息列表不能为空")
            if messages[-1]["role"] != "user":
                # 只有当messages为空或最后一条消息的角色不是"user"时，才执行添加操作
                messages.append(
                    {
                        "role": "user",
                        "content": "请根据上述内容进行精简的回复，尽量控制在100字以内",
                    }
                )
            responses = Application.call(
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                app_id=os.getenv("DASHSCOPE_APP_ID"),
                messages=messages,
                biz_params={"user_prompt_params": {"rolePrompt": rolePrompts[role]}},
                flow_stream_mode="agent_format",
                stream=True,
                incremental_output=True,
            )

            return responses
        except Exception as e:
            print(f"RAG对话生成失败: {str(e)}")
            return {"error": "生成对话失败。"}

    def get_response_asnyc(self, messages, is_stream=True):
        try:
            if messages[-1]["role"] != "user":
                # 只有当messages为空或最后一条消息的角色不是"user"时，才执行添加操作
                messages.append(
                    {
                        "role": "user",
                        "content": "请根据上述内容进行精简的回复，尽量控制在100字以内",
                    }
                )
            if is_stream:
                responses = Generation.call(
                    api_key=dashscope.api_key,
                    model=Generation.Models.qwen_turbo,
                    messages=messages,
                    result_format="message",  # 设置结果格式为"message"
                    stream=is_stream,
                    enable_thinking=True,
                    incremental_output=True,  # 以流式方式逐步获取输出
                )
            else:
                responses = Generation.call(
                    api_key=dashscope.api_key,
                    model=Generation.Models.qwen_turbo,
                    messages=messages,
                    result_format="message",  # 设置结果格式为"message"
                    stream=is_stream,
                    # 不包含incremental_output字段
                )
            return responses
        except Exception as e:  # 捕获超时异常和其他异常
            print(f"Unexpected error: {str(e)}")
            return {"error": "All API keys failed."}

    def generate_response_stream(self, message, rag=False, role="chat"):
        response = (
            self.get_response_asnyc(message, is_stream=True)
            if not rag
            else self.get_rag_response_asnyc(message, role)
        )

        # 错误处理
        if isinstance(response, dict) and response.get("error"):
            yield "data: %s\n\n" % "啊哦，我有点处理不过来了，请等会儿再问我试试看！"

        else:
            for chunk in response:
                # 检查 chunk 是否为字典，且 chunk 中有 output 属性，以及 output 中有 choices 属性或者 text 属性
                if (
                    not isinstance(chunk, dict)
                    or "output" not in chunk
                    or not chunk["output"]
                    or (
                        "choices" not in chunk["output"]
                        and "text" not in chunk["output"]
                    )
                    or (
                        not chunk["output"].get("choices", None)
                        and not chunk["output"].get("text", None)
                    )
                ):
                    print(f"Unexpected or incomplete chunk: {chunk}")
                    continue  # 跳过不合规范的 chunk
                # 获取当前内容
                current_content = (
                    chunk["output"]["choices"][0]["message"]["content"]
                    if chunk["output"].get("choices")
                    else chunk["output"].get("text", "")
                )

                # 如果有内容就输出
                if current_content and current_content.strip():
                    yield "data: %s\n\n" % current_content.replace("\n", "<br/>")

        yield "data: [DONE]\n\n"
        return

    def generate_image(self, prompt):
        """
        使用 HTTP 方式调用 DashScope 图像生成接口，返回流式结果。
        :parms: prompt: str, 图像生成的提示词。
        """
        try:
            # 获取 prompt
            if not prompt:
                return {"success": False, "error": "没有获取到提示词"}

            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                return {"success": False, "error": "API_KEY 未设置"}

            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
            headers = {
                "X-DashScope-Async": "enable",
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "wan2.2-t2i-flash",
                "input": {"prompt": prompt},
                "parameters": {"n": 2, "size": "1024*1024"},
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
            except Exception as e:
                return {"success": False, "error": str(e)}

            if response.status_code == 200:
                data = response.json()
                # 兼容不同返回结构
                task_id = data.get("output", {}).get("task_id")
                if not task_id or not isinstance(task_id, str):
                    print(
                        f"图像生成任务未返回有效的 task_id, code: {data.get('code')}, message: {data.get('message')}"
                    )
                    return {
                        "success": False,
                        "error": "图像生成任务未返回有效的 task_id",
                    }
                else:
                    print(f"图像生成任务已创建，任务ID: {task_id}")
                    for i in range(10):
                        fetch_result_url = (
                            f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
                        )
                        fetch_result_headers = {"Authorization": f"Bearer {api_key}"}
                        try:
                            rsp = requests.get(
                                fetch_result_url,
                                headers=fetch_result_headers,
                                timeout=60,
                            ).json()
                        except Exception as e:
                            return {
                                "success": False,
                                "error": f"查询图像生成结果错误: {str(e)}",
                            }
                        if rsp.get("output", {}).get("task_status") == "SUCCEEDED":
                            results = rsp.get("output", {}).get("results", [])
                            print(f"图像生成任务完成, results: {results}")
                            urls = [
                                result.get("url")
                                for result in results
                                if result.get("url")
                            ]
                            if urls:
                                return {"success": True, "urls": urls}
                            else:
                                return {
                                    "success": False,
                                    "error": "未找到生成的图像URL",
                                }
                        else:
                            print(
                                f"任务生成状态: {rsp.get('output').get('task_status')}"
                            )
                            if rsp.get("output").get("task_status") == "FAILED":
                                return {"success": False, "error": "图像生成任务失败"}
                            time.sleep(3)
            else:
                try:
                    err = response.json()
                    print(
                        f"图像生成失败，code: {err.get('code')}, 错误信息: {err.get('message')}"
                    )
                except Exception:
                    err = response.text
                return {"success": False, "error": err.get("message")}
        except Exception as e:
            print(f"图像生成错误: {str(e)}")
            return {"success": False, "error": "图像生成错误"}

    def image_edit_by_fetch(
        self,
        prompt,
        base_image_url,
        function="description_edit",
        max_retry=10,
        wait_seconds=3,
    ):
        """
        使用DashScope异步API进行图像风格化编辑，自动轮询任务状态，返回最终结果。
        :param prompt: 图像风格化描述
        :param function: 图像编辑功能(
            stylization_all:全局风格化，当前支持2种风格(法国绘本风格 金箔艺术风格)。
            stylization_local:局部风格化，当前支持8种风格(
                冰雕:ice
                云朵:cloud
                花灯:chinese festive lantern
                木板:wooden
                青花瓷:blue and white porcelain
                毛茸茸:fluffy
                毛线:weaving
                气球:balloon
            )。
            description_edit:指令编辑。通过指令即可编辑图像，简单编辑任务优先推荐这种方式。
            remove_watermark:去文字水印。
            expand:扩图。
            super_resolution:图像超分。
            colorization:图像上色。
            doodle:线稿生图。
            control_cartoon_feature:参考卡通形象生图。
        )
        :param base_image_url: 原始图片URL
        :param api_key: 可选，DashScope API Key
        :param max_retry: 最大轮询次数
        :param wait_seconds: 每次轮询间隔秒数
        :return: dict，包含任务状态和结果
        """

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {"success": False, "error": "DASHSCOPE_API_KEY 未设置"}

        # 判断base_image_url是否为本地文件路径（不是http/https开头）
        if base_image_url:
            print(f"读取的本地文件路径: {base_image_url}")
            # 读取本地图片并转为base64
            try:
                with open(base_image_url, "rb") as f:
                    img_bytes = f.read()
                mime_type, _ = mimetypes.guess_type(base_image_url)
                if not mime_type:
                    mime_type = "image/png"  # 默认png
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                base_image_url = f"data:{mime_type};base64,{img_b64}"
            except Exception as e:
                return {"success": False, "error": f"本地图片转base64失败: {str(e)}"}

        headers_create_task = {
            "X-DashScope-Async": "enable",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "wanx2.1-imageedit",
            "input": {
                "function": function,
                "prompt": prompt,
                "base_image_url": base_image_url,
            },
            "parameters": {"n": 1},
        }
        print(
            f"图像编辑API请求参数: {payload.get('input').get('prompt')},{payload.get('input').get('function')}\n"
        )
        try:
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis",
                headers=headers_create_task,
                json=payload,
            )
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("output", {}).get("task_id") or data.get("id")
                if not task_id:
                    return {"success": False, "error": "未返回任务ID", "raw": data}
            else:
                return {
                    "success": False,
                    "error": f"创建任务失败: {response.text}",
                }
        except Exception as e:
            print(f"创建任务异常: {str(e)}")
            return {"success": False, "error": "创建图像编辑请求异常"}

        # 轮询查询任务状态
        headers_query_task = {
            "Authorization": f"Bearer {api_key}",
        }
        for i in range(max_retry):
            try:
                resp = requests.get(
                    f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
                    headers=headers_query_task,
                )
                if resp.status_code == 200:
                    print(f"查询任务状态成功: {resp.json()}")
                else:
                    print(
                        f"查询任务失败，状态码: {resp.status_code}, 内容: {resp.text}"
                    )
                    return {
                        "success": False,
                        "error": "网络异常",
                        "content": resp.text,
                    }
            except Exception as e:
                print(f"查询任务请求异常: {str(e)}")
                return {"success": False, "error": "任务中断"}

            # 任务完成，返回结果
            if resp.json().get("output", {}).get("task_status") == "SUCCEEDED":
                return {
                    "success": True,
                    "urls": [
                        result.get("url")
                        for result in resp.json().get("output", {}).get("results", [])
                        if result.get("url")
                    ],
                }
            else:
                time.sleep(wait_seconds)

        # 超时未完成
        return {"done": True}

    def handle_image(self, messages, image_url=None, user_id=None, db=None):
        """
        处理图像相关请求（生成和编辑）

        Args:
            messages: 消息列表
            image_url: 图片URL（用于编辑）
            user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段，用于配额扣除）
            db: 数据库会话（用于记录日志）
        """
        try:
            # 检查 API 密钥是否设置
            if not dashscope.api_key:
                return {"error": "DASHSCOPE_API_KEY 环境变量未设置"}

            responses = Generation.call(
                api_key=dashscope.api_key,
                model=Generation.Models.qwen_max,
                messages=messages,
                result_format="message",  # 设置结果格式为"message"
                tools=tools,
            )
            print(f"通义千问响应: {responses}")

            # 检查 API 响应状态
            if hasattr(responses, "status_code") and responses.status_code != 200:
                error_msg = f"API 调用失败: {responses.get('message', '未知错误')}"
                if responses.get("code") == "AccessDenied":
                    error_msg = (
                        "访问被拒绝，请检查 API 密钥是否有效或是否有图像生成权限"
                    )
                print(f"通义千问API调用失败: {error_msg}")
                yield "data: 智能体异常，请稍后重试\n\n"
                return

            response_content = responses.output.choices[0].message
            tool_call = None

            # 安全地检查 tool_calls 是否存在（response_content 是字典）
            if (
                isinstance(response_content, dict)
                and "tool_calls" in response_content
                and response_content["tool_calls"]
            ):
                tool_call = response_content["tool_calls"][0]
                print(f"工具调用 tool_call: {tool_call}")

            # 处理 generate_image 工具调用
            if (
                tool_call
                and tool_call.get("function", {}).get("name") == "generate_image"
            ):
                # 使用讯飞星火图像生成
                arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                xunfei_image = XunfeiImageGenerator()
                try:
                    arguments = json.loads(arguments_str)
                    image_prompt = arguments.get("prompt", "")
                    yield f"data: 正在为你生成图像：{image_prompt}\n\n"
                    logging.info(f"调用图像生成,入参: {image_prompt}")
                    yield from xunfei_image.handle_image(prompt=image_prompt)

                    # 🔥 生成成功后扣除配额
                    if user_id and db:
                        try:
                            from main import redis_client
                            from utils.image_quota_manager import (
                                ImageQuotaManager,
                                ImageServiceType,
                            )

                            if redis_client:
                                quota_manager = ImageQuotaManager(redis_client)

                                # 使用同步方法扣除配额（避免事件循环冲突）
                                quota_manager.consume_quota_sync(
                                    user_id=user_id,
                                    service_type=ImageServiceType.GENERATE,
                                    db=db,
                                    prompt=image_prompt,
                                    status="success",
                                )
                        except Exception as quota_error:
                            logger.error(f"扣除生成配额失败: {str(quota_error)}")
                            # 配额扣除失败不影响图像返回

                except HTTPException:
                    raise
                except json.JSONDecodeError:
                    image_prompt = ""
                    logger.error(f"图像生成提示词解析错误, 入参: {arguments_str}")
                except Exception as e:
                    logger.error(f"图像生成异常: {str(e)}")
                    yield f"data: 图像生成异常: {str(e)}\n\n"

                # arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                # try:
                #     arguments = json.loads(arguments_str)
                #     image_prompt = arguments.get("prompt", "")
                #     yield f"data: 正在为你生成图像：{image_prompt}\n\n"
                #     print(f"调用图像生成,入参: {arguments}")
                #     result = self.generate_image(prompt=image_prompt)
                #     if result.get("success"):
                #         for url in result.get("urls", []):
                #             yield f"data: ![Generated Image]({url})\n\n"
                #     else:
                #         yield f"data: 图像生成失败: {result.get('error', '未知错误')}\n\n"
                # except json.JSONDecodeError:
                #     image_prompt = ""
                #     print(f"图像生成提示词解析错误, 入参: {arguments_str}")

            # 只有当提供了image_url时才处理图像编辑工具调用
            elif (
                tool_call
                and tool_call.get("function", {}).get("name") == "image_edit_by_fetch"
            ):
                if not image_url:
                    yield f"data: {random.choice(['你还没有提供图片呢!', '请先上传图片!', '你是不是忘记给我图片啦？'])}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                try:
                    arguments = json.loads(arguments_str)
                    function_type = arguments.get("function", "")
                    image_edit_prompt = arguments.get("prompt", "")
                    yield f"data: 正在为你编辑图像：{image_edit_prompt}\n\n"
                    if arguments:
                        try:
                            result = self.image_edit_by_fetch(
                                function=function_type,
                                prompt=image_edit_prompt,
                                base_image_url=image_url,
                            )
                            if result.get("success"):
                                for url in result.get("urls", []):
                                    yield f"data: ![Generated Image]({url})\n\n"

                                # 🔥 编辑成功后扣除配额
                                if user_id and db:
                                    try:
                                        from main import redis_client
                                        from utils.image_quota_manager import (
                                            ImageQuotaManager,
                                            ImageServiceType,
                                        )

                                        if redis_client:
                                            quota_manager = ImageQuotaManager(
                                                redis_client
                                            )

                                            # 使用同步方法扣除配额（避免事件循环冲突）
                                            quota_manager.consume_quota_sync(
                                                user_id=user_id,
                                                service_type=ImageServiceType.EDIT,
                                                db=db,
                                                prompt=image_edit_prompt,
                                                status="success",
                                            )
                                    except Exception as quota_error:
                                        logger.error(
                                            f"扣除编辑配额失败: {str(quota_error)}"
                                        )
                                        # 配额扣除失败不影响图像返回

                            elif result.get("done"):
                                yield "data: 图像编辑任务超时未完成。\n\n"
                            else:
                                yield f"data: 图像编辑失败: {result.get('error', '未知错误')}\n\n"
                        except Exception as e:
                            yield f"data: 图像编辑错误: {str(e)}\n\n"
                    else:
                        yield "data: 没有提供图像编辑的提示、图片URL或功能类型。\n\n"
                except json.JSONDecodeError:
                    print("图像编辑入参解析错误")
            else:
                # 如果没有调用工具或调用了其他工具，返回普通的文本响应
                print(f"普通文本响应: {response_content}")
                if response_content and response_content.get("content"):
                    yield "data: %s\n\n" % response_content.get("content").replace(
                        " ", ""
                    ).replace("\t", "").replace("\n", "<br/>")
                else:
                    print("No valid response content found in response.")
                    yield "data: 响应格式错误"
        except Exception as e:
            print(f"图像生成出错: {str(e)}")
            yield "data: 图像生成出错\n\n"
        yield "data: [DONE]\n\n"

    def image_input(self, messages):
        if not dashscope.api_key:
            raise HTTPException(status_code=500, detail="模型API_KEY未设置")
        logging.debug(f"通义千问图像输入入参: {messages}\n")
        try:
            try:
                responses = dashscope.MultiModalConversation.call(
                    model="qwen3-vl-plus",
                    messages=messages,
                    stream=True,
                    incremental_output=True,
                )
                for chunk in responses:
                    # 检查chunk是否为字典类型
                    if isinstance(chunk, dict):
                        if chunk.get("status_code") == 200:
                            try:
                                if (
                                    chunk.get("output", {}).get("finish_reason")
                                    == "stop"
                                    or chunk.get("output", {})
                                    .get("choices")[0]
                                    .get("finish_reason")
                                    == "stop"
                                ):
                                    yield "data: [DONE]\n\n"
                                    return
                                if chunk.get("output", {}).get("choices"):
                                    yield "data: %s\n\n" % chunk["output"]["choices"][
                                        0
                                    ]["message"]["content"][0]["text"].replace(
                                        "\n", "<br/>"
                                    )
                            except Exception as inner_e:
                                print(f"[DEBUG]chunk异常: {str(inner_e)}\n{chunk}")
                                raise
                        else:
                            print(f"[DEBUG]通义千问图像输入失败: {chunk}\n")
                            raise HTTPException(
                                status_code=chunk.status_code,
                                detail={
                                    "msg": "作品评分失败",
                                    "error": chunk.get("message", "未知错误"),
                                },
                            )
                    else:
                        # 处理非字典类型的chunk
                        try:
                            # 尝试安全地将chunk转换为字符串
                            chunk_str = str(chunk)
                            if "error" in chunk_str.lower():
                                print(f"[DEBUG]chunk中包含错误信息: {chunk_str}")
                                yield f"data: 处理图像输入时出错: {chunk_str}\n\n"
                        except Exception as str_e:
                            print(f"[DEBUG]将chunk转换为字符串时出错: {str(str_e)}")
                            yield "data: 处理图像输入时出错: 无法处理响应格式\n\n"
                            raise
            except Exception:
                raise
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"作品评分出错: {str(e)}"
            print(f"[DEBUG]{error_msg}")
            yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"msg": "作品评分失败", "error": error_msg},
            )
