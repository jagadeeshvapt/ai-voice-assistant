#!/usr/bin/env python3
"""
JARVIS API Server - REST + WebSocket for controlling JARVIS remotely
Like having JARVIS in cloud

Endpoints:
GET  /           -> info
POST /ask        -> ask jarvis {query: "what time is it"}
GET  /memory     -> get memory
GET  /todo       -> list todos
POST /todo       -> add todo
GET  /status     -> system status
WebSocket /ws    -> real-time chat
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from jarvis.brain import get_brain
from jarvis.memory import get_memory
from jarvis.config import config

app = FastAPI(title="JARVIS API", description="JARVIS Voice Assistant API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

brain = get_brain()
memory = get_memory()

class QueryRequest(BaseModel):
    query: str
    user_name: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    response: str
    timestamp: str

@app.get("/")
def root():
    return {
        "name": config.JARVIS_NAME,
        "version": "2.0.0",
        "status": "online",
        "user": memory.data.get("user_name", "Sir"),
        "mode": "text" if config.TEXT_MODE else "voice",
        "endpoints": ["/ask", "/memory", "/todo", "/status", "/ws"]
    }

@app.post("/ask", response_model=QueryResponse)
def ask_jarvis(req: QueryRequest):
    import datetime
    if req.user_name:
        memory.set_user_name(req.user_name)
    
    response = brain.process(req.query)
    clean = response.replace("__EXIT__", "").strip()
    
    return QueryResponse(
        query=req.query,
        response=clean,
        timestamp=datetime.datetime.now().isoformat()
    )

@app.get("/memory")
def get_mem():
    return memory.data

@app.get("/todo")
def list_todo():
    return {"todos": memory.list_todo()}

@app.post("/todo")
def add_todo(req: QueryRequest):
    todo = memory.add_todo(req.query)
    return todo

@app.delete("/todo/{index}")
def delete_todo(index: int):
    success = memory.complete_todo(index)
    return {"success": success}

@app.get("/status")
def sys_status():
    import psutil, platform, datetime
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
    except:
        cpu = ram = 0
    return {
        "system": platform.system(),
        "cpu": cpu,
        "ram": ram,
        "time": datetime.datetime.now().isoformat(),
        "jarvis": config.JARVIS_NAME,
        "user": memory.data.get("user_name"),
        "history_count": len(memory.data.get("history", []))
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "greeting", "message": f"Hello {memory.data.get('user_name','Sir')}, JARVIS online. Ready."})
    
    try:
        while True:
            data = await websocket.receive_text()
            response = brain.process(data)
            clean = response.replace("__EXIT__", "").strip()
            await websocket.send_json({
                "type": "response",
                "query": data,
                "response": clean
            })
            if "__EXIT__" in response:
                await websocket.close()
                break
    except WebSocketDisconnect:
        print("WebSocket disconnected")

if __name__ == "__main__":
    print(f"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗  API Server
    Starting JARVIS API on http://localhost:8000
    Docs at http://localhost:8000/docs
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
