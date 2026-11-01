import requests
import json

class LLMClient:
    def __init__(self, api_key=None, model="mimo-v2.5-pro"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.mimo.one/v1"

    def chat(self, messages, stream=False):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        resp = requests.post(f"{self.base_url}/chat/completions",
                           json=payload, headers=headers)
        return resp.json()

    def analyze_deep(self, context, question):
        messages = [
            {"role": "system", "content": "你是精通命理学的AI助手，基于真实数据进行科学分析。"},
            {"role": "user", "content": f"背景: {context}\n问题: {question}"}
        ]
        return self.chat(messages)
