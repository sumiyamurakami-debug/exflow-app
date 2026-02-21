"""
ExFlow - Ã§ÂµÂÃ¨Â²Â»Ã§Â®Â¡Ã§ÂÂÃ£ÂÂ·Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂ  Ã£ÂÂÃ£ÂÂÃ£ÂÂ¯Ã£ÂÂ¨Ã£ÂÂ³Ã£ÂÂ
FastAPI + SQLAlchemy + SQLite
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Date, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from typing import Optional
import os, csv, io, hmac, hashlib, base64, json
from dotenv import load_dotenv

load_dotenv()

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã¨Â¨Â­Ã¥Â®Â
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
SECRET_KEY        = os.getenv("SECRET_KEY", "expflow-secret-please-change-in-production")
DATABASE_URL      = os.getenv("DATABASE_URL", "sqlite:///./expflow.db")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_TOKEN  = os.getenv("LINE_CHANNEL_TOKEN", "")

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ¿Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ¹
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã£ÂÂ¢Ã£ÂÂÃ£ÂÂ«Ã¯Â¼ÂÃ£ÂÂÃ£ÂÂ¼Ã£ÂÂ¿Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂÃ£ÂÂ«Ã¥Â®ÂÃ§Â¾Â©Ã¯Â¼Â
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    department    = Column(String(100), default="")
    role          = Column(String(20), default="employee")   # employee | admin
    line_user_id  = Column(String(100), unique=True, nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = "categories"
    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(20), unique=True, nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(Text, default="")
    is_active   = Column(Boolean, default=True)
    sort_order  = Column(Integer, default=0)

class Expense(Base):
    __tablename__ = "expenses"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount       = Column(Integer, nullable=False)
    category_id  = Column(Integer, ForeignKey("categories.id"), nullable=False)
    location     = Column(String(200), default="")
    expense_date = Column(Date, nullable=False)
    receipt_url  = Column(String(500), nullable=True)
    note         = Column(Text, default="")
    status       = Column(String(20), default="pending")   # pending | approved | rejected
    approved_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at  = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã¨ÂªÂÃ¨Â¨Â¼Ã£ÂÂ¦Ã£ÂÂ¼Ã£ÂÂÃ£ÂÂ£Ã£ÂÂªÃ£ÂÂÃ£ÂÂ£
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer  = HTTPBearer()

def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(pw, hashed)

def create_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_current_user(
    db: Session = Depends(get_db)
) -> User:
    # ログイン不要：管理者ユーザーを常に返す
    user = db.query(User).filter(User.role == "admin", User.is_active == True).first()
    if not user:
        user = db.query(User).filter(User.is_active == True).first()
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Ã§Â®Â¡Ã§ÂÂÃ¨ÂÂÃ¦Â¨Â©Ã©ÂÂÃ£ÂÂÃ¥Â¿ÂÃ¨Â¦ÂÃ£ÂÂ§Ã£ÂÂ")
    return user

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã£ÂÂªÃ£ÂÂ¯Ã£ÂÂ¨Ã£ÂÂ¹Ã£ÂÂ/Ã£ÂÂ¬Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂ³Ã£ÂÂ¹ Ã£ÂÂ¹Ã£ÂÂ­Ã£ÂÂ¼Ã£ÂÂ
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
class LoginRequest(BaseModel):
    email:    str
    password: str

class ExpenseCreate(BaseModel):
    amount:       int
    category_id:  int
    location:     Optional[str] = ""
    expense_date: date
    note:         Optional[str] = ""

class ExpenseUpdate(BaseModel):
    amount:       Optional[int]  = None
    category_id:  Optional[int]  = None
    location:     Optional[str]  = None
    expense_date: Optional[date] = None
    note:         Optional[str]  = None

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã£ÂÂÃ£ÂÂ«Ã£ÂÂÃ£ÂÂ¼
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
def expense_to_dict(e: Expense, db: Session) -> dict:
    user  = db.query(User).filter(User.id == e.user_id).first()
    cat   = db.query(Category).filter(Category.id == e.category_id).first()
    appr  = db.query(User).filter(User.id == e.approved_by).first() if e.approved_by else None
    return {
        "id":           e.id,
        "amount":       e.amount,
        "status":       e.status,
        "location":     e.location or "",
        "note":         e.note or "",
        "expense_date": e.expense_date.isoformat() if e.expense_date else "",
        "receipt_url":  e.receipt_url,
        "created_at":   e.created_at.isoformat() if e.created_at else "",
        "approved_at":  e.approved_at.isoformat() if e.approved_at else None,
        "user":     {"id": user.id,  "name": user.name,  "department": user.department}  if user else {},
        "category": {"id": cat.id,   "name": cat.name,   "code": cat.code}               if cat  else {},
        "approver": {"id": appr.id,  "name": appr.name}                                  if appr else None,
    }

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# FastAPI Ã£ÂÂ¢Ã£ÂÂÃ£ÂÂªÃ£ÂÂ±Ã£ÂÂ¼Ã£ÂÂ·Ã£ÂÂ§Ã£ÂÂ³
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
app = FastAPI(
    title="ExFlow API",
    description="Ã§ÂµÂÃ¨Â²Â»Ã§Â®Â¡Ã§ÂÂÃ£ÂÂ·Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂ  REST API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã¨ÂªÂÃ¨Â¨Â¼Ã£ÂÂ¨Ã£ÂÂ³Ã£ÂÂÃ£ÂÂÃ£ÂÂ¤Ã£ÂÂ³Ã£ÂÂ
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Ã£ÂÂ­Ã£ÂÂ°Ã£ÂÂ¤Ã£ÂÂ³ Ã¢ÂÂ JWTÃ£ÂÂÃ£ÂÂ¼Ã£ÂÂ¯Ã£ÂÂ³Ã£ÂÂÃ¨Â¿ÂÃ£ÂÂ"""
    user = db.query(User).filter(User.email == req.email, User.is_active == True).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Ã£ÂÂ¡Ã£ÂÂ¼Ã£ÂÂ«Ã£ÂÂ¢Ã£ÂÂÃ£ÂÂ¬Ã£ÂÂ¹Ã£ÂÂ¾Ã£ÂÂÃ£ÂÂ¯Ã£ÂÂÃ£ÂÂ¹Ã£ÂÂ¯Ã£ÂÂ¼Ã£ÂÂÃ£ÂÂÃ©ÂÂÃ©ÂÂÃ£ÂÂ£Ã£ÂÂ¦Ã£ÂÂÃ£ÂÂ¾Ã£ÂÂ")
    return {
        "access_token": create_token(user.id),
        "token_type":   "bearer",
        "user": {
            "id": user.id, "name": user.name, "email": user.email,
            "department": user.department, "role": user.role
        }
    }

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã£ÂÂ¦Ã£ÂÂ¼Ã£ÂÂ¶Ã£ÂÂ¼
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
@app.get("/api/users/me")
def get_me(current: User = Depends(get_current_user)):
    return {"id": current.id, "name": current.name, "email": current.email,
            "department": current.department, "role": current.role}

