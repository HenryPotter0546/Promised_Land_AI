import os
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class StoryRAGService:
    """剧情检索增强生成服务，用于提供相关的剧情背景知识以增强AI生成"""
    
    def __init__(self):
        self.story_data = []  # 存储剧情数据库
        self.vectorizer = TfidfVectorizer(max_features=100)  # TF-IDF向量化器
        self.story_vectors = None  # 存储剧情数据的TF-IDF向量
        self.story_db_path = "data/story_database.json"
        self.initialize_story_database()
    
    def initialize_story_database(self):
        """初始化剧情数据库"""
        # 检查是否存在数据目录，如果不存在则创建
        os.makedirs("data", exist_ok=True)
        
        # 尝试加载现有的剧情数据库
        if os.path.exists(self.story_db_path):
            try:
                with open(self.story_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.story_data = data.get("stories", [])
                    print(f"成功加载剧情数据库，共 {len(self.story_data)} 条记录")
                    # 加载后立即生成向量
                    self.generate_embeddings()
            except Exception as e:
                print(f"加载剧情数据库失败: {e}")
                # 初始化默认剧情数据
                self._initialize_default_stories()
        else:
            # 初始化默认剧情数据
            self._initialize_default_stories()
    
    def _initialize_default_stories(self):
        """初始化默认剧情数据"""
        # 默认的剧情数据
        default_stories = [
            {
                "title": "洞穴入口",
                "stage": 0,
                "content": "洞穴入口被古老的藤蔓和苔藓覆盖，透出一种神秘的氛围。据传说，这个洞穴中藏有失落的宝藏，但也有许多探险者踏入后再也没有回来。洞穴深处的微光像是在诱惑着冒险者深入探索。"
            },
            {
                "title": "洞穴深处的宝箱",
                "stage": 0,
                "content": "在洞穴深处，有一个古老的宝箱，它被精美的雕刻和神秘的符文所装饰。宝箱周围的地面上有奇怪的花纹，似乎是某种魔法阵。空气中弥漫着一种古老的能量，让人感到不安和好奇。"
            },
            {
                "title": "陷阱与迷宫",
                "stage": 1,
                "content": "宝箱是个精心设计的陷阱，打开它的人会被传送到一个复杂的迷宫中。这个迷宫的墙壁由一种奇特的黑色石材构成，能够轻微改变位置，让走在其中的人永远找不到出路。迷宫中散落着之前探险者的遗骸，他们的表情凝固在恐惧之中。"
            },
            {
                "title": "迷宫的恐怖",
                "stage": 1,
                "content": "迷宫中潜伏着无形的恐惧，那是探险者内心深处最原始的恐惧被迷宫魔法具象化的结果。每个人看到的恐惧都不同，但都足以让人崩溃。只有那些内心强大的人才能看穿这种幻象，找到隐藏在恐惧背后的线索。"
            },
            {
                "title": "迷宫出口",
                "stage": 2,
                "content": "经过重重考验，迷宫的出口终于出现在视野中。然而，出口前站着一个身披黑色斗篷的高大身影——迷宫的建造者，被称为'魔王'的存在。他的眼睛闪烁着不祥的红光，手持一把由纯粹黑暗锻造的长剑。"
            },
            {
                "title": "魔王的防御",
                "stage": 2,
                "content": "魔王周身环绕着一层魔法屏障，普通的物理攻击无法穿透。他能够操控迷宫中的阴影，将它们变成攻击的武器。魔王似乎了解每个进入迷宫者的内心，总能说出让人动摇的话语。"
            },
            {
                "title": "魔王的弱点",
                "stage": 3,
                "content": "仔细观察可以发现，魔王胸前挂着一个发光的水晶吊坠，那是他力量的源泉，也是他的弱点。每当他使用强大魔法时，吊坠会闪烁不定的光芒。此外，魔王左肩的护甲有一道裂痕，那里曾经被一位英雄的圣剑所伤。"
            },
            {
                "title": "魔王的过去",
                "stage": 3,
                "content": "魔王曾经也是一位为正义而战的勇者，但在一次对抗远古邪恶的战斗中，他被黑暗力量所侵蚀。那个水晶吊坠原本是封印黑暗的圣物，现在却成了维持他生命的关键。在某些瞬间，你可以在他的眼中看到挣扎的人性光芒。"
            },
            {
                "title": "击败魔王",
                "stage": 4,
                "content": "魔王在战斗中被击败，那个水晶吊坠碎裂开来，黑暗的能量从中释放。魔王的身体开始崩解，最后化为点点光芒消散在空气中。他的最后一句话充满了解脱：'终于...自由了...'。战胜魔王后，迷宫开始塌陷，留给探索者有限的逃生时间。"
            },
            {
                "title": "魔王的宝藏",
                "stage": 4,
                "content": "魔王的宝库中堆满了来自不同时代和地域的珍宝。金币、宝石、武器、防具、魔法卷轴和药剂应有尽有。特别引人注目的是一套闪烁着金光的铠甲和一把散发着圣洁能量的长剑——传说中的'光明守护者'套装，据说穿戴它的人能够抵御一切黑暗力量。"
            },
            {
                "title": "远离城镇",
                "stage": 5,
                "content": "走出洞穴后，探险者们发现自己处于一片陌生的荒原中，远离任何已知的城镇。天空中不寻常的星象表明，他们不仅在空间上被传送，甚至可能在时间上也发生了扭曲。远处隐约可见一座高耸的山脉，那可能是唯一的地标。"
            },
            {
                "title": "荒原的危险",
                "stage": 5,
                "content": "荒原中生活着各种危险的生物，有巨大的沙虫能够在沙地下高速移动；有能够伪装成岩石的捕食者；还有夜晚出没的幽灵般的掠食者。此外，频繁的沙尘暴和极端的温差也是生存的巨大挑战。水源稀缺，每一滴水都珍贵如金。"
            },
            {
                "title": "返回城镇",
                "stage": 6,
                "content": "经过艰辛的旅程，城镇的轮廓终于出现在地平线上。那是一座繁华的贸易城市，高大的城墙和醒目的瞭望塔提供了安全保障。城门口排着长队，商队和旅行者都在等待入城。守卫严格检查每个人，以防邪恶力量的渗透。"
            },
            {
                "title": "英雄的荣耀",
                "stage": 6,
                "content": "击败魔王并带回宝藏的英雄在城中受到盛大的欢迎。市长举办了盛大的庆典，人们在街头歌舞庆祝。英雄的事迹被吟游诗人传唱，很快就传遍了整个王国。国王甚至派使者前来，邀请英雄前往王城接受嘉奖。"
            }
        ]
        
        self.story_data = default_stories
        # 保存到文件
        self._save_story_database()
        # 生成向量
        self.generate_embeddings()
        print(f"初始化默认剧情数据库，共 {len(self.story_data)} 条记录")
    
    def _save_story_database(self):
        """保存剧情数据库到文件"""
        try:
            data = {
                "stories": self.story_data
            }
            with open(self.story_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"剧情数据库保存成功")
        except Exception as e:
            print(f"保存剧情数据库失败: {e}")
    
    def generate_embeddings(self):
        """为所有剧情生成TF-IDF词向量"""
        if not self.story_data:
            print("没有剧情数据，无法生成词向量")
            return
        
        texts = [story["content"] for story in self.story_data]
        
        try:
            # 使用TF-IDF生成向量
            self.story_vectors = self.vectorizer.fit_transform(texts)
            print(f"成功为 {len(texts)} 条剧情生成TF-IDF词向量")
        except Exception as e:
            print(f"生成词向量失败: {e}")
    
    def find_similar_stories(self, query: str, player_stage: int, top_k: int = 3) -> List[Dict]:
        """查找与查询文本相似的剧情"""
        # 如果没有向量，先生成
        if self.story_vectors is None:
            self.generate_embeddings()
        
        # 将查询文本转换为向量
        query_vector = self.vectorizer.transform([query])
        
        # 计算相似度
        similarities = cosine_similarity(query_vector, self.story_vectors).flatten()
        
        # 考虑玩家阶段的加权，当前阶段的剧情权重更高
        weighted_similarities = []
        for i, sim in enumerate(similarities):
            stage_weight = 1.0
            if "stage" in self.story_data[i]:
                story_stage = self.story_data[i]["stage"]
                # 当前阶段和相邻阶段的剧情权重更高
                if story_stage == player_stage:
                    stage_weight = 1.5
                elif abs(story_stage - player_stage) == 1:
                    stage_weight = 1.2
            
            weighted_similarities.append(sim * stage_weight)
        
        # 获取相似度最高的前top_k个剧情
        top_indices = np.argsort(weighted_similarities)[-top_k:][::-1]
        
        # 返回相似剧情
        similar_stories = []
        for idx in top_indices:
            story = self.story_data[idx].copy()
            story["similarity"] = float(weighted_similarities[idx])
            similar_stories.append(story)
        
        return similar_stories
    
    def get_rag_context(self, query: str, player_stage: int) -> str:
        """获取RAG增强上下文"""
        similar_stories = self.find_similar_stories(query, player_stage)
        
        if not similar_stories:
            return ""
        
        # 构建上下文
        context = "以下是相关的游戏背景信息，可用于丰富描述和回应：\n\n"
        for story in similar_stories:
            context += f"【{story['title']}】\n{story['content']}\n\n"
        
        return context

# 全局RAG服务实例
story_rag_service = StoryRAGService() 