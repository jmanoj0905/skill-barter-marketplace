from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_connection_pool, close_all_connections
from app.api.routes import matching,chat  # NEW - Import matching routes


# ============================================
# LIFESPAN EVENTS (NEW)
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    Manages database connection pool
    """
    # Startup
    print(f"🚀 Starting {settings.APP_NAME}...")
    init_connection_pool()
    print("✓ Database connection pool initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    close_all_connections()
    print("✓ Database connections closed")


# ============================================
# CREATE APP
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,  # NEW - Add lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# INCLUDE ROUTERS (NEW)
# ============================================

# Include matching routes
app.include_router(matching.router, prefix="/api")
# Include chat routes
app.include_router(chat.router, prefix="/api")


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint for verification."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Skill Barter Marketplace API",
        "docs": "/docs",
        "health": "/health",
        "phase": "Phase 4 - Matching Algorithm",  # NEW
        "endpoints": {  # NEW - Show available endpoints
            "matching": {
                "find_matches": "POST /api/matching/request",
                "accept_match": "POST /api/matching/accept",
                "statistics": "GET /api/matching/statistics",
                "health": "GET /api/matching/health"
            },
                "chat": {
            "send_message": "POST /api/chat/send"
            }
        }
    }