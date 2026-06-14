# encoding: UTF-8
"""
讯飞星火图像生成工具类
"""

import base64
import hashlib
import hmac
import logging
import os
from fastapi import HTTPException, status
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema


def parse_url(request_url):
    """解析URL"""
    stidx = request_url.index("://")
    host = request_url[stidx + 3 :]
    schema = request_url[: stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + request_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


def assemble_ws_auth_url(request_url, method="GET", api_key="", api_secret=""):
    """生成鉴权url"""
    u = parse_url(request_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))

    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(
        host, date, method, path
    )
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")

    authorization_origin = (
        'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
        % (api_key, "hmac-sha256", "host date request-line", signature_sha)
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
        encoding="utf-8"
    )

    values = {"host": host, "date": date, "authorization": authorization}

    return request_url + "?" + urlencode(values)


def get_body(appid, text):
    """生成请求body体"""
    body = {
        "header": {
            "app_id": appid,
        },
        "parameter": {
            "chat": {
                "domain": "general",
                "width": 512,
                "height": 512,
                "temperature": 0.5,
                "max_tokens": 4096,
            }
        },
        "payload": {"message": {"text": [{"role": "user", "content": text}]}},
    }
    return body


class XunfeiImageGenerator:
    """讯飞星火图像生成器"""

    def __init__(self):
        self.app_id = os.getenv("XUNFEI_APP_ID")
        self.api_secret = os.getenv("XUNFEI_API_SECRET")
        self.api_key = os.getenv("XUNFEI_API_KEY")
        self.host = "http://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti"

        if not all([self.app_id, self.api_secret, self.api_key]):
            raise ValueError(
                "讯飞星火配置不完整，请检查环境变量 XUNFEI_APP_ID, XUNFEI_API_SECRET, XUNFEI_API_KEY"
            )

    def generate_image(self, prompt):
        """
        生成图像
        :param prompt: 图像生成的提示词
        :return: dict，包含生成状态和图像base64数据
        """
        try:
            if not prompt:
                return {"success": False, "error": "没有获取到提示词"}

            # 提示词合并角色提示词（系统）
            prompt = (
                "以下是图像生成的规则：1.不生成真人肖像或复杂版权内容 2.如果没有指定风格，则默认选择卡通风格或者水彩风格，根据以上规则生成以下图像："
                + prompt
            )

            # 生成鉴权URL
            url = assemble_ws_auth_url(
                self.host,
                method="POST",
                api_key=self.api_key,
                api_secret=self.api_secret,
            )

            # 生成请求体
            content = get_body(self.app_id, prompt)

            # 发起请求
            logger.info(f"[讯飞星火] 开始生成图像，提示词: {prompt}")
            response = requests.post(
                url,
                json=content,
                headers={"content-type": "application/json"},
                timeout=60,
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"请求失败，状态码: {response.status_code}",
                }

            # 解析响应
            data = response.json()
            code = data.get("header", {}).get("code")

            if code != 0:
                error_msg = data.get("header", {}).get("message", "未知错误")
                logger.error(f"[讯飞星火] 请求错误: {code}, {error_msg}")
                return {"success": False, "error": f"图像生成失败: {error_msg}"}

            # 提取图像数据
            text = data.get("payload", {}).get("choices", {}).get("text", [])
            if not text:
                return {"success": False, "error": "响应中没有图像数据"}

            image_content = text[0]
            image_base64 = image_content.get("content", "")

            if not image_base64:
                return {"success": False, "error": "未获取到图像base64数据"}

            logger.info("[讯飞星火] 图像生成成功")
            return {
                "success": True,
                "image_base64": image_base64,
                "task_id": data.get("header", {}).get("sid", ""),
            }

        except Exception as e:
            logger.exception(f"[讯飞星火] 图像生成错误: {str(e)}")
            return {"success": False, "error": f"图像生成异常: {str(e)}"}

    def handle_image(self, prompt, image_url=None):
        """
        处理图像生成请求,与AliChat的handle_image接口保持一致
        :param messages: 消息列表
        :param image_url: 图片URL(讯飞暂不支持图片编辑,此参数保留用于接口兼容)
        :return: 生成器,流式返回结果
        """
        try:
            # 从消息中提取用户的请求
            if not prompt:
                yield "data: 请提供图像生成的描述\n\n"
                yield "data: [DONE]\n\n"
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"msg": "图像生成失败", "error": "没有获取到提示词"},
                )

            logger.info(f"[讯飞星火] 调用图像生成,提示词: {prompt}")

            # 调用图像生成
            result = self.generate_image(prompt=prompt)

            if result.get("success"):
                # 将base64图像转换为data URL格式
                image_base64 = result.get("image_base64", "")
                data_url = self.base64_to_data_url(image_base64)
                yield f"data: ![Generated Image]({data_url})\n\n"
            else:
                yield f"data: 图像生成失败: {result.get('error', '未知错误')}\n\n"

        except Exception as e:
            logger.exception(f"[讯飞星火] 图像处理出错: {str(e)}")
            yield "data: 图像生成出错\n\n"

    def base64_to_data_url(self, base64_data):
        """将base64转换为data URL格式"""
        return f"data:image/png;base64,{base64_data}"
