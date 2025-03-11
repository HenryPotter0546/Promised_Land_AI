import os
import httpx
from fastapi import FastAPI
from config.settings import settings
import aiohttp
from config.settings import Settings

async def generate_ai_response(player_id: str, input_text: str, **kwargs):
    prompt = f"""作为文字冒险主持人，根据当前情境处理玩家输入：

    玩家ID：{player_id}
    输入指令：{input_text}
    
    生成要求：
    1. 保持叙事连贯性
    2. 用中文回复
    3. 限制在{kwargs.get('max_tokens', 200)}token内
    """
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "deepseek-chat",
                **kwargs
            }
        )
    
    if response.status_code != 200:
        return "神秘力量干扰了世界的运转..."
    
    result = response.json()
    return result['choices'][0]['message']['content']

settings = Settings()

class AIService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_base = settings.deepseek_api_base
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def generate_response(self, stage_hint: str, context: str, user_action: str) -> str:
        """生成AI响应"""
        # prompt = f"{settings.system_hint}\n\n当前场景：{context}\n\n玩家行动：{user_action}\n\nAI响应："
        print(stage_hint)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": settings.system_hint + stage_hint},
                        {"role": "assistant", "content": context},
                        {"role": "user", "content": user_action}
                        ],
                    "max_tokens": settings.ai_max_tokens,
                    "temperature": settings.ai_temperature
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"AI API调用失败: {error_text}")
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            

    def format_response(self, ai_response: str) -> dict:
        """格式化AI响应"""
        return {
            "type": "ai_response",
            "content": ai_response
        }

# 全局AI服务实例
ai_service = AIService()