from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    deepseek_api_key: str = 'your_deepeek_api_key'
    max_players_per_room: int = 4
    ai_max_tokens: int = 600
    ai_temperature: float = 0.7
    
    # DeepSeek API配置
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    
    # 游戏配置
    system_hint: str = """你现在是一个文字冒险游戏的AI主持人。你需要：
    1. 根据玩家的行动生成生动的描述和结果
    2. 维持游戏的连贯性和趣味性
    3. 确保每个响应都富有创意且引人入胜
    4. 适时提供选择和建议给玩家

    请用富有画面感的语言描述场景和结果，同时引导玩家推进剧情。"""
    
    # WebSocket配置
    ws_heartbeat_interval: int = 30  # 秒
    
    class Config:
        env_file = ".env"

settings = Settings()
