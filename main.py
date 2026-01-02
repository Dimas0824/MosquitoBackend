from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.database import init_db
from app.config import settings
import os

# Initialize FastAPI app
app = FastAPI(
    title="IoT Larva Detection System",
    description="Backend API for ESP32-CAM Mosquito Larva Detection",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["main"])


@app.on_event("startup")
async def startup_event():
    """Initialize database dan storage directories on startup"""
    # Create database tables
    init_db()
    
    # Ensure storage directories exist
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.IMAGE_ORIGINAL_PATH, exist_ok=True)
    os.makedirs(settings.IMAGE_PREPROCESSED_PATH, exist_ok=True)
    
    print("✓ Database initialized")
    print("✓ Storage directories created")
    print(f"✓ Server starting on {settings.API_HOST}:{settings.API_PORT}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "IoT Larva Detection System API",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
