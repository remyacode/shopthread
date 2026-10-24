from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth

app = FastAPI(
    title="ShopThread API",
    description="Multi-agent commerce OS for Instagram jewellery sellers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - only allow our frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ShopThread API"}
