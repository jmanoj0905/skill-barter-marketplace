from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine, SessionLocal
from app.db import base
from app.db.seed import seed_initial_data
from app.routes.session import router as session_router
from app.routes.warning import router as warning_router
from app.routes.trust import router as trust_router
# from app.routes.verdict import router as verdict_router

app = FastAPI(title="Skill Barter Marketplace Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

db = SessionLocal()
seed_initial_data(db)
db.close()

app.include_router(session_router)
app.include_router(warning_router)
app.include_router(trust_router)
# app.include_router(verdict_router)

@app.get("/")
def root():
    return {"message": "Skill Barter backend is running"}