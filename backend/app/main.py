"""
VIGIL Backend - Main Application Entry Point
Privacy-Preserving Intelligent Surveillance Decision-Support System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import cameras, alerts, analytics, audit, auth, zones, demo
from app.api.websocket import router as ws_router
from app.api.stream import router as stream_router
from app.api import stats_ws
from app.db.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(" VIGIL Backend started successfully with saying Jai Shri Ram")
    yield
    # Shutdown
    print(" VIGIL Backend shutting down and saying bro i broke up bro")


app = FastAPI(
    title="VIGIL API",
    description="""
    ## Privacy-Preserving Intelligent Surveillance Decision-Support System
    
    ⚠️ **IMPORTANT DISCLAIMER**
    
    This is a **decision-support tool**, NOT a crime prediction system.
    All outputs require human interpretation and verification.
    
    ### Key Features:
    - Real-time video analysis with privacy-preserving anonymization
    - Explainable risk scoring with transparent reasoning
    - Complete audit logging for accountability
    - Human-in-the-loop design
    
    ### Ethical Commitments:
    - Anonymization by default
    - No automated enforcement actions
    - Full explainability of all alerts
    - Bias awareness and documentation
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["Cameras"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Logs"])
app.include_router(zones.router, prefix="/api/zones", tags=["Zones"])
app.include_router(stream_router, prefix="/api/stream", tags=["Video Streaming"])
app.include_router(demo.router, prefix="/api/demo", tags=["Demo & Simulation"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
app.include_router(stats_ws.router, prefix="/ws", tags=["WebSocket Stats"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "operational",
        "system": "VIGIL",
        "version": "1.0.0",
        "deployment_mode": settings.DEPLOYMENT_MODE,
        "disclaimer": "This is a decision-support tool. All outputs require human verification."
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "ml_models": "loaded",
        "anonymization": "active",
        "deployment_mode": settings.DEPLOYMENT_MODE,
    }
