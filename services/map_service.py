from typing import Dict, List, Optional
import re
import random

class MapService:
    def __init__(self):
        # 存储每个房间的地图
        self.room_maps: Dict[str, Dict[int, str]] = {}
        # 玩家位置标记
        self.player_positions: Dict[str, Dict[str, Dict[str, int]]] = {}
        # 默认迷雾地图
        self.default_map = self._generate_fog_map()
    
    def _generate_fog_map(self) -> str:
        """生成一个特殊标记，前端可以用它来渲染逼真的流动迷雾效果"""
        # 返回一个特殊的标记，前端会将其识别为动态迷雾效果
        return "FOG_MAP_DYNAMIC_MARKER"
    
    def get_map_for_room(self, room_id: str) -> str:
        """获取房间的地图"""
        # 如果房间没有地图，返回动态生成的迷雾地图
        if room_id not in self.room_maps:
            return self._generate_fog_map()
        
        # 从room_manager获取当前游戏阶段
        from services.room_manager import room_manager
        room = room_manager.get_room(room_id)
        if not room:
            return self._generate_fog_map()
        
        current_stage = room.game_state["current_stage"]
        
        # 获取当前阶段的地图
        if current_stage not in self.room_maps[room_id]:
            return self._generate_fog_map()
        
        # 获取基础地图
        base_map = self.room_maps[room_id][current_stage]
        
        # 添加玩家位置标记
        if room_id in self.player_positions:
            # 将地图转换为行列表
            map_lines = base_map.split('\n')
            
            # 为每个玩家添加标记
            for player_id, position in self.player_positions[room_id].items():
                x, y = position.get('x', 0), position.get('y', 0)
                
                # 确保坐标在有效范围内
                if 0 <= y < len(map_lines) and 0 <= x < len(map_lines[y]):
                    # 替换字符
                    line = map_lines[y]
                    map_lines[y] = line[:x] + '@' + line[x+1:]
            
            # 重新组合地图
            return '\n'.join(map_lines)
        
        return base_map
    
    def update_map(self, room_id: str, new_map: str):
        """更新房间的地图"""
        # 从room_manager获取当前游戏阶段
        from services.room_manager import room_manager
        room = room_manager.get_room(room_id)
        if not room:
            return
        
        current_stage = room.game_state["current_stage"]
        
        # 确保房间有地图字典
        if room_id not in self.room_maps:
            self.room_maps[room_id] = {}
        
        # 更新当前阶段的地图
        self.room_maps[room_id][current_stage] = new_map
        
        # 重置玩家位置
        if room_id in self.player_positions:
            self.player_positions[room_id] = {}
    
    def update_map_for_stage(self, room_id: str, stage: int, new_map: str):
        """更新特定阶段的地图"""
        # 确保房间有地图字典
        if room_id not in self.room_maps:
            self.room_maps[room_id] = {}
        
        # 更新指定阶段的地图
        self.room_maps[room_id][stage] = new_map
    
    def update_player_position(self, room_id: str, player_id: str, x: int, y: int):
        """更新玩家在地图上的位置"""
        if room_id not in self.player_positions:
            self.player_positions[room_id] = {}
        
        self.player_positions[room_id][player_id] = {'x': x, 'y': y}
    
    def remove_player(self, room_id: str, player_id: str):
        """从地图上移除玩家"""
        if room_id in self.player_positions and player_id in self.player_positions[room_id]:
            del self.player_positions[room_id][player_id]
    
    def initialize_room_map(self, room_id: str, stage: int):
        """根据游戏阶段初始化房间地图"""
        # 确保房间有地图字典
        if room_id not in self.room_maps:
            self.room_maps[room_id] = {}
        
        # 为指定阶段设置迷雾地图
        fog_map = self._generate_fog_map()
        self.room_maps[room_id][stage] = fog_map
        return fog_map

# 全局地图服务实例
map_service = MapService() 