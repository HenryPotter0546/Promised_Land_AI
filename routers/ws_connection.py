import json
import random
from fastapi import WebSocket, WebSocketDisconnect
from services.room_manager import room_manager
from services.ai_service import ai_service
from services.llm_db_service import llm_db_service
from services.map_service import map_service
import logging
logger = logging.getLogger(__name__)

async def handle_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # 获取或创建房间
        room = await room_manager.get_or_create_room()
        # 连接到房间
        player_id = await room.connect(websocket)
        
        # 发送房间信息，包含玩家ID和玩家列表
        players_dict = {pid: f"玩家{pid[:6]}" for pid in room.players.keys()}
        await websocket.send_json({
            "type": "room_info",
            "room_id": room.room_id,
            "player_count": room.get_player_count(),
            "player_id": player_id,
            "players": players_dict
        })
        
        # 发送玩家状态
        player_status_html = llm_db_service.get_player_status_html(player_id)
        await websocket.send_json({
            "type": "player_status",
            "content": player_status_html
        })
        
        # 发送当前场景
        await websocket.send_json({
            "type": "ai_response",
            "content": room.game_state["current_scene"]
        })
        
        # 初始化并发送游戏地图
        current_stage = room.game_state["current_stage"]
        # 如果房间没有地图，根据当前阶段初始化
        if room.room_id not in map_service.room_maps:
            map_service.initialize_room_map(room.room_id, current_stage)
        
        game_map = map_service.get_map_for_room(room.room_id)
        await websocket.send_json({
            "type": "game_map",
            "content": game_map
        })
        
        # 广播新玩家加入消息
        await room.broadcast({
            "type": "player_joined",
            "player_id": player_id,
            "player_count": room.get_player_count()
        })
        
        try:
            while True:
                try:
                    # 接收玩家消息
                    data = await websocket.receive_text()
                    logger.info(f"Received data: {data}")  # 记录接收的原始数据

                    message = json.loads(data)
                    logger.debug(f"Parsed message: {message}")
                    
                    if message["type"] == "action":
                        # 广播玩家行动
                        await room.broadcast({
                            "type": "user_action",
                            "player_id": player_id,
                            "content": message["content"]
                        })

                        #todo: hint不该在这里拼接，提取成单独的函数                    
                        hint = f"现在的情景是 {room.game_stage[room.game_state['current_stage']]}"
                        
                        
                        # 使用LLM数据库服务处理玩家行动
                        ai_response, updated_data = await llm_db_service.process_llm_action(
                            stage_hint=hint,
                            player_id=player_id,
                            user_action=message["content"],
                            context=room.game_state["current_scene"],
                            room_id=room.room_id
                        )
                        logger.debug(f"LLM response: {ai_response}")
                        
                        # 更新游戏状态
                        # todo: 如何识别到没到达下一步
                        old_stage = room.game_state["current_stage"]
                        should_goto_next_stage = random.choice([True, False])
                        if should_goto_next_stage:
                            room.game_state["current_stage"] = min(room.game_state["current_stage"] + 1, room.stage_cnt)
                        
                        # 如果游戏阶段变化，更新地图
                        if old_stage != room.game_state["current_stage"]:
                            map_service.initialize_room_map(room.room_id, room.game_state["current_stage"])
                            # 广播更新后的地图
                            game_map = map_service.get_map_for_room(room.room_id)
                            await room.broadcast({
                                "type": "game_map",
                                "content": game_map
                            })
                        
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
                        
                        # 如果玩家数据有更新，发送更新后的状态
                        if updated_data["player"] or updated_data["weapons"] or updated_data["new_weapons"]:
                            player_status_html = llm_db_service.get_player_status_html(player_id)
                            await websocket.send_json({
                                "type": "player_status",
                                "content": player_status_html
                            })
                        
                        # 发送更新后的游戏地图
                        game_map = llm_db_service.get_game_map(room.room_id)
                        await room.broadcast({
                            "type": "game_map",
                            "content": game_map
                        })
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}, 原始数据: {data}")
                    await websocket.send_json({"type": "error", "content": "无效的JSON格式"})
                except KeyError as e:
                    logger.error(f"消息缺少必要字段: {e}, 消息内容: {message}")
                    await websocket.send_json({"type": "error", "content": f"缺少字段: {e}"})
                except Exception as e:
                    logger.error(f"处理消息时发生未知错误: {e}", exc_info=True)
                    await websocket.send_json({"type": "error", "content": "内部服务器错误"})
                    raise  # 重新抛出异常以触发外层断开逻辑
                    
        except WebSocketDisconnect:
            # 处理断开连接
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
        await websocket.close(code=1001, reason=str(e))