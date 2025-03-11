import uuid
from typing import Dict, Optional
from fastapi import WebSocket
import asyncio
from config.settings import Settings

settings = Settings()

class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: Dict[str, WebSocket] = {}

        # 这个房间正在进行的剧情，应当从脚本加载
        self.game_stage: list = [
            "玩家进入洞穴，根据洞穴内的异常现象发现深处的宝箱",
            "宝箱是个陷阱，玩家落入了迷宫，迷宫内有很多探险者的尸体",
            "玩家发现迷宫的出口，但迷宫的建造者，邪恶的魔王在等着他们",
            "一般的攻击对魔王无效，玩家通过细心观察，发现魔王的弱点",
            "玩家抓住破绽击败魔王，魔王不甘地被击败了，玩家搜刮魔王的宝藏",
            "玩家意图返回，发现自己的位置离城镇很远",
            "玩家想方设法回到了城镇，成为了英雄"
        ]
        self.stage_cnt = len(self.game_stage) - 1
        
        self.game_state = {
            "story": [],
            "current_scene": "你站在一个神秘洞穴的入口，周围是茂密的森林。洞穴深处传来微弱的光芒和神秘的声音。",
            "current_stage": 0
        }

    async def connect(self, websocket: WebSocket) -> str:
        """添加新玩家到房间"""
        print("room.connect")
        if len(self.players) >= settings.max_players_per_room:
            raise ValueError("房间已满")
        
        player_id = str(uuid.uuid4())
        self.players[player_id] = websocket
        return player_id

    async def disconnect(self, player_id: str):
        """移除玩家"""
        if player_id in self.players:
            del self.players[player_id]

    async def broadcast(self, message: dict):
        """向房间内所有玩家广播消息"""
        for ws in self.players.values():
            await ws.send_json(message)

    def get_player_count(self) -> int:
        """获取当前房间玩家数量"""
        return len(self.players)

    def update_game_state(self, new_state: dict):
        """更新游戏状态"""
        self.game_state.update(new_state)

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.lock = asyncio.Lock()

    async def get_or_create_room(self) -> GameRoom:
        print("trying get or create room")
        """获取可用房间或创建新房间"""
        async with self.lock:
            # 查找未满的房间
            for room in self.rooms.values():
                print("room manager get avail room")
                if room.get_player_count() < settings.max_players_per_room:
                    return room
            
            # 如果没有可用房间，创建新房间
            room_id = str(uuid.uuid4())[:8]
            new_room = GameRoom(room_id)
            self.rooms[room_id] = new_room
            print("room manager created new room")
            return new_room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """获取指定房间"""
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str):
        """删除空房间"""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if room.get_player_count() == 0:
                del self.rooms[room_id]

# 全局房间管理器实例
room_manager = RoomManager()