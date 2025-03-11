import json
import random
from fastapi import WebSocket, WebSocketDisconnect
from services.room_manager import room_manager
from services.ai_service import ai_service

async def handle_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # 获取或创建房间
        room = await room_manager.get_or_create_room()
        print("get avail room success")
        # 连接到房间
        
        player_id = await room.connect(websocket)
        print("connect success")
        
        # 发送房间信息，包含玩家ID和玩家列表
        players_dict = {pid: f"玩家{pid[:6]}" for pid in room.players.keys()}
        await websocket.send_json({
            "type": "room_info",
            "room_id": room.room_id,
            "player_count": room.get_player_count(),
            "player_id": player_id,
            "players": players_dict
        })
        
        # 发送当前场景
        await websocket.send_json({
            "type": "ai_response",
            "content": room.game_state["current_scene"]
        })
        
        # 广播新玩家加入消息
        await room.broadcast({
            "type": "player_joined",
            "player_id": player_id,
            "player_count": room.get_player_count()
        })
        
        try:
            while True:
                # 接收玩家消息
                data = await websocket.receive_text()
                message = json.loads(data)

                print("message:\n",message, '\n')
                
                if message["type"] == "system":
                    pass

                if message["type"] == "action":
                    # 广播玩家行动
                    await room.broadcast({
                        "type": "user_action",
                        "player_id": player_id,
                        "content": message["content"]
                    })
                    
                    # 生成AI响应
                    # todo: hint不该在这里拼接，提取成单独的函数
                    
                    hint = f"现在的情景是 {room.game_stage[room.game_state['current_stage']]}"
                    ai_response = await ai_service.generate_response(
                        stage_hint=hint,
                        context=room.game_state["current_scene"],
                        user_action=message["content"]
                    )
                    
                    # 更新游戏状态
                    # todo: 如何识别到没到达下一步
                    should_goto_next_stage = random.choice([True, False])
                    if should_goto_next_stage:
                        room.game_state["current_stage"] += 1
                    room.game_state["current_scene"] = ai_response
                    room.game_state["story"].append({
                        "action": message["content"],
                        "response": ai_response
                    })
                    
                    # 只向当前玩家发送AI响应
                    await websocket.send_json({
                        "type": "ai_response",
                        "content": ai_response
                    })
                    
        except WebSocketDisconnect:
            # 处理断开连接
            # fixme: 刷新网页会临时原地增加一个玩家，稍后才断开连接
            await room.disconnect(player_id)
            if room.get_player_count() > 0:
                await room.broadcast({
                    "type": "player_left",
                    "player_id": player_id,
                    "player_count": room.get_player_count()
                })
            else:
                room_manager.remove_room(room.room_id)
                
    except Exception as e:
        print("ERROR:\t", e)
        await websocket.close(code=1001, reason=str(e))