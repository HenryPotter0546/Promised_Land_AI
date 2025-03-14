import uuid
from typing import Dict, Optional, List
from fastapi import WebSocket
import asyncio
from config.settings import Settings
from services.map_service import map_service
from services.ai_service import ai_service

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
        
        # 房间全局游戏状态（作为默认值和模板）
        self.game_state = {
            "story": [],
            "init_scene": "你站在一个神秘洞穴的入口，周围是茂密的森林。洞穴深处传来微弱的光芒和神秘的声音。",
            "current_scene": "你站在一个神秘洞穴的入口，周围是茂密的森林。洞穴深处传来微弱的光芒和神秘的声音。",
            "current_stage": 0
        }
        
        # 每个玩家的独立游戏状态
        self.player_states: Dict[str, dict] = {}
        
        # 初始化房间的地图
        asyncio.create_task(self._initialize_maps())
    
    async def _initialize_maps(self):
        """初始化所有游戏阶段的地图"""
        print(f"开始为房间 {self.room_id} 生成地图...")
        # 为每个游戏阶段初始化地图
        for stage in range(len(self.game_stage)):
            # 获取阶段描述
            stage_description = self.game_stage[stage]
            
            # 构建提示
            prompt = f"""
你是一个文字冒险游戏的地图设计师。请根据以下游戏阶段描述，创建一个ASCII地图。
地图参考下面这份地图：

  北
  ↑
🌳[宿舍楼🏠]━主路━[食堂🍜]🌳
  ┃           ┃
  ┃      支路┅╋┅支路
  ┃           ┃
🗿[小路]    [小卖部🔴]
  ┃           ┃
  ┃━支路━━[实验室⚗️]━主路━▶出口
  ━━━━━小路━━━━━━━━┛

游戏阶段描述：{stage_description}

请注意：
1. 使用方括号[]表示地点
2. 使用═、║、╫等符号表示路径和连接
3. 使用🔴标记玩家当前位置
4. 地图应该反映游戏阶段的场景和环境
5. 只返回ASCII地图，不要有其他解释

ASCII地图：
"""
            
            # 调用AI服务生成地图
            try:
                generated_map = await ai_service.generate_response(f"生成游戏地图-阶段{stage}", stage_description, prompt)
                print(f"为阶段 {stage} 生成的地图: {generated_map}")
                
                # 清理生成的地图（移除可能的前缀和后缀）
                generated_map = self._clean_generated_map(generated_map)
                
                # 保存生成的地图
                map_service.update_map_for_stage(self.room_id, stage, generated_map)
                print(f"为阶段 {stage} 生成地图成功")
            except Exception as e:
                print(f"为阶段 {stage} 生成地图失败: {e}")
                # 创建一个简单的默认地图
                default_map = f"""
  北
  ↑
[入口]━━━━━[中心区域🔴]━━━━━[出口]
  │         │         │
  │         │         │
[左侧区域]━━[迷雾区域]━━[右侧区域]
  │         │         │
  │         │         │
[秘密通道]━━[宝藏室]━━━[休息处]
"""
                # 使用默认地图
                map_service.update_map_for_stage(self.room_id, stage, default_map)
                print(f"为阶段 {stage} 使用默认地图")
        
        print(f"房间 {self.room_id} 的所有地图初始化完成")
    
    def _clean_generated_map(self, map_text: str) -> str:
        """清理生成的地图文本，移除可能的前缀和后缀"""
        # 移除可能的"ASCII地图："前缀
        map_text = map_text.replace("ASCII地图：", "")
        
        # 移除可能的代码块标记
        map_text = map_text.replace("```", "")
        
        # 移除开头和结尾的空行
        map_text = map_text.strip()
        
        return map_text

    async def connect(self, websocket: WebSocket) -> str:
        """添加新玩家到房间"""
        print("room.connect")
        if len(self.players) >= settings.max_players_per_room:
            raise ValueError("房间已满")
        
        player_id = str(uuid.uuid4())
        self.players[player_id] = websocket
        
        # 初始化玩家独立游戏状态
        self.player_states[player_id] = {
            "story": [],
            "current_scene": self.game_state["init_scene"],
            "current_stage": 0,  # 新玩家总是从第一个阶段开始
            "joined_at_room_stage": self.game_state["current_stage"]  # 记录玩家加入时的房间阶段
        }
        
        return player_id

    async def disconnect(self, player_id: str):
        """移除玩家"""
        if player_id in self.players:
            del self.players[player_id]
            
            # 清理玩家状态
            if player_id in self.player_states:
                del self.player_states[player_id]

    async def broadcast(self, message: dict):
        """向房间内所有玩家广播消息"""
        for ws in self.players.values():
            await ws.send_json(message)

    def get_player_count(self) -> int:
        """获取当前房间玩家数量"""
        return len(self.players)

    def update_player_state(self, player_id: str, new_state: dict) -> bool:
        """更新玩家的游戏状态"""
        if player_id in self.player_states:
            self.player_states[player_id].update(new_state)
            return True
        return False
    
    def update_player_stage(self, player_id: str, stage: int) -> bool:
        """更新玩家的游戏阶段"""
        if player_id in self.player_states and 0 <= stage <= self.stage_cnt:
            self.player_states[player_id]["current_stage"] = stage
            return True
        return False
    
    def get_player_state(self, player_id: str) -> dict:
        """获取玩家的游戏状态"""
        return self.player_states.get(player_id, self.game_state.copy())
    
    def get_player_stage(self, player_id: str) -> int:
        """获取玩家的当前游戏阶段"""
        if player_id in self.player_states:
            return self.player_states[player_id]["current_stage"]
        return 0  # 默认返回第一个阶段
    
    def get_player_scene(self, player_id: str) -> str:
        """获取玩家的当前场景描述"""
        if player_id in self.player_states:
            return self.player_states[player_id]["current_scene"]
        return self.game_state["init_scene"]  # 默认返回初始场景

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.lock = asyncio.Lock()
        # 玩家ID到房间ID的映射，方便查找玩家所在的房间
        self.player_room_map: Dict[str, str] = {}

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
            print(f"创建新房间 {room_id}")
            return new_room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """获取指定房间"""
        return self.rooms.get(room_id)
    
    def get_player_room(self, player_id: str) -> Optional[GameRoom]:
        """获取玩家所在的房间"""
        room_id = self.player_room_map.get(player_id)
        if room_id:
            return self.get_room(room_id)
        return None

    def remove_room(self, room_id: str):
        """删除空房间"""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if room.get_player_count() == 0:
                # 清理玩家到房间的映射
                for player_id, mapped_room_id in list(self.player_room_map.items()):
                    if mapped_room_id == room_id:
                        del self.player_room_map[player_id]
                
                del self.rooms[room_id]
                print(f"删除空房间 {room_id}")
    
    async def join_room(self, room_id: str, websocket: WebSocket) -> tuple:
        """加入指定房间"""
        room = self.get_room(room_id)
        if not room:
            raise ValueError(f"房间 {room_id} 不存在")
        
        player_id = await room.connect(websocket)
        self.player_room_map[player_id] = room_id
        
        return room, player_id
    
    async def leave_room(self, player_id: str):
        """离开房间"""
        room = self.get_player_room(player_id)
        if room:
            await room.disconnect(player_id)
            
            # 如果房间空了，删除房间
            if room.get_player_count() == 0:
                self.remove_room(room.room_id)
            
            # 清理玩家到房间的映射
            if player_id in self.player_room_map:
                del self.player_room_map[player_id]

# 全局房间管理器实例
room_manager = RoomManager()