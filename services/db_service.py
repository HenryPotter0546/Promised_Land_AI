import sqlite3
import json
import os
import uuid
from typing import Dict, List, Any, Optional

class DatabaseService:
    def __init__(self, db_path="game_data.db"):
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        # 玩家表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            name TEXT,
            health INTEGER DEFAULT 100,
            max_health INTEGER DEFAULT 100,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 50,
            attributes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 武器表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS weapons (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            damage INTEGER,
            durability INTEGER,
            rarity TEXT,
            attributes TEXT
        )
        ''')
        
        # 玩家武器关联表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_weapons (
            player_id TEXT,
            weapon_id TEXT,
            is_equipped INTEGER DEFAULT 0,
            current_durability INTEGER,
            PRIMARY KEY (player_id, weapon_id),
            FOREIGN KEY (player_id) REFERENCES players (id),
            FOREIGN KEY (weapon_id) REFERENCES weapons (id)
        )
        ''')
        
        # 天赋表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS talents (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            effect TEXT,
            rarity TEXT
        )
        ''')
        
        # 玩家天赋关联表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_talents (
            player_id TEXT,
            talent_id TEXT,
            PRIMARY KEY (player_id, talent_id),
            FOREIGN KEY (player_id) REFERENCES players (id),
            FOREIGN KEY (talent_id) REFERENCES talents (id)
        )
        ''')
        
        # 初始化基础武器
        self._init_basic_weapons()
        
        # 初始化基础天赋
        self._init_basic_talents()
        
        self.conn.commit()
    
    def _init_basic_weapons(self):
        """初始化基础武器数据"""
        basic_weapons = [
            {
                "id": "weapon_001",
                "name": "生锈的短剑",
                "description": "一把普通的短剑，已经有些生锈了。",
                "damage": 5,
                "durability": 50,
                "rarity": "普通",
                "attributes": json.dumps({"critical_chance": 0.05})
            },
            {
                "id": "weapon_002",
                "name": "猎人弓",
                "description": "猎人常用的弓，射程较远。",
                "damage": 7,
                "durability": 40,
                "rarity": "普通",
                "attributes": json.dumps({"range": 2})
            },
            {
                "id": "weapon_003",
                "name": "魔法杖",
                "description": "能够释放简单魔法的法杖。",
                "damage": 8,
                "durability": 30,
                "rarity": "稀有",
                "attributes": json.dumps({"magic_damage": 3})
            }
        ]
        
        for weapon in basic_weapons:
            self.cursor.execute(
                "INSERT OR IGNORE INTO weapons VALUES (?, ?, ?, ?, ?, ?, ?)",
                (weapon["id"], weapon["name"], weapon["description"], 
                 weapon["damage"], weapon["durability"], weapon["rarity"], 
                 weapon["attributes"])
            )
    
    def _init_basic_talents(self):
        """初始化基础天赋数据"""
        basic_talents = [
            {
                "id": "talent_001",
                "name": "强壮体魄",
                "description": "你天生体格强健，拥有更多的生命值。",
                "effect": json.dumps({"health_bonus": 20}),
                "rarity": "普通"
            },
            {
                "id": "talent_002",
                "name": "敏锐感知",
                "description": "你的感官异常敏锐，能够察觉到常人无法发现的细节。",
                "effect": json.dumps({"perception_bonus": 2, "critical_chance_bonus": 0.1}),
                "rarity": "稀有"
            },
            {
                "id": "talent_003",
                "name": "魔法亲和",
                "description": "你天生与魔法元素亲近，使用魔法武器时更加得心应手。",
                "effect": json.dumps({"magic_damage_bonus": 5}),
                "rarity": "稀有"
            },
            {
                "id": "talent_004",
                "name": "幸运儿",
                "description": "你似乎总是比别人更加幸运。",
                "effect": json.dumps({"luck_bonus": 3, "loot_chance_bonus": 0.15}),
                "rarity": "稀有"
            },
            {
                "id": "talent_005",
                "name": "商人天赋",
                "description": "你在交易方面有着天然的优势。",
                "effect": json.dumps({"buy_discount": 0.1, "sell_bonus": 0.1}),
                "rarity": "普通"
            }
        ]
        
        for talent in basic_talents:
            self.cursor.execute(
                "INSERT OR IGNORE INTO talents VALUES (?, ?, ?, ?, ?)",
                (talent["id"], talent["name"], talent["description"], 
                 talent["effect"], talent["rarity"])
            )
    
    def create_player(self, player_id: str, name: str) -> Dict:
        """创建新玩家"""
        attributes = json.dumps({
            "strength": 5,
            "dexterity": 5,
            "intelligence": 5,
            "charisma": 5
        })
        
        self.cursor.execute(
            "INSERT INTO players (id, name, attributes) VALUES (?, ?, ?)",
            (player_id, name, attributes)
        )
        
        # 给新玩家分配初始武器
        self.cursor.execute(
            "INSERT INTO player_weapons (player_id, weapon_id, current_durability) VALUES (?, ?, ?)",
            (player_id, "weapon_001", 50)  # 生锈的短剑作为初始武器
        )
        
        # 随机分配3个天赋
        import random
        talent_ids = ["talent_001", "talent_002", "talent_003", "talent_004", "talent_005"]
        selected_talents = random.sample(talent_ids, 3)
        
        for talent_id in selected_talents:
            self.cursor.execute(
                "INSERT INTO player_talents (player_id, talent_id) VALUES (?, ?)",
                (player_id, talent_id)
            )
        
        self.conn.commit()
        return self.get_player(player_id)
    
    def get_player(self, player_id: str) -> Optional[Dict]:
        """获取玩家信息"""
        self.cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        player = self.cursor.fetchone()
        
        if not player:
            return None
        
        player_dict = dict(player)
        player_dict["attributes"] = json.loads(player_dict["attributes"])
        
        # 获取玩家的武器
        player_dict["weapons"] = self.get_player_weapons(player_id)
        
        # 获取玩家的天赋
        player_dict["talents"] = self.get_player_talents(player_id)
        
        return player_dict
    
    def get_player_weapons(self, player_id: str) -> List[Dict]:
        """获取玩家的武器"""
        self.cursor.execute("""
            SELECT w.*, pw.is_equipped, pw.current_durability 
            FROM weapons w
            JOIN player_weapons pw ON w.id = pw.weapon_id
            WHERE pw.player_id = ?
        """, (player_id,))
        
        weapons = []
        for row in self.cursor.fetchall():
            weapon = dict(row)
            weapon["attributes"] = json.loads(weapon["attributes"])
            weapons.append(weapon)
        
        return weapons
    
    def get_player_talents(self, player_id: str) -> List[Dict]:
        """获取玩家的天赋"""
        self.cursor.execute("""
            SELECT t.* 
            FROM talents t
            JOIN player_talents pt ON t.id = pt.talent_id
            WHERE pt.player_id = ?
        """, (player_id,))
        
        talents = []
        for row in self.cursor.fetchall():
            talent = dict(row)
            talent["effect"] = json.loads(talent["effect"])
            talents.append(talent)
        
        return talents
    
    def update_player_weapon(self, player_id: str, weapon_id: str, updates: Dict) -> bool:
        """更新玩家武器信息"""
        update_fields = []
        values = []
        
        for key, value in updates.items():
            if key in ["is_equipped", "current_durability"]:
                update_fields.append(f"{key} = ?")
                values.append(value)
        
        if not update_fields:
            return False
        
        query = f"""
            UPDATE player_weapons 
            SET {', '.join(update_fields)}
            WHERE player_id = ? AND weapon_id = ?
        """
        values.extend([player_id, weapon_id])
        
        self.cursor.execute(query, values)
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def update_player_stats(self, player_id: str, updates: Dict) -> bool:
        """更新玩家状态"""
        update_fields = []
        values = []
        
        for key, value in updates.items():
            if key in ["health", "max_health", "level", "experience", "gold"]:
                update_fields.append(f"{key} = ?")
                values.append(value)
            elif key == "attributes":
                update_fields.append("attributes = ?")
                values.append(json.dumps(value))
        
        if not update_fields:
            return False
        
        query = f"""
            UPDATE players 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """
        values.append(player_id)
        
        self.cursor.execute(query, values)
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def add_weapon_to_player(self, player_id: str, weapon_id: str, durability: int) -> bool:
        """给玩家添加武器"""
        try:
            self.cursor.execute(
                "INSERT INTO player_weapons (player_id, weapon_id, current_durability) VALUES (?, ?, ?)",
                (player_id, weapon_id, durability)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 玩家已经拥有这个武器
            return False
    
    def get_all_weapons(self) -> List[Dict]:
        """获取所有武器信息"""
        self.cursor.execute("SELECT * FROM weapons")
        weapons = []
        for row in self.cursor.fetchall():
            weapon = dict(row)
            weapon["attributes"] = json.loads(weapon["attributes"])
            weapons.append(weapon)
        return weapons
    
    def get_all_talents(self) -> List[Dict]:
        """获取所有天赋信息"""
        self.cursor.execute("SELECT * FROM talents")
        talents = []
        for row in self.cursor.fetchall():
            talent = dict(row)
            talent["effect"] = json.loads(talent["effect"])
            talents.append(talent)
        return talents
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

# 全局数据库服务实例
db_service = DatabaseService() 