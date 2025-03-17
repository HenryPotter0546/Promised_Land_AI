const ws = new WebSocket(`ws://${location.host}/ws`);
const personalStoryDiv = document.getElementById("personal-story");
const worldInfoDiv = document.getElementById("world-info");
const playerListEl = document.getElementById("player-list");
const playerStatusEl = document.getElementById("player-status");
const gameMapEl = document.getElementById("game-map");
const inputEl = document.getElementById("input");
const roomIdEl = document.getElementById("room-id");
const playerCountEl = document.getElementById("player-count");

// 当前玩家ID
let currentPlayerId = "";
// 所有玩家列表
let players = {};
// 当前地图数据
let currentMapData = "";

// 添加消息到个人剧情
function addPersonalMessage(text, type) {
    const p = document.createElement("p");
    p.textContent = text;
    p.className = `message ${type}-message`;
    personalStoryDiv.appendChild(p);
    // 滚轮自动滚到底部
    personalStoryDiv.scrollTop = personalStoryDiv.scrollHeight;
}

// 添加消息到世界信息
function addWorldMessage(text, type) {
    const p = document.createElement("p");
    p.textContent = text;
    p.className = `message ${type}-message`;
    worldInfoDiv.appendChild(p);
    // 滚轮自动滚到底部
    worldInfoDiv.scrollTop = worldInfoDiv.scrollHeight;
}

// 更新玩家列表
function updatePlayerList() {
    playerListEl.innerHTML = "";
    Object.keys(players).forEach(playerId => {
        const li = document.createElement("li");
        li.className = "player-item";
        li.textContent = playerId === currentPlayerId ? 
            `${players[playerId]} (你)` : players[playerId];
        playerListEl.appendChild(li);
    });
}

// 更新玩家状态
function updatePlayerStatus(html) {
    playerStatusEl.innerHTML = html;
}

// 更新游戏地图
function updateGameMap(mapData) {
    // 保存当前地图数据
    currentMapData = mapData;
    
    // 检查是否是动态迷雾地图
    if (mapData === "FOG_MAP_DYNAMIC_MARKER") {
        // 使用迷雾效果模块渲染迷雾地图
        gameMapEl.innerHTML = ""; // 清空地图容器
        FogEffect.renderFogMap(gameMapEl);
        
        // 确保地图元素填满容器
        gameMapEl.style.width = "100%";
        gameMapEl.style.height = "100%";
        gameMapEl.style.display = "block";
    } else {
        // 如果是普通ASCII地图，直接设置文本内容
        gameMapEl.innerHTML = ""; // 清空地图容器
        gameMapEl.textContent = mapData;
    }
    
    // 调试信息
    console.log("更新游戏地图", {
        mapType: mapData === "FOG_MAP_DYNAMIC_MARKER" ? "迷雾地图" : "ASCII地图",
        gameMapWidth: gameMapEl.offsetWidth,
        gameMapHeight: gameMapEl.offsetHeight,
        containerWidth: document.getElementById("game-map-container").offsetWidth,
        containerHeight: document.getElementById("game-map-container").offsetHeight
    });
}

ws.onopen = () => {
    addPersonalMessage("连接成功！欢迎来到(The Promised Land)应许之地！", "system");
};

ws.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        
        if (data.type === "room_info") {
            roomIdEl.textContent = `房间ID: ${data.room_id}`;
            playerCountEl.textContent = `在线玩家: ${data.player_count}`;
            
            // 如果收到房间信息，保存当前玩家ID
            if (data.player_id && !currentPlayerId) {
                currentPlayerId = data.player_id;
            }
            
            // 更新玩家列表
            if (data.players) {
                players = data.players;
                updatePlayerList();
            }
        } 
        else if (data.type === "player_joined") {
            // 新玩家加入
            players[data.player_id] = `玩家${data.player_id.substring(0, 6)}`;
            updatePlayerList();
            addWorldMessage(`${players[data.player_id]} 加入了游戏`, "system");
        }
        else if (data.type === "player_left") {
            // 玩家离开
            if (players[data.player_id]) {
                addWorldMessage(`${players[data.player_id]} 离开了游戏`, "system");
                delete players[data.player_id];
                updatePlayerList();
            }
        }
        else if (data.type === "ai_response") {
            // AI响应只显示在个人剧情中
            addPersonalMessage(data.content, "ai");
        } 
        else if (data.type === "user_action") {
            // 其他玩家的动作显示在世界信息中
            if (data.player_id !== currentPlayerId) {
                const playerName = players[data.player_id] || `玩家${data.player_id.substring(0, 6)}`;
                addWorldMessage(`${playerName}: ${data.content}`, "user");
            } else {
                // 自己的动作显示在个人剧情中
                addPersonalMessage(`你: ${data.content}`, "user");
            }
        }
        else if (data.type === "system") {
            // 系统消息显示在世界信息中
            addWorldMessage(data.content, "system");
        }
        else if (data.type === "player_status") {
            // 更新玩家状态
            updatePlayerStatus(data.content);
        }
        else if (data.type === "game_map") {
            // 更新游戏地图
            updateGameMap(data.content);
        }
    } catch (e) {
        // 如果不是JSON格式，作为AI响应处理
        addPersonalMessage(event.data, "ai");
        console.error("解析WebSocket消息出错:", e);
    }
};

ws.onclose = () => {
    addPersonalMessage("连接已断开，请刷新页面重试", "system");
};

inputEl.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && inputEl.value.trim()) {
        const message = inputEl.value.trim();
        ws.send(JSON.stringify({
            type: "action",
            content: message
        }));
        inputEl.value = "";
    }
}); 