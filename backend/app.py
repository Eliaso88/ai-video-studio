from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router

app = FastAPI(title="AI Video Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
