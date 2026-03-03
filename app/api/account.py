from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi.middleware.cors import CORSMiddleware
from app.api import schemas, models

router = APIRouter(
    prefix="/userApi/v1/account",
    tags=["Accounts"]
)
