from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, webhook, orders

app = FastAPI(
    title="ShopThread API",
    description="Multi-agent commerce OS for Instagram jewellery sellers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(orders.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ShopThread API"}
