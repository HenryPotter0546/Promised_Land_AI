import json
import re
from typing import Dict, List, Any, Optional, Tuple
from services.db_service import db_service
from services.ai_service import ai_service

class LLMDatabaseService:
    def __init__(self):
        self.db = db_service
    
    async def process_llm_action(
            self, 
            stage_hint: str, 
            player_id: str, 
            user_action: str, 
            context: str
            ) -> Tuple[str, Dict]:
        """处理LLM动作，包括读写数据库"""
        # 获取玩家信息
        player_data = self.db.get_player(player_id)
        if not player_data:
            # 如果玩家不存在，创建新玩家
            player_name = f"玩家{player_id[:6]}"
            player_data = self.db.create_player(player_id, player_name)
        
        # 构建提示，包含玩家状态和天赋信息
        prompt = self._build_prompt(player_data, user_action, context)
        
        # 调用AI服务获取响应
        ai_response = await ai_service.generate_response(stage_hint,context, prompt)

        print(f"before parse ai_response: {ai_response}")
        
        # 解析AI响应中的数据库操作指令
        updated_data = self._parse_db_operations(ai_response, player_id)

        print(f"after parse ai_response: {ai_response}")
        
        # 清理AI响应，移除数据库操作指令
        cleaned_response = self._clean_response(ai_response)

        print(f"cleaned_response: {cleaned_response}")
        
        return cleaned_response, updated_data
    
    def _build_prompt(self, player_data: Dict, user_action: str, context: str) -> str:
        """构建包含玩家数据的提示"""
        # 提取玩家基本信息
        player_info = {
            "id": player_data["id"],
            "name": player_data["name"],
            "health": player_data["health"],
            "max_health": player_data["max_health"],
            "level": player_data["level"],
            "experience": player_data["experience"],
            "gold": player_data["gold"],
            "attributes": player_data["attributes"]
        }
        
        # 提取玩家武器信息
        weapons_info = []
        for weapon in player_data["weapons"]:
            weapons_info.append({
                "id": weapon["id"],
                "name": weapon["name"],
                "description": weapon["description"],
                "damage": weapon["damage"],
                "durability": weapon["current_durability"],
                "max_durability": weapon["durability"],
                "is_equipped": bool(weapon["is_equipped"]),
                "rarity": weapon["rarity"],
                "attributes": weapon["attributes"]
            })
        
        # 提取玩家天赋信息
        talents_info = []
        for talent in player_data["talents"]:
            talents_info.append({
                "id": talent["id"],
                "name": talent["name"],
                "description": talent["description"],
                "effect": talent["effect"],
                "rarity": talent["rarity"]
            })
        
        # 构建提示
        prompt = f"""
你是一个文字冒险游戏的AI主持人。你需要根据玩家的行动生成生动的描述和结果。

当前玩家信息:
```
{json.dumps(player_info, ensure_ascii=False, indent=2)}
```

玩家武器:
```
{json.dumps(weapons_info, ensure_ascii=False, indent=2)}
```

玩家天赋:
```
{json.dumps(talents_info, ensure_ascii=False, indent=2)}
```

当前场景:
{context}

玩家行动:
{user_action}

请根据玩家行动生成响应。如果需要修改玩家数据，请使用以下格式:
[DB:UPDATE_PLAYER] {{更新的玩家数据JSON}} [/DB]
[DB:UPDATE_WEAPON] {{武器ID}} {{更新的武器数据JSON}} [/DB]
[DB:ADD_WEAPON] {{武器ID}} {{武器耐久度}} [/DB]

例如:
[DB:UPDATE_PLAYER] {{"health": 90, "gold": 60}} [/DB]
[DB:UPDATE_WEAPON] weapon_001 {{"current_durability": 45, "is_equipped": 1}} [/DB]

请注意:
1. 只有在合理的情况下才修改数据
2. 武器耐久度在使用后应适当减少
3. 如果玩家受伤，减少生命值
4. 如果玩家获得物品，增加相应的物品
5. 不要在响应中包含数据库操作的指令，这些指令会被自动处理

AI响应:
"""
        return prompt
    
    def _parse_db_operations(self, response: str, player_id: str) -> Dict:
        """解析AI响应中的数据库操作指令"""
        updated_data = {"player": {}, "weapons": {}, "new_weapons": []}
        
        # 解析更新玩家数据的指令
        player_updates = re.findall(r'\[DB:UPDATE_PLAYER\]\s*(.*?)\s*\[/DB\]', response, re.DOTALL)
        for update in player_updates:
            try:
                player_data = json.loads(update)
                updated_data["player"].update(player_data)
                self.db.update_player_stats(player_id, player_data)
            except json.JSONDecodeError:
                continue
        
        # 解析更新武器数据的指令
        weapon_updates = re.findall(r'\[DB:UPDATE_WEAPON\]\s*(\w+)\s*(.*?)\s*\[/DB\]', response, re.DOTALL)
        for weapon_id, update in weapon_updates:
            try:
                weapon_data = json.loads(update)
                updated_data["weapons"][weapon_id] = weapon_data
                self.db.update_player_weapon(player_id, weapon_id, weapon_data)
            except json.JSONDecodeError:
                continue
        
        # 解析添加武器的指令
        add_weapon = re.findall(r'\[DB:ADD_WEAPON\]\s*(\w+)\s*(\d+)\s*\[/DB\]', response)
        for weapon_id, durability in add_weapon:
            try:
                durability = int(durability)
                self.db.add_weapon_to_player(player_id, weapon_id, durability)
                updated_data["new_weapons"].append(weapon_id)
            except ValueError:
                continue
        
        return updated_data
    
    def _clean_response(self, response: str) -> str:
        """清理AI响应，移除数据库操作指令"""
        # 移除所有数据库操作指令
        cleaned = re.sub(r'\[DB:UPDATE_PLAYER\].*?\[/DB\]', '', response, flags=re.DOTALL)
        cleaned = re.sub(r'\[DB:UPDATE_WEAPON\].*?\[/DB\]', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'\[DB:ADD_WEAPON\].*?\[/DB\]', '', cleaned, flags=re.DOTALL)
        
        # 移除多余的空行
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def get_player_status_html(self, player_id: str) -> str:
        """获取玩家状态的HTML表示，用于前端显示"""
        player_data = self.db.get_player(player_id)
        if not player_data:
            return "<p>玩家数据不存在</p>"
        
        # 构建HTML
        html = f"""
        <div class="player-status">
            <h3>{player_data['name']}</h3>
            <div class="status-row">
                <span>生命值: {player_data['health']}/{player_data['max_health']}</span>
                <span>等级: {player_data['level']}</span>
                <span>经验: {player_data['experience']}</span>
                <span>金币: {player_data['gold']}</span>
            </div>
            <div class="attributes">
                <h4>属性:</h4>
                <ul>
                    <li>力量: {player_data['attributes']['strength']}</li>
                    <li>敏捷: {player_data['attributes']['dexterity']}</li>
                    <li>智力: {player_data['attributes']['intelligence']}</li>
                    <li>魅力: {player_data['attributes']['charisma']}</li>
                </ul>
            </div>
            <div class="weapons">
                <h4>武器:</h4>
                <ul>
        """
        
        for weapon in player_data["weapons"]:
            equipped = "【已装备】" if weapon["is_equipped"] else ""
            durability = f"{weapon['current_durability']}/{weapon['durability']}"
            html += f"""
                    <li>{weapon['name']} {equipped} (伤害: {weapon['damage']}, 耐久: {durability})</li>
            """
        
        html += """
                </ul>
            </div>
            <div class="talents">
                <h4>天赋:</h4>
                <ul>
        """
        
        for talent in player_data["talents"]:
            html += f"""
                    <li>{talent['name']} ({talent['rarity']}): {talent['description']}</li>
            """
        
        html += """
                </ul>
            </div>
        </div>
        """
        
        return html

# 全局LLM数据库服务实例
llm_db_service = LLMDatabaseService() 