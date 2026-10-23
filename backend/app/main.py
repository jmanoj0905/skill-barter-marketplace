# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager

# from app.core.config import settings
# from app.core.database import init_connection_pool, close_all_connections
# from app.api.routes import matching,chat  # NEW - Import matching routes
# from app.api.routes.session import router as session_router # NEW - Import session routes
# from app.api.routes.feedback import router as feedback_router # NEW - Import feedback routes

# # app.include_router(session_router)



# # ============================================
# # LIFESPAN EVENTS (NEW)
# # ============================================

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Lifespan events for startup and shutdown
#     Manages database connection pool
#     """
#     # Startup
#     print(f"🚀 Starting {settings.APP_NAME}...")
#     init_connection_pool()
#     print("✓ Database connection pool initialized")
    
#     yield
    
#     # Shutdown
#     print("🛑 Shutting down...")
#     close_all_connections()
#     print("✓ Database connections closed")


# # ============================================
# # CREATE APP
# # ============================================

# app = FastAPI(
#     title=settings.APP_NAME,
#     version=settings.APP_VERSION,
#     debug=settings.DEBUG,
#     # lifespan=lifespan,  # NEW - Add lifespan
# )

# # Configure CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # ============================================
# # INCLUDE ROUTERS (NEW)
# # ============================================

# # Include matching routes
# app.include_router(matching.router, prefix="/api")
# # Include chat routes
# app.include_router(chat.router, prefix="/api")
# #include session routes
# app.include_router(session_router)
# #include feedback routes
# app.include_router(feedback_router)



# # ============================================
# # ROOT ENDPOINTS
# # ============================================

# @app.get("/health")
# async def health_check():
#     """Health check endpoint for verification."""
#     return {
#         "status": "healthy",
#         "app_name": settings.APP_NAME,
#         "version": settings.APP_VERSION,
#     }


# @app.get("/")
# async def root():
#     """Root endpoint."""
#     return {
#         "message": "Welcome to Skill Barter Marketplace API",
#         "docs": "/docs",
#         "health": "/health",
#         "phase": "Phase 4 - Matching Algorithm",  # NEW
#         "endpoints": {  # NEW - Show available endpoints
#             "matching": {
#                 "find_matches": "POST /api/matching/request",
#                 "accept_match": "POST /api/matching/accept",
#                 "statistics": "GET /api/matching/statistics",
#                 "health": "GET /api/matching/health"
#             },
#                 "chat": {
#             "send_message": "POST /api/chat/send"
#             }
#         }
#     }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_routes
from app.api import skill_routes
from app.api import user_routes
from app.db import base_models
from app.db.base import Base
from app.db.session import engine
from app.models import transaction, user, wallet

app = FastAPI(title="Skill Barter Marketplace API")

# Allow local frontend apps (Vite default ports) to call API endpoints.
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:5173",
		"http://127.0.0.1:5173",
		"http://localhost:5174",
		"http://127.0.0.1:5174",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Create database tables.
Base.metadata.create_all(bind=engine)

# Register routes.
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(skill_routes.router)
app.include_router(skill_routes.api_router)


@app.get("/")
def root():
	return {"message": "Skill Barter Marketplace API is running"}


@app.get("/health")
def health():
	return {"status": "ok"}