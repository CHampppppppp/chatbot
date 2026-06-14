import json

from fastapi import Response


# 基础返回格式
def BaseResponse(msg, data=None, code=200, err=None, response: Response = None):
    content = {
        "data": data,
        "error": err,
        "msg": msg,
    }
    if not response:
        return content
    response.content = json.dumps(content)
    response.status_code = code

    return {"content": content, "status_code": code}
