from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from routers.ws_connection import handle_websocket
from fastapi.responses import RedirectResponse

from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket(websocket)



# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     print("连接成功")
#     while True:
#         data = await websocket.receive_text()
#         await websocket.send_text(f"接收到的消息是：{data}")

# 静态文件配置（注意 directory 路径）
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

app.mount(
    "/", 
    StaticFiles(directory=static_dir, html=True), 
    name="static"
)


if __name__ == "__main__":
    uvicorn.run(
        "adventure:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4,
        loop="uvloop"
    )