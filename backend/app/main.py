from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import json
from uuid import uuid4

from .api.routes import articles, positions, analysis, activity_logs
from .api.endpoints import models
from .core.database import engine, Base
from .core.websocket import websocket_manager
from .models import Article, Analysis, Position
from .models.activity_log import ActivityLog

Base.metadata.create_all(bind=engine)

class CORSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # If it's a redirect (307), add CORS headers
        if response.status_code == 307:
            origin = request.headers.get("origin")
            if origin and any(origin.startswith(allowed) for allowed in ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

app = FastAPI(
    title="Market Analysis API",
    description="AI-powered financial news analysis and trading recommendations",
    version="1.0.0",
    redirect_slashes=False  # Disable automatic redirect to avoid CORS issues
)

app.add_middleware(CORSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"http://localhost:[0-9]+",
    expose_headers=["*"]
)

app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])
app.include_router(positions.router, prefix="/api/v1/positions", tags=["positions"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(activity_logs.router, prefix="/api/v1/activity-logs", tags=["activity-logs"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(default_factory=lambda: str(uuid4()))
):
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle subscription to analysis sessions
                if message.get("type") == "subscribe_session":
                    session_id = message.get("session_id")
                    if session_id:
                        await websocket_manager.subscribe_to_session(client_id, session_id)
                        await websocket_manager.send_personal_message(
                            {"type": "subscription_confirmed", "session_id": session_id},
                            client_id
                        )
                
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"},
                    client_id
                )
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)


@app.get("/")
async def root():
    return {"message": "Market Analysis API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logging.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )