"""
MedFlow AI - Main FastAPI Application Entrypoint
Provides REST endpoints and WebSocket channels for real-time hospital operations.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.routes_patient import router as patient_router
from .api.routes_doctor import router as doctor_router
from .api.routes_state import router as state_router
from .api.routes_simulation import router as simulation_router
from .api.websockets import ws_manager

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("medflow.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================================")
    logger.info(f" MedFlow AI Backend Initialized | Environment: {settings.ENVIRONMENT}")
    logger.info(f" OR-Tools Optimization Engine: ACTIVE | Max Timeout: {settings.MAX_ORTOOLS_SOLVER_TIME_SECONDS}s")
    logger.info("==================================================================")
    yield
    logger.info("MedFlow AI Backend shutting down.")


app = FastAPI(
    title="MedFlow AI: Multi-Agent Hospital Operations Platform",
    description="Intelligent Triage, OR-Tools Resource Optimization, and Human-in-the-Loop Safety.",
    version=settings.VERSION,
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS) for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST Routers
app.include_router(patient_router)
app.include_router(doctor_router)
app.include_router(state_router)
app.include_router(simulation_router)


# WebSocket Channel for Real-Time Streaming
@app.websocket("/ws/operations")
async def websocket_operations_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive receive loop
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.get("/")
def health_check():
    return {
        "status": "HEALTHY",
        "system": "MedFlow AI",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "websocket_url": "/ws/operations"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
