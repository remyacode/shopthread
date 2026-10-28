from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, webhook, orders, products, catalogue, upload, shipments, analytics

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
app.include_router(products.router)
app.include_router(catalogue.router)
app.include_router(upload.router)
app.include_router(shipments.router)
app.include_router(analytics.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ShopThread API"}
