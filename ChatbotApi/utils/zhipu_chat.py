import os

import zhipuai

class ZhipuChat():
    def __init__(self):
        self.api_key = os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY is not configured")
        zhipuai.api_key = self.api_key

    def get_response_async(self,messages, is_stream=True):
        try:
            # messages.append({"role": "user", "content": "请根据上述内容回复"})
            response = zhipuai.model_api.sse_invoke(
                model="chatglm_turbo",
                prompt=messages,
                top_p=0.7,
                temperature=0.9,
            )
        
            return response
        except Exception as e:  # 捕获超时异常和其他异常
            return {"error": "All API keys failed."}

    def generate_response_stream(self, messages):
        print("开始处理 generate_response_stream")
        response = self.get_response_async(messages)
        print("已获取响应")

        try:
            for event in response.events():
                print(f"处理事件: {event.event}")
                if event.event == "add":
                    print(f"添加事件数据: {event.data}")
                    current_content = event.data
                elif event.event == "error" or event.event == "interrupted":
                    print(f"错误或中断事件: {event.data}")
                    continue
                elif event.event == "finish":
                    current_content = "[DONE]"
                    print(f"完成事件，当前内容: {current_content}")
                    yield 'data: %s\n\n' % current_content.replace("\n", "<br/>")
                    return
                else:
                    print(f"其他事件: {event.data}")
                    current_content = event.data

                yield f'data: %s\n\n' % current_content.replace("\n", "<br/>")
        except Exception as e:
            print(f"发生异常: {e}")

       