@app.get("/api/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [{"id": u.id, "name": u.name, "department": u.department, "role": u.role}
            for u in db.query(User).filter(User.is_active == True).all()]

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã§ÂµÂÃ¨Â²Â»Ã§Â§ÂÃ§ÂÂ®
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [{"id": c.id, "code": c.code, "name": c.name}
            for c in db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()]

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã§ÂµÂÃ¨Â²Â» CRUD
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
@app.get("/api/expenses")
def list_expenses(
    date_from:   Optional[str] = None,
    date_to:     Optional[str] = None,
    status:      Optional[str] = None,
    category_id: Optional[int] = None,
    user_id:     Optional[int] = None,
    sort:        str = "date_desc",
    db:          Session = Depends(get_db),
    current:     User    = Depends(get_current_user)
):
    q = db.query(Expense)
    # Ã¦Â¨Â©Ã©ÂÂÃ£ÂÂÃ£ÂÂ£Ã£ÂÂ«Ã£ÂÂ¿Ã£ÂÂ¼Ã¯Â¼ÂÃ§Â¤Â¾Ã¥ÂÂ¡Ã£ÂÂ¯Ã¨ÂÂªÃ¥ÂÂÃ£ÂÂ®Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂ®Ã£ÂÂ¿Ã¯Â¼Â
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    elif user_id:
        q = q.filter(Expense.user_id == user_id)

    if date_from:   q = q.filter(Expense.expense_date >= date_from)
    if date_to:     q = q.filter(Expense.expense_date <= date_to)
    if status:      q = q.filter(Expense.status == status)
    if category_id: q = q.filter(Expense.category_id == category_id)

    sort_map = {
        "date_desc":   Expense.expense_date.desc(),
        "date_asc":    Expense.expense_date.asc(),
        "amount_desc": Expense.amount.desc(),
        "amount_asc":  Expense.amount.asc(),
    }
    q = q.order_by(sort_map.get(sort, Expense.expense_date.desc()))
    return [expense_to_dict(e, db) for e in q.all()]

@app.post("/api/expenses", status_code=201)
def create_expense(
    req:     ExpenseCreate,
    db:      Session = Depends(get_db),
    current: User    = Depends(get_current_user)
):
    e = Expense(
        user_id=current.id, amount=req.amount,
        category_id=req.category_id, location=req.location,
        expense_date=req.expense_date, note=req.note
    )
    db.add(e); db.commit(); db.refresh(e)
    return expense_to_dict(e, db)

