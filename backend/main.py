from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import Base, engine
from backend.routes.auth_routes import router as auth_router
from backend.routes.upload_routes import router as upload_router
from backend.routes.forecast_routes import router as forecast_router


app = FastAPI(title="E-commerce AI SaaS API")

# Create database tables
Base.metadata.create_all(bind=engine)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(forecast_router)


@app.get("/")
def root():
    return {
        "status": "API is running",
        "message": "E-commerce AI SaaS backend is live"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }