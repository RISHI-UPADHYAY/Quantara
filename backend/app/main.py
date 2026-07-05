from fastapi import FastAPI

from app.database.session import Base, engine
from app.models.user import User



app = FastAPI(
    title = "Quantara API",
    version = "1.0.0"
)

@app.get("/")
def root():
    return { "message": "Welcome to Quantara API" }