@app.get("/api/expenses/{expense_id}")
def get_expense(expense_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂÃ¨Â¦ÂÃ£ÂÂ¤Ã£ÂÂÃ£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    if current.role != "admin" and e.user_id != current.id:
        raise HTTPException(403, "Ã£ÂÂ¢Ã£ÂÂ¯Ã£ÂÂ»Ã£ÂÂ¹Ã¦Â¨Â©Ã©ÂÂÃ£ÂÂÃ£ÂÂÃ£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    return expense_to_dict(e, db)

@app.put("/api/expenses/{expense_id}")
def update_expense(
    expense_id: int, req: ExpenseUpdate,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂÃ¨Â¦ÂÃ£ÂÂ¤Ã£ÂÂÃ£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    if e.user_id != current.id and current.role != "admin":
        raise HTTPException(403, "Ã£ÂÂ¢Ã£ÂÂ¯Ã£ÂÂ»Ã£ÂÂ¹Ã¦Â¨Â©Ã©ÂÂÃ£ÂÂÃ£ÂÂÃ£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    if e.status == "approved":
        raise HTTPException(400, "Ã¦ÂÂ¿Ã¨ÂªÂÃ¦Â¸ÂÃ£ÂÂ¿Ã£ÂÂ®Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂ¯Ã¥Â¤ÂÃ¦ÂÂ´Ã£ÂÂ§Ã£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    if req.amount       is not None: e.amount       = req.amount
    if req.category_id  is not None: e.category_id  = req.category_id
    if req.location     is not None: e.location     = req.location
    if req.expense_date is not None: e.expense_date = req.expense_date
    if req.note         is not None: e.note         = req.note
    e.updated_at = datetime.utcnow()
    db.commit(); db.refresh(e)
    return expense_to_dict(e, db)

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂÃ¨Â¦ÂÃ£ÂÂ¤Ã£ÂÂÃ£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    if e.user_id != current.id and current.role != "admin":
        raise HTTPException(403, "Ã£ÂÂ¢Ã£ÂÂ¯Ã£ÂÂ»Ã£ÂÂ¹Ã¦Â¨Â©Ã©ÂÂÃ£ÂÂÃ£ÂÂÃ£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    if e.status == "approved":
        raise HTTPException(400, "Ã¦ÂÂ¿Ã¨ÂªÂÃ¦Â¸ÂÃ£ÂÂ¿Ã£ÂÂ®Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂ¯Ã¥ÂÂÃ©ÂÂ¤Ã£ÂÂ§Ã£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    db.delete(e); db.commit()
    return {"message": "Ã¥ÂÂÃ©ÂÂ¤Ã£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ"}

@app.post("/api/expenses/{expense_id}/approve")
def approve_expense(expense_id: int, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂÃ¨Â¦ÂÃ£ÂÂ¤Ã£ÂÂÃ£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    e.status = "approved"; e.approved_by = current.id; e.approved_at = datetime.utcnow()
    db.commit(); db.refresh(e)
    return expense_to_dict(e, db)

@app.post("/api/expenses/{expense_id}/reject")
def reject_expense(expense_id: int, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂÃ¨Â¦ÂÃ£ÂÂ¤Ã£ÂÂÃ£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    e.status = "rejected"; e.approved_by = current.id; e.approved_at = datetime.utcnow()
    db.commit(); db.refresh(e)
    return expense_to_dict(e, db)

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã¥ÂÂÃ¦ÂÂÃ£ÂÂ»Ã©ÂÂÃ¨Â¨Â
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
@app.get("/api/analytics/summary")
def analytics_summary(
    year: int = 2026, month: int = 2,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    """Ã£ÂÂÃ£ÂÂÃ£ÂÂ·Ã£ÂÂ¥Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂÃ§ÂÂ¨Ã£ÂÂµÃ£ÂÂÃ£ÂÂªÃ£ÂÂ¼"""
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)

    all_exp  = q.all()
    ym       = f"{year}-{str(month).zfill(2)}"
    monthly  = [e for e in all_exp if e.expense_date and e.expense_date.isoformat()[:7] == ym]
    yearly   = [e for e in all_exp if e.expense_date and e.expense_date.year == year]
    pending  = [e for e in all_exp if e.status == "pending"]

    return {
        "monthly_total":  sum(e.amount for e in monthly),
        "monthly_count":  len(monthly),
        "yearly_total":   sum(e.amount for e in yearly),
        "yearly_count":   len(yearly),
        "pending_count":  len(pending),
    }

@app.get("/api/analytics/monthly")
def analytics_monthly(
    year: int = 2026,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    """Ã¦ÂÂÃ¥ÂÂ¥Ã¦ÂÂ¨Ã§Â§Â»Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ¿"""
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    all_exp = [e for e in q.all() if e.expense_date and e.expense_date.year == year]

    return [
        {
            "month": m, "label": f"{m}Ã¦ÂÂ",
            "total": sum(e.amount for e in all_exp if e.expense_date.month == m),
            "count": len([e for e in all_exp if e.expense_date.month == m])
        }
        for m in range(1, 13)
    ]

@app.get("/api/analytics/daily")
def analytics_daily(
    year: int = 2026, month: int = 2,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    """Ã¦ÂÂ¥Ã¥ÂÂ¥Ã¦ÂÂ¨Ã§Â§Â»Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ¿"""
    import calendar
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    ym      = f"{year}-{str(month).zfill(2)}"
    all_exp = [e for e in q.all() if e.expense_date and e.expense_date.isoformat()[:7] == ym]
    days    = calendar.monthrange(year, month)[1]

    return [
        {
            "day": d, "label": f"{d}Ã¦ÂÂ¥",
            "total": sum(e.amount for e in all_exp if e.expense_date.day == d),
            "count": len([e for e in all_exp if e.expense_date.day == d])
        }
        for d in range(1, days + 1)
    ]

@app.get("/api/analytics/category")
def analytics_category(
    year:  Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    """Ã§Â§ÂÃ§ÂÂ®Ã¥ÂÂ¥Ã©ÂÂÃ¨Â¨Â"""
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    all_exp = q.all()

    if year:  all_exp = [e for e in all_exp if e.expense_date and e.expense_date.year  == year]
    if month: all_exp = [e for e in all_exp if e.expense_date and e.expense_date.month == month]

    grand   = sum(e.amount for e in all_exp)
    cats    = db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()
    result  = []
    for c in cats:
        items = [e for e in all_exp if e.category_id == c.id]
        if not items: continue
        total = sum(e.amount for e in items)
        result.append({
            "category_id":   c.id,
            "category_name": c.name,
            "category_code": c.code,
            "count":  len(items),
            "total":  total,
            "avg":    total // len(items),
            "ratio":  round(total / grand * 100, 1) if grand > 0 else 0.0,
        })
    return sorted(result, key=lambda x: x["total"], reverse=True)

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# CSV Ã£ÂÂ¨Ã£ÂÂ¯Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
@app.get("/api/export/csv")
def export_csv(
    date_from:   Optional[str] = None,
    date_to:     Optional[str] = None,
    status:      Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    if date_from:   q = q.filter(Expense.expense_date >= date_from)
    if date_to:     q = q.filter(Expense.expense_date <= date_to)
    if status:      q = q.filter(Expense.status == status)
    if category_id: q = q.filter(Expense.category_id == category_id)

    items       = q.order_by(Expense.expense_date.desc()).all()
    status_map  = {"approved": "Ã¦ÂÂ¿Ã¨ÂªÂÃ¦Â¸ÂÃ£ÂÂ¿", "pending": "Ã¦ÂÂ¿Ã¨ÂªÂÃ¥Â¾ÂÃ£ÂÂ¡", "rejected": "Ã¥ÂÂ¦Ã¨ÂªÂ"}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ã§ÂµÂÃ¨Â²Â»ID","Ã§ÂÂ³Ã¨Â«ÂÃ¨ÂÂ","Ã©ÂÂ¨Ã§Â½Â²","Ã§ÂÂºÃ§ÂÂÃ¦ÂÂ¥","Ã§Â§ÂÃ§ÂÂ®","Ã§Â§ÂÃ§ÂÂ®Ã£ÂÂ³Ã£ÂÂ¼Ã£ÂÂ","Ã¤Â½Â¿Ã§ÂÂ¨Ã¥Â Â´Ã¦ÂÂ","Ã©ÂÂÃ©Â¡ÂÃ¯Â¼ÂÃ¥ÂÂÃ¯Â¼Â","Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ¿Ã£ÂÂ¹","Ã¥ÂÂÃ¨ÂÂ","Ã§ÂÂ»Ã©ÂÂ²Ã¦ÂÂ¥"])
    for e in items:
        u = db.query(User).filter(User.id == e.user_id).first()
        c = db.query(Category).filter(Category.id == e.category_id).first()
        writer.writerow([
            e.id,
            u.name if u else "", u.department if u else "",
            e.expense_date.isoformat() if e.expense_date else "",
            c.name if c else "", c.code if c else "",
            e.location or "", e.amount,
            status_map.get(e.status, e.status),
            e.note or "",
            e.created_at.isoformat() if e.created_at else ""
        ])

    content = "\ufeff" + output.getvalue()   # BOMÃ¤Â»ÂÃ£ÂÂUTF-8Ã¯Â¼ÂExcelÃ¥Â¯Â¾Ã¥Â¿ÂÃ¯Â¼Â
    filename = f"expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# LINE Webhook
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
@app.post("/api/line/webhook")
async def line_webhook(request: Request, db: Session = Depends(get_db)):
    """LINEÃ¥ÂÂ¬Ã¥Â¼ÂÃ£ÂÂ¢Ã£ÂÂ«Ã£ÂÂ¦Ã£ÂÂ³Ã£ÂÂÃ£ÂÂÃ£ÂÂÃ£ÂÂ®WebhookÃ£ÂÂÃ¥ÂÂÃ¤Â¿Â¡"""
    body = await request.body()

    # Ã§Â½Â²Ã¥ÂÂÃ¦Â¤ÂÃ¨Â¨Â¼Ã¯Â¼ÂLINE_CHANNEL_SECRETÃ£ÂÂÃ¨Â¨Â­Ã¥Â®ÂÃ£ÂÂÃ£ÂÂÃ£ÂÂ¦Ã£ÂÂÃ£ÂÂÃ¥Â Â´Ã¥ÂÂÃ¯Â¼Â
    if LINE_CHANNEL_SECRET:
        sig      = request.headers.get("X-Line-Signature", "")
        h        = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
        expected = base64.b64encode(h).decode()
        if not hmac.compare_digest(expected, sig):
            raise HTTPException(400, "Invalid LINE signature")

    data = json.loads(body)
    for event in data.get("events", []):
        if event.get("type") != "message": continue
        msg      = event.get("message", {})
        line_uid = event.get("source", {}).get("userId", "")

        # Ã§ÂÂ»Ã¥ÂÂÃ£ÂÂ»Ã¥ÂÂÃ§ÂÂ»Ã£ÂÂ¡Ã£ÂÂÃ£ÂÂ»Ã£ÂÂ¼Ã£ÂÂ¸Ã£ÂÂÃ¥ÂÂÃ¤Â¿Â¡
        if msg.get("type") in ("image", "video"):
            user = db.query(User).filter(User.line_user_id == line_uid).first()
            if user:
                # TODO: LINE Content APIÃ£ÂÂÃ£ÂÂÃ£ÂÂ¡Ã£ÂÂÃ£ÂÂ£Ã£ÂÂ¢Ã£ÂÂÃ¥ÂÂÃ¥Â¾Â Ã¢ÂÂ S3Ã¤Â¿ÂÃ¥Â­Â Ã¢ÂÂ Google Cloud Vision OCR
                # Ã§ÂÂ¾Ã§ÂÂ¶Ã£ÂÂ¯Ã§Â¢ÂºÃ¨ÂªÂÃ¥Â¾ÂÃ£ÂÂ¡Ã£ÂÂ®Ã£ÂÂÃ£ÂÂ¬Ã£ÂÂ¼Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂ«Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ¨Ã£ÂÂÃ£ÂÂ¦Ã§ÂÂ»Ã©ÂÂ²
                e = Expense(
                    user_id=user.id, amount=0, category_id=1,
                    expense_date=date.today(), status="pending",
                    note="Ã¢ÂÂ  LINEÃ©ÂÂÃ¤Â¿Â¡Ã£ÂÂ¬Ã£ÂÂ·Ã£ÂÂ¼Ã£ÂÂÃ¯Â¼ÂÃ©ÂÂÃ©Â¡ÂÃ£ÂÂ»Ã§Â§ÂÃ§ÂÂ®Ã£ÂÂÃ§Â¢ÂºÃ¨ÂªÂÃ£ÂÂ»Ã¤Â¿Â®Ã¦Â­Â£Ã£ÂÂÃ£ÂÂ¦Ã£ÂÂÃ£ÂÂ Ã£ÂÂÃ£ÂÂÃ¯Â¼Â",
                    receipt_url=f"line-media://{msg.get('id')}"
                )
                db.add(e); db.commit()

    return {"status": "ok"}

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã¨ÂµÂ·Ã¥ÂÂÃ¦ÂÂÃ£ÂÂ®Ã¥ÂÂ¦Ã§ÂÂÃ¯Â¼ÂDBÃ¥ÂÂÃ¦ÂÂÃ¥ÂÂ + Ã£ÂÂ·Ã£ÂÂ¼Ã£ÂÂÃ£ÂÂÃ£ÂÂ¼Ã£ÂÂ¿Ã¦ÂÂÃ¥ÂÂ¥Ã¯Â¼Â
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            _seed(db)
            print("Ã¢ÂÂ Ã¥ÂÂÃ¦ÂÂÃ£ÂÂÃ£ÂÂ¼Ã£ÂÂ¿Ã£ÂÂÃ¦ÂÂÃ¥ÂÂ¥Ã£ÂÂÃ£ÂÂ¾Ã£ÂÂÃ£ÂÂ")
    finally:
        db.close()

def _seed(db: Session):
    # ãã§ã«ãã¼ã¿ãããå ´åã¯ã¹ã­ãã
    if db.query(Category).first():
        return
    # Ã¢ÂÂÃ¢ÂÂ Ã§ÂµÂÃ¨Â²Â»Ã§Â§ÂÃ§ÂÂ® Ã¢ÂÂÃ¢ÂÂ
    cats = [
        Category(code="EXP-001", name="Ã¤ÂºÂ¤Ã©ÂÂÃ¨Â²Â»",      sort_order=1),
        Category(code="EXP-002", name="Ã¥Â®Â¿Ã¦Â³ÂÃ¨Â²Â»",      sort_order=2),
        Category(code="EXP-003", name="Ã¤Â¼ÂÃ¨Â­Â°Ã¨Â²Â»",      sort_order=3),
        Category(code="EXP-004", name="Ã¦ÂÂ¥Ã¥Â¾ÂÃ¤ÂºÂ¤Ã©ÂÂÃ¨Â²Â»",  sort_order=4),
        Category(code="EXP-005", name="Ã¦Â¶ÂÃ¨ÂÂÃ¥ÂÂÃ¨Â²Â»",    sort_order=5),
        Category(code="EXP-006", name="Ã©ÂÂÃ¤Â¿Â¡Ã¨Â²Â»",      sort_order=6),
        Category(code="EXP-007", name="Ã¦ÂÂ¸Ã§Â±ÂÃ£ÂÂ»Ã¨Â³ÂÃ¦ÂÂÃ¨Â²Â»",sort_order=7),
        Category(code="EXP-008", name="Ã§Â ÂÃ¤Â¿Â®Ã¨Â²Â»",      sort_order=8),
        Category(code="EXP-009", name="Ã¦ÂÂ¶Ã¥Â¼ÂÃ¨Â²Â»",      sort_order=9),
        Category(code="EXP-010", name="Ã£ÂÂÃ£ÂÂ®Ã¤Â»Â",      sort_order=10),
    ]
    for c in cats: db.add(c)
    db.commit()

    # Ã¢ÂÂÃ¢ÂÂ Ã£ÂÂ¦Ã£ÂÂ¼Ã£ÂÂ¶Ã£ÂÂ¼ Ã¢ÂÂÃ¢ÂÂ
    users_data = [
        ("Ã§ÂÂ°Ã¤Â¸Â­ Ã¨ÂÂ±Ã¥Â­Â", "tanaka@example.com",  "password123", "Ã¥ÂÂ¶Ã¦Â¥Â­Ã©ÂÂ¨", "employee"),
        ("Ã©ÂÂ´Ã¦ÂÂ¨ Ã¤Â¸ÂÃ©ÂÂ", "suzuki@example.com",  "password123", "Ã§Â·ÂÃ¥ÂÂÃ©ÂÂ¨", "employee"),
        ("Ã¤Â½ÂÃ¨ÂÂ¤ Ã¦Â¬Â¡Ã©ÂÂ", "sato@example.com",    "password123", "Ã¦ÂÂÃ¨Â¡ÂÃ©ÂÂ¨", "employee"),
        ("Ã¥Â±Â±Ã§ÂÂ° Ã§Â¤Â¾Ã©ÂÂ·", "yamada@example.com",  "admin1234",   "Ã§ÂµÂÃ¥ÂÂ¶",   "admin"),
    ]
    for name, email, pw, dept, role in users_data:
        db.add(User(name=name, email=email, password_hash=hash_password(pw),
                    department=dept, role=role))
    db.commit()

    uid  = {u.email: u.id for u in db.query(User).all()}
    cid  = {c.code:  c.id for c in db.query(Category).all()}

    # Ã¢ÂÂÃ¢ÂÂ Ã£ÂÂµÃ£ÂÂ³Ã£ÂÂÃ£ÂÂ«Ã§ÂµÂÃ¨Â²Â»Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ¿ Ã¢ÂÂÃ¢ÂÂ
    samples = [
        # 2026/01 Ã¢ÂÂ Ã¦ÂÂ¿Ã¨ÂªÂÃ¦Â¸ÂÃ£ÂÂ¿
        (uid["tanaka@example.com"],  1840, cid["EXP-001"], "Ã¦ÂÂ±Ã¤ÂºÂ¬Ã£ÂÂ¡Ã£ÂÂÃ£ÂÂ­",            date(2026,1,6),  "approved", "Ã¦ÂÂ°Ã¥Â®Â¿Ã¢ÂÂÃ¦Â¸ÂÃ¨Â°Â· Ã¥Â®Â¢Ã¥ÂÂÃ¨Â¨ÂªÃ¥ÂÂ",      uid["yamada@example.com"], datetime(2026,1,7,9,0)),
        (uid["tanaka@example.com"],  5400, cid["EXP-003"], "Ã£ÂÂ¹Ã£ÂÂ¿Ã£ÂÂ¼Ã£ÂÂÃ£ÂÂÃ£ÂÂ¯Ã£ÂÂ¹ Ã¦ÂÂ°Ã¥Â®Â¿",    date(2026,1,8),  "approved", "Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ Ã¤Â¼ÂÃ¨Â­Â°Ã¨Â²Â»",             uid["yamada@example.com"], datetime(2026,1,9,9,0)),
        (uid["tanaka@example.com"], 15000, cid["EXP-004"], "Ã©ÂÂÃ¥ÂºÂ§ Ã©ÂÂÃ¦ÂÂ¿Ã§ÂÂ¼Ã£ÂÂ Ã¥ÂÂ",       date(2026,1,10), "approved", "ABCÃ¥ÂÂÃ¤ÂºÂÃ£ÂÂ¨Ã£ÂÂ®Ã¦ÂÂ¥Ã¥Â¾Â",          uid["yamada@example.com"], datetime(2026,1,12,14,0)),
        (uid["suzuki@example.com"],  3500, cid["EXP-001"], "Ã¦ÂÂ°Ã¥Â¹Â¹Ã§Â·Â Ã¦ÂÂ±Ã¤ÂºÂ¬Ã¢ÂÂÃ¥ÂÂÃ¥ÂÂ¤Ã¥Â±Â",     date(2026,1,14), "approved", "Ã¥ÂÂÃ¥ÂÂ¤Ã¥Â±ÂÃ¥ÂÂºÃ¥Â¼Âµ Ã¥Â¾ÂÃ¨Â·Â¯",          uid["yamada@example.com"], datetime(2026,1,15,9,0)),
        (uid["suzuki@example.com"], 12000, cid["EXP-002"], "Ã¥ÂÂÃ¥ÂÂ¤Ã¥Â±Â Ã¦ÂÂ±Ã¦Â¨ÂªÃ£ÂÂ¤Ã£ÂÂ³",        date(2026,1,14), "approved", "Ã¥ÂÂºÃ¥Â¼ÂµÃ¥Â®Â¿Ã¦Â³Â 1Ã¦Â³Â",             uid["yamada@example.com"], datetime(2026,1,15,9,0)),
        (uid["tanaka@example.com"],  2800, cid["EXP-005"], "Ã£ÂÂ¤Ã£ÂÂÃ£ÂÂÃ©ÂÂ»Ã¦Â©Â LABI",        date(2026,1,16), "approved", "USBÃ£ÂÂÃ£ÂÂÃ£ÂÂ»Ã£ÂÂ±Ã£ÂÂ¼Ã£ÂÂÃ£ÂÂ«Ã©Â¡Â",      uid["yamada@example.com"], datetime(2026,1,17,10,0)),
        (uid["sato@example.com"],    8800, cid["EXP-008"], "Udemy",                  date(2026,1,20), "approved", "PythonÃ£ÂÂÃ£ÂÂ­Ã£ÂÂ°Ã£ÂÂ©Ã£ÂÂÃ£ÂÂ³Ã£ÂÂ°Ã¨Â¬ÂÃ¥ÂºÂ§", uid["yamada@example.com"], datetime(2026,1,21,9,0)),
        (uid["tanaka@example.com"],   660, cid["EXP-006"], "NTTÃ£ÂÂÃ£ÂÂ³Ã£ÂÂ¢",              date(2026,1,25), "approved", "Ã¦Â¥Â­Ã¥ÂÂÃ§ÂÂ¨Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂÃ©ÂÂÃ¤Â¿Â¡Ã¨Â²Â»Ã¯Â¼Â1Ã¦ÂÂÃ¯Â¼Â",uid["yamada@example.com"], datetime(2026,1,26,10,0)),
        (uid["suzuki@example.com"],  3200, cid["EXP-007"], "Ã§Â´ÂÃ¤Â¼ÂÃ¥ÂÂÃ¥Â±ÂÃ¦ÂÂ¸Ã¥ÂºÂ",            date(2026,1,28), "approved", "Ã£ÂÂÃ£ÂÂ¸Ã£ÂÂÃ£ÂÂ¹Ã¦ÂÂ¸ 3Ã¥ÂÂ",           uid["yamada@example.com"], datetime(2026,1,29,9,0)),
        # 2026/02 Ã¢ÂÂ Ã¦ÂÂ¿Ã¨ÂªÂÃ¦Â¸ÂÃ£ÂÂ¿
        (uid["tanaka@example.com"],  2100, cid["EXP-001"], "Ã¦ÂÂ±Ã¤ÂºÂ¬Ã£ÂÂ¡Ã£ÂÂÃ£ÂÂ­",              date(2026,2,3),  "approved", "Ã¥Â®Â¢Ã¥ÂÂÃ¨Â¨ÂªÃ¥ÂÂÃ¯Â¼ÂÃ¦Â±Â Ã¨Â¢ÂÃ¯Â¼Â",          uid["yamada@example.com"], datetime(2026,2,4,9,0)),
        (uid["tanaka@example.com"],  7500, cid["EXP-003"], "WeWork Ã¦Â¸ÂÃ¨Â°Â·",             date(2026,2,5),  "approved", "Ã¥Â¤ÂÃ©ÂÂ¨MTG Ã¤Â¼ÂÃ¨Â­Â°Ã¥Â®Â¤Ã¤Â»Â£",          uid["yamada@example.com"], datetime(2026,2,6,9,0)),
        (uid["sato@example.com"],   22000, cid["EXP-004"], "Ã¥ÂÂ­Ã¦ÂÂ¬Ã¦ÂÂ¨ Restaurant XYZ",   date(2026,2,7),  "approved", "DEFÃ¦Â ÂªÃ¥Â¼ÂÃ¤Â¼ÂÃ§Â¤Â¾Ã¦ÂÂ¥Ã¥Â¾Â",          uid["yamada@example.com"], datetime(2026,2,8,10,0)),
        (uid["suzuki@example.com"],  1650, cid["EXP-005"], "Amazon",                  date(2026,2,10), "approved", "Ã£ÂÂ³Ã£ÂÂÃ£ÂÂ¼Ã§ÂÂ¨Ã§Â´ÂÃ¯Â¼Â500Ã¦ÂÂÃÂ2Ã¯Â¼Â",    uid["yamada@example.com"], datetime(2026,2,11,9,0)),
        # 2026/02 Ã¢ÂÂ Ã¦ÂÂ¿Ã¨ÂªÂÃ¥Â¾ÂÃ£ÂÂ¡
        (uid["tanaka@example.com"],  5800, cid["EXP-003"], "Ã£ÂÂÃ£ÂÂÃ£ÂÂ¼Ã£ÂÂ« Ã¦Â¸ÂÃ¨Â°Â·Ã¥ÂºÂ",          date(2026,2,12), "pending",  "Ã¥ÂÂ¶Ã¦Â¥Â­Ã£ÂÂÃ£ÂÂ¼Ã£ÂÂ MTG",    None, None),
        (uid["sato@example.com"],    1200, cid["EXP-006"], "SoftBank",                date(2026,2,13), "pending",  "Ã¦Â¥Â­Ã¥ÂÂÃ§ÂÂ¨Ã£ÂÂ¹Ã£ÂÂÃ£ÂÂÃ©ÂÂÃ¤Â¿Â¡Ã¨Â²Â»Ã¯Â¼Â2Ã¦ÂÂÃ¯Â¼Â",None, None),
        (uid["tanaka@example.com"], 18000, cid["EXP-004"], "Ã©ÂºÂ»Ã¥Â¸ÂÃ¥ÂÂÃ§ÂÂª Ã¥ÂÂÃ©Â£Â Ã£ÂÂÃ£ÂÂÃ£ÂÂ",     date(2026,2,15), "pending",  "GHIÃ¥ÂÂÃ¤ÂºÂÃ¦ÂÂ¥Ã¥Â¾Â",     None, None),
        (uid["suzuki@example.com"],  4200, cid["EXP-001"], "Ã¦ÂÂ°Ã¥Â¹Â¹Ã§Â·Â Ã¦ÂÂ±Ã¤ÂºÂ¬Ã¢ÂÂÃ¥Â¤Â§Ã©ÂÂª",        date(2026,2,17), "pending",  "Ã¥Â¤Â§Ã©ÂÂªÃ¥ÂÂºÃ¥Â¼Âµ Ã¥Â¾ÂÃ¨Â·Â¯",    None, None),
        (uid["tanaka@example.com"],   980, cid["EXP-007"], "Amazon",                  date(2026,2,18), "pending",  "Ã¦ÂÂÃ¨Â¡ÂÃ¦ÂÂ¸ 1Ã¥ÂÂ",        None, None),
    ]
    for uid_, amt, cid_, loc, dt_, st, note, apid, apat in samples:
        db.add(Expense(user_id=uid_, amount=amt, category_id=cid_, location=loc,
                       expense_date=dt_, status=st, note=note,
                       approved_by=apid, approved_at=apat))
    db.commit()

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã©ÂÂÃ§ÂÂÃ£ÂÂÃ£ÂÂ¡Ã£ÂÂ¤Ã£ÂÂ«Ã©ÂÂÃ¤Â¿Â¡Ã¯Â¼ÂÃ£ÂÂÃ£ÂÂ­Ã£ÂÂ³Ã£ÂÂÃ£ÂÂ¨Ã£ÂÂ³Ã£ÂÂÃ¯Â¼Â
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# Ã£ÂÂ¨Ã£ÂÂ³Ã£ÂÂÃ£ÂÂªÃ£ÂÂ¼Ã£ÂÂÃ£ÂÂ¤Ã£ÂÂ³Ã£ÂÂ
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
