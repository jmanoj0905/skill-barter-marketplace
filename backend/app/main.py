"""
FastAPI Main Application
Updated with skills router for Phase 2 completion
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.core.database import init_connection_pool, close_all_connections
from backend.app.api.routes import matching, chat, skills  # NEW: added skills


# ============================================
# LIFESPAN EVENTS
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    Manages database connection pool and ML models
    """
    # Startup
    print(f"🚀 Starting {settings.APP_NAME}...")
    init_connection_pool()
    print("✓ Database connection pool initialized")
    
    # Load embedding model on startup (happens in first service call)
    print("✓ Embedding service ready (model loads on first use)")
    
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
    lifespan=lifespan,
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
# INCLUDE ROUTERS
# ============================================

# Phase 1: Skills management (NEW)
app.include_router(skills.router, prefix="/api")

# Phase 2: Matching algorithm
app.include_router(matching.router, prefix="/api")

# Phase 3: Chat (basic implementation)
app.include_router(chat.router, prefix="/api")


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "message": "Welcome to Skill Barter Marketplace API",
        "docs": "/docs",
        "health": "/health",
        "phase": "Phase 2 Complete - Matching & Skills",
        "endpoints": {
            "skills": {
                "add_skill": "POST /api/skills",
                "get_skills": "GET /api/skills",
                "update_skill": "PUT /api/skills/{id}",
                "delete_skill": "DELETE /api/skills/{id}",
                "search_skills": "GET /api/skills/search?query=python",
                "suggestions": "GET /api/skills/suggestions",
                "health": "GET /api/skills/health"
            },
            "matching": {
                "find_matches": "POST /api/matching/request",
                "accept_match": "POST /api/matching/accept",
                "statistics": "GET /api/matching/statistics",
                "health": "GET /api/matching/health"
            },
            "chat": {
                "send_message": "POST /api/chat/send"
            }
        },
        "schema": "Normalized skill_graph + user_skills design",
        "features": [
            "✓ Skill normalization (auto-deduplication)",
            "✓ AI semantic matching (384-dim embeddings)",
            "✓ Multi-factor scoring (skill + trust + activity)",
            "✓ Mutual interest detection",
            "✓ Popularity tracking",
            "✓ Skill search & suggestions"
        ]
    }