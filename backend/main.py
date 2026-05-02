from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import Base, engine
from backend.routes.auth_routes import router as auth_router

from backend.routes.upload_routes import router as upload_router
from backend.routes.forecast_routes import router as forecast_router

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="E-commerce AI SaaS API")

# Create tables
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router)

app.include_router(upload_router)

app.include_router(forecast_router)

@app.get("/")
def home():
    return {"message": "API running"}