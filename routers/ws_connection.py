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
        
        # 发送玩家的初始场景（每个玩家都从初始场景开始）
        player_scene = room.get_player_scene(player_id)
        await websocket.send_json({
            "type": "ai_response",
            "content": player_scene
        })
        
        # 获取并发送玩家当前阶段的游戏地图（每个玩家都从第一阶段开始）
        player_stage = room.get_player_stage(player_id)
        game_map = map_service.get_map_for_stage(room.room_id, player_stage)
        print(f"发送玩家 {player_id} 的地图数据: 阶段 {player_stage}")
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
                        # 广播玩家行动（只广播行动内容，不广播AI响应）
                        await room.broadcast({
                            "type": "user_action",
                            "player_id": player_id,
                            "content": message["content"]
                        })

                        # 获取玩家当前阶段
                        player_stage = room.get_player_stage(player_id)
                        hint = f"现在的情景是 {room.game_stage[player_stage]}"
                        
                        # 获取玩家当前场景
                        player_scene = room.get_player_scene(player_id)
                        
                        # 使用LLM数据库服务处理玩家行动
                        ai_response, updated_data = await llm_db_service.process_llm_action(
                            stage_hint=hint,
                            player_id=player_id,
                            user_action=message["content"],
                            context=player_scene,
                            room_id=room.room_id
                        )
                        logger.debug(f"LLM response: {ai_response}")
                        
                        # 更新玩家游戏状态
                        old_stage = player_stage
                        
                        # 随机决定是否进入下一阶段（这只影响当前玩家）
                        should_goto_next_stage = random.choice([True, False])
                        if should_goto_next_stage:
                            new_stage = min(player_stage + 1, room.stage_cnt)
                            room.update_player_stage(player_id, new_stage)
                            player_stage = new_stage
                        
                        # 更新玩家的场景和故事
                        player_state = room.get_player_state(player_id)
                        player_story = player_state.get("story", [])
                        player_story.append({
                            "action": message["content"],
                            "response": ai_response
                        })
                        
                        room.update_player_state(player_id, {
                            "current_scene": ai_response,
                            "story": player_story
                        })
                        
                        # 如果玩家阶段变化，发送对应阶段的地图
                        if old_stage != player_stage:
                            game_map = map_service.get_map_for_stage(room.room_id, player_stage)
                            print(f"玩家 {player_id} 阶段变化: {old_stage} -> {player_stage}, 发送阶段 {player_stage} 的地图")
                            await websocket.send_json({
                                "type": "game_map",
                                "content": game_map
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
            await room_manager.leave_room(player_id)
            if room.get_player_count() > 0:
                await room.broadcast({
                    "type": "player_left",
                    "player_id": player_id,
                    "player_count": room.get_player_count()
                })
                
    except Exception as e:
        logger.error(f"WebSocket连接处理发生错误: {e}", exc_info=True)
        await websocket.close(code=1001, reason=str(e))