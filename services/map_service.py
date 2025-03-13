from typing import Dict, List, Optional
import json
import os

class MapService:
    def __init__(self):
        # 存储每个房间的地图
        self.room_maps: Dict[str, str] = {}
        # 玩家位置标记
        self.player_positions: Dict[str, Dict[str, Dict[str, int]]] = {}
        # 默认空地图
        self.default_map = """
  北
  ↑
[入口]═══小路═══[未知区域]
  ║           
  ║      
  ║           
[未知]      
  ║           
  ║
  ║
"""
        # 预设的游戏阶段地图模板
        self.stage_maps = {
            0: """
  北
  ↑
[森林]═══小路═══[洞穴入口🔴]
  ║           ║
  ║      小径-╫-小径
  ║           ║
[树林]      [岩石]
  ║           ║
  ║══小路══[洞穴深处]
""",
            1: """
  北
  ↑
[洞穴入口]═══通道═══[陷阱🔴]
  ║           ║
  ║      岔路-╫-岔路
  ║           ║
[石壁]      [尸骨]
  ║           ║
  ║══通道══[迷宫入口]══通道═══[?]
""",
            2: """
  北
  ↑
[陷阱]═══通道═══[迷宫中心]
  ║           ║
  ║      岔路-╫-岔路
  ║           ║
[死路]      [宝箱]
  ║           ║
  ║══通道══[迷宫出口🔴]══通道═══[?]
""",
            3: """
  北
  ↑
[迷宫]═══通道═══[魔王大厅🔴]
  ║           ║
  ║      岔路-╫-岔路
  ║           ║
[石柱]      [魔法阵]
  ║           ║
  ║══通道══[宝座]══通道═══[?]
""",
            4: """
  北
  ↑
[魔王大厅]═══通道═══[宝库]
  ║           ║
  ║      岔路-╫-岔路
  ║           ║
[石柱]      [魔法阵]
  ║           ║
  ║══通道══[宝座🔴]══通道═══[出口]
""",
            5: """
  北
  ↑
[洞穴]═══荒野═══[山脉]
  ║           ║
  ║      小径-╫-小径
  ║           ║
[森林]      [河流🔴]
  ║           ║
  ║══荒野══[平原]══荒野═══[远方城镇]
""",
            6: """
  北
  ↑
[荒野]═══大路═══[城门]
  ║           ║
  ║      小路-╫-小路
  ║           ║
[农田]      [市场]
  ║           ║
  ║══大路══[城镇广场🔴]══大路═══[城堡]
"""
        }
    
    def get_map_for_room(self, room_id: str) -> str:
        """获取房间的地图"""
        # 如果房间没有地图，返回默认地图
        if room_id not in self.room_maps:
            return self.default_map
        
        # 获取基础地图
        base_map = self.room_maps[room_id]
        
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
        self.room_maps[room_id] = new_map
        # 重置玩家位置
        if room_id in self.player_positions:
            self.player_positions[room_id] = {}
    
    def update_player_position(self, room_id: str, player_id: str, x: int, y: int):
        """更新玩家在地图上的位置"""
        if room_id not in self.player_positions:
            self.player_positions[room_id] = {}
        
        self.player_positions[room_id][player_id] = {'x': x, 'y': y}
    
    def remove_player(self, room_id: str, player_id: str):
        """从地图上移除玩家"""
        if room_id in self.player_positions and player_id in self.player_positions[room_id]:
            del self.player_positions[room_id][player_id]
    
    def get_stage_map(self, stage: int) -> str:
        """根据游戏阶段获取预设地图"""
        return self.stage_maps.get(stage, self.default_map)
    
    def initialize_room_map(self, room_id: str, stage: int):
        """根据游戏阶段初始化房间地图"""
        stage_map = self.get_stage_map(stage)
        self.update_map(room_id, stage_map)
        return stage_map

# 全局地图服务实例
map_service = MapService() 