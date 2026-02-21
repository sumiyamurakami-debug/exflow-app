"""
ExFlow - çµè²»ç®¡çã·ã¹ãã  ããã¯ã¨ã³ã
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

# ââââââââââââââââââââââââââââââââââââââââ
# è¨­å®
# ââââââââââââââââââââââââââââââââââââââââ
SECRET_KEY        = os.getenv("SECRET_KEY", "expflow-secret-please-change-in-production")
DATABASE_URL      = os.getenv("DATABASE_URL", "sqlite:///./expflow.db")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_TOKEN  = os.getenv("LINE_CHANNEL_TOKEN", "")

# ââââââââââââââââââââââââââââââââââââââââ
# ãã¼ã¿ãã¼ã¹
# ââââââââââââââââââââââââââââââââââââââââ
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

# ââââââââââââââââââââââââââââââââââââââââ
# ã¢ãã«ï¼ãã¼ã¿ãã¼ã¹ãã¼ãã«å®ç¾©ï¼
# ââââââââââââââââââââââââââââââââââââââââ
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

# ââââââââââââââââââââââââââââââââââââââââ
# èªè¨¼ã¦ã¼ãã£ãªãã£
# ââââââââââââââââââââââââââââââââââââââââ
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
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db:   Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = int(payload.get("sub", 0))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="èªè¨¼ãã¼ã¯ã³ãç¡å¹ã§ã")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="ã¦ã¼ã¶ã¼ãè¦ã¤ããã¾ãã")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="ç®¡çèæ¨©éãå¿è¦ã§ã")
    return user

# ââââââââââââââââââââââââââââââââââââââââ
# ãªã¯ã¨ã¹ã/ã¬ã¹ãã³ã¹ ã¹ã­ã¼ã
# ââââââââââââââââââââââââââââââââââââââââ
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

# ââââââââââââââââââââââââââââââââââââââââ
# ãã«ãã¼
# ââââââââââââââââââââââââââââââââââââââââ
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

# ââââââââââââââââââââââââââââââââââââââââ
# FastAPI ã¢ããªã±ã¼ã·ã§ã³
# ââââââââââââââââââââââââââââââââââââââââ
app = FastAPI(
    title="ExFlow API",
    description="çµè²»ç®¡çã·ã¹ãã  REST API",
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

# ââââââââââââââââââââââââââââââââââââââââ
# èªè¨¼ã¨ã³ããã¤ã³ã
# ââââââââââââââââââââââââââââââââââââââââ
@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """ã­ã°ã¤ã³ â JWTãã¼ã¯ã³ãè¿ã"""
    user = db.query(User).filter(User.email == req.email, User.is_active == True).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="ã¡ã¼ã«ã¢ãã¬ã¹ã¾ãã¯ãã¹ã¯ã¼ããééã£ã¦ãã¾ã")
    return {
        "access_token": create_token(user.id),
        "token_type":   "bearer",
        "user": {
            "id": user.id, "name": user.name, "email": user.email,
            "department": user.department, "role": user.role
        }
    }

# ââââââââââââââââââââââââââââââââââââââââ
# ã¦ã¼ã¶ã¼
# ââââââââââââââââââââââââââââââââââââââââ
@app.get("/api/users/me")
def get_me(current: User = Depends(get_current_user)):
    return {"id": current.id, "name": current.name, "email": current.email,
            "department": current.department, "role": current.role}

@app.get("/api/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [{"id": u.id, "name": u.name, "department": u.department, "role": u.role}
            for u in db.query(User).filter(User.is_active == True).all()]

# ââââââââââââââââââââââââââââââââââââââââ
# çµè²»ç§ç®
# ââââââââââââââââââââââââââââââââââââââââ
@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [{"id": c.id, "code": c.code, "name": c.name}
            for c in db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()]

# ââââââââââââââââââââââââââââââââââââââââ
# çµè²» CRUD
# ââââââââââââââââââââââââââââââââââââââââ
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
    # æ¨©éãã£ã«ã¿ã¼ï¼ç¤¾å¡ã¯èªåã®çµè²»ã®ã¿ï¼
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
    if not e: raise HTTPException(404, "çµè²»ãè¦ã¤ããã¾ãã")
    if current.role != "admin" and e.user_id != current.id:
        raise HTTPException(403, "ã¢ã¯ã»ã¹æ¨©éãããã¾ãã")
    return expense_to_dict(e, db)

@app.put("/api/expenses/{expense_id}")
def update_expense(
    expense_id: int, req: ExpenseUpdate,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "çµè²»ãè¦ã¤ããã¾ãã")
    if e.user_id != current.id and current.role != "admin":
        raise HTTPException(403, "ã¢ã¯ã»ã¹æ¨©éãããã¾ãã")
    if e.status == "approved":
        raise HTTPException(400, "æ¿èªæ¸ã¿ã®çµè²»ã¯å¤æ´ã§ãã¾ãã")
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
    if not e: raise HTTPException(404, "çµè²»ãè¦ã¤ããã¾ãã")
    if e.user_id != current.id and current.role != "admin":
        raise HTTPException(403, "ã¢ã¯ã»ã¹æ¨©éãããã¾ãã")
    if e.status == "approved":
        raise HTTPException(400, "æ¿èªæ¸ã¿ã®çµè²»ã¯åé¤ã§ãã¾ãã")
    db.delete(e); db.commit()
    return {"message": "åé¤ãã¾ãã"}

@app.post("/api/expenses/{expense_id}/approve")
def approve_expense(expense_id: int, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "çµè²»ãè¦ã¤ããã¾ãã")
    e.status = "approved"; e.approved_by = current.id; e.approved_at = datetime.utcnow()
    db.commit(); db.refresh(e)
    return expense_to_dict(e, db)

@app.post("/api/expenses/{expense_id}/reject")
def reject_expense(expense_id: int, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "çµè²»ãè¦ã¤ããã¾ãã")
    e.status = "rejected"; e.approved_by = current.id; e.approved_at = datetime.utcnow()
    db.commit(); db.refresh(e)
    return expense_to_dict(e, db)

# ââââââââââââââââââââââââââââââââââââââââ
# åæã»éè¨
# ââââââââââââââââââââââââââââââââââââââââ
@app.get("/api/analytics/summary")
def analytics_summary(
    year: int = 2026, month: int = 2,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    """ããã·ã¥ãã¼ãç¨ãµããªã¼"""
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
    """æå¥æ¨ç§»ãã¼ã¿"""
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    all_exp = [e for e in q.all() if e.expense_date and e.expense_date.year == year]

    return [
        {
            "month": m, "label": f"{m}æ",
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
    """æ¥å¥æ¨ç§»ãã¼ã¿"""
    import calendar
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    ym      = f"{year}-{str(month).zfill(2)}"
    all_exp = [e for e in q.all() if e.expense_date and e.expense_date.isoformat()[:7] == ym]
    days    = calendar.monthrange(year, month)[1]

    return [
        {
            "day": d, "label": f"{d}æ¥",
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
    """ç§ç®å¥éè¨"""
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

# ââââââââââââââââââââââââââââââââââââââââ
# CSV ã¨ã¯ã¹ãã¼ã
# ââââââââââââââââââââââââââââââââââââââââ
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
    status_map  = {"approved": "æ¿èªæ¸ã¿", "pending": "æ¿èªå¾ã¡", "rejected": "å¦èª"}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["çµè²»ID","ç³è«è","é¨ç½²","çºçæ¥","ç§ç®","ç§ç®ã³ã¼ã","ä½¿ç¨å ´æ","éé¡ï¼åï¼","ã¹ãã¼ã¿ã¹","åè","ç»é²æ¥"])
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

    content = "\ufeff" + output.getvalue()   # BOMä»ãUTF-8ï¼Excelå¯¾å¿ï¼
    filename = f"expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ââââââââââââââââââââââââââââââââââââââââ
# LINE Webhook
# ââââââââââââââââââââââââââââââââââââââââ
@app.post("/api/line/webhook")
async def line_webhook(request: Request, db: Session = Depends(get_db)):
    """LINEå¬å¼ã¢ã«ã¦ã³ãããã®Webhookãåä¿¡"""
    body = await request.body()

    # ç½²åæ¤è¨¼ï¼LINE_CHANNEL_SECRETãè¨­å®ããã¦ããå ´åï¼
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

        # ç»åã»åç»ã¡ãã»ã¼ã¸ãåä¿¡
        if msg.get("type") in ("image", "video"):
            user = db.query(User).filter(User.line_user_id == line_uid).first()
            if user:
                # TODO: LINE Content APIããã¡ãã£ã¢ãåå¾ â S3ä¿å­ â Google Cloud Vision OCR
                # ç¾ç¶ã¯ç¢ºèªå¾ã¡ã®ãã¬ã¼ã¹ãã«ãã¼ã¨ãã¦ç»é²
                e = Expense(
                    user_id=user.id, amount=0, category_id=1,
                    expense_date=date.today(), status="pending",
                    note="â  LINEéä¿¡ã¬ã·ã¼ãï¼éé¡ã»ç§ç®ãç¢ºèªã»ä¿®æ­£ãã¦ãã ããï¼",
                    receipt_url=f"line-media://{msg.get('id')}"
                )
                db.add(e); db.commit()

    return {"status": "ok"}

# ââââââââââââââââââââââââââââââââââââââââ
# èµ·åæã®å¦çï¼DBåæå + ã·ã¼ããã¼ã¿æå¥ï¼
# ââââââââââââââââââââââââââââââââââââââââ
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            _seed(db)
            print("â åæãã¼ã¿ãæå¥ãã¾ãã")
    finally:
        db.close()

def _seed(db: Session):
    # すでにデータがある場合はスキップ
    if db.query(Category).first():
        return
    # ââ çµè²»ç§ç® ââ
    cats = [
        Category(code="EXP-001", name="äº¤éè²»",      sort_order=1),
        Category(code="EXP-002", name="å®¿æ³è²»",      sort_order=2),
        Category(code="EXP-003", name="ä¼è­°è²»",      sort_order=3),
        Category(code="EXP-004", name="æ¥å¾äº¤éè²»",  sort_order=4),
        Category(code="EXP-005", name="æ¶èåè²»",    sort_order=5),
        Category(code="EXP-006", name="éä¿¡è²»",      sort_order=6),
        Category(code="EXP-007", name="æ¸ç±ã»è³æè²»",sort_order=7),
        Category(code="EXP-008", name="ç ä¿®è²»",      sort_order=8),
        Category(code="EXP-009", name="æ¶å¼è²»",      sort_order=9),
        Category(code="EXP-010", name="ãã®ä»",      sort_order=10),
    ]
    for c in cats: db.add(c)
    db.commit()

    # ââ ã¦ã¼ã¶ã¼ ââ
    users_data = [
        ("ç°ä¸­ è±å­", "tanaka@example.com",  "password123", "å¶æ¥­é¨", "employee"),
        ("é´æ¨ ä¸é", "suzuki@example.com",  "password123", "ç·åé¨", "employee"),
        ("ä½è¤ æ¬¡é", "sato@example.com",    "password123", "æè¡é¨", "employee"),
        ("å±±ç° ç¤¾é·", "yamada@example.com",  "admin1234",   "çµå¶",   "admin"),
    ]
    for name, email, pw, dept, role in users_data:
        db.add(User(name=name, email=email, password_hash=hash_password(pw),
                    department=dept, role=role))
    db.commit()

    uid  = {u.email: u.id for u in db.query(User).all()}
    cid  = {c.code:  c.id for c in db.query(Category).all()}

    # ââ ãµã³ãã«çµè²»ãã¼ã¿ ââ
    samples = [
        # 2026/01 â æ¿èªæ¸ã¿
        (uid["tanaka@example.com"],  1840, cid["EXP-001"], "æ±äº¬ã¡ãã­",            date(2026,1,6),  "approved", "æ°å®¿âæ¸è°· å®¢åè¨ªå",      uid["yamada@example.com"], datetime(2026,1,7,9,0)),
        (uid["tanaka@example.com"],  5400, cid["EXP-003"], "ã¹ã¿ã¼ããã¯ã¹ æ°å®¿",    date(2026,1,8),  "approved", "ãã¼ã ä¼è­°è²»",             uid["yamada@example.com"], datetime(2026,1,9,9,0)),
        (uid["tanaka@example.com"], 15000, cid["EXP-004"], "éåº§ éæ¿ç¼ã å",       date(2026,1,10), "approved", "ABCåäºã¨ã®æ¥å¾",          uid["yamada@example.com"], datetime(2026,1,12,14,0)),
        (uid["suzuki@example.com"],  3500, cid["EXP-001"], "æ°å¹¹ç· æ±äº¬âåå¤å±",     date(2026,1,14), "approved", "åå¤å±åºå¼µ å¾è·¯",          uid["yamada@example.com"], datetime(2026,1,15,9,0)),
        (uid["suzuki@example.com"], 12000, cid["EXP-002"], "åå¤å± æ±æ¨ªã¤ã³",        date(2026,1,14), "approved", "åºå¼µå®¿æ³ 1æ³",             uid["yamada@example.com"], datetime(2026,1,15,9,0)),
        (uid["tanaka@example.com"],  2800, cid["EXP-005"], "ã¤ããé»æ© LABI",        date(2026,1,16), "approved", "USBããã»ã±ã¼ãã«é¡",      uid["yamada@example.com"], datetime(2026,1,17,10,0)),
        (uid["sato@example.com"],    8800, cid["EXP-008"], "Udemy",                  date(2026,1,20), "approved", "Pythonãã­ã°ã©ãã³ã°è¬åº§", uid["yamada@example.com"], datetime(2026,1,21,9,0)),
        (uid["tanaka@example.com"],   660, cid["EXP-006"], "NTTãã³ã¢",              date(2026,1,25), "approved", "æ¥­åç¨ã¹ããéä¿¡è²»ï¼1æï¼",uid["yamada@example.com"], datetime(2026,1,26,10,0)),
        (uid["suzuki@example.com"],  3200, cid["EXP-007"], "ç´ä¼åå±æ¸åº",            date(2026,1,28), "approved", "ãã¸ãã¹æ¸ 3å",           uid["yamada@example.com"], datetime(2026,1,29,9,0)),
        # 2026/02 â æ¿èªæ¸ã¿
        (uid["tanaka@example.com"],  2100, cid["EXP-001"], "æ±äº¬ã¡ãã­",              date(2026,2,3),  "approved", "å®¢åè¨ªåï¼æ± è¢ï¼",          uid["yamada@example.com"], datetime(2026,2,4,9,0)),
        (uid["tanaka@example.com"],  7500, cid["EXP-003"], "WeWork æ¸è°·",             date(2026,2,5),  "approved", "å¤é¨MTG ä¼è­°å®¤ä»£",          uid["yamada@example.com"], datetime(2026,2,6,9,0)),
        (uid["sato@example.com"],   22000, cid["EXP-004"], "å­æ¬æ¨ Restaurant XYZ",   date(2026,2,7),  "approved", "DEFæ ªå¼ä¼ç¤¾æ¥å¾",          uid["yamada@example.com"], datetime(2026,2,8,10,0)),
        (uid["suzuki@example.com"],  1650, cid["EXP-005"], "Amazon",                  date(2026,2,10), "approved", "ã³ãã¼ç¨ç´ï¼500æÃ2ï¼",    uid["yamada@example.com"], datetime(2026,2,11,9,0)),
        # 2026/02 â æ¿èªå¾ã¡
        (uid["tanaka@example.com"],  5800, cid["EXP-003"], "ããã¼ã« æ¸è°·åº",          date(2026,2,12), "pending",  "å¶æ¥­ãã¼ã MTG",    None, None),
        (uid["sato@example.com"],    1200, cid["EXP-006"], "SoftBank",                date(2026,2,13), "pending",  "æ¥­åç¨ã¹ããéä¿¡è²»ï¼2æï¼",None, None),
        (uid["tanaka@example.com"], 18000, cid["EXP-004"], "éº»å¸åçª åé£ ããã",     date(2026,2,15), "pending",  "GHIåäºæ¥å¾",     None, None),
        (uid["suzuki@example.com"],  4200, cid["EXP-001"], "æ°å¹¹ç· æ±äº¬âå¤§éª",        date(2026,2,17), "pending",  "å¤§éªåºå¼µ å¾è·¯",    None, None),
        (uid["tanaka@example.com"],   980, cid["EXP-007"], "Amazon",                  date(2026,2,18), "pending",  "æè¡æ¸ 1å",        None, None),
    ]
    for uid_, amt, cid_, loc, dt_, st, note, apid, apat in samples:
        db.add(Expense(user_id=uid_, amount=amt, category_id=cid_, location=loc,
                       expense_date=dt_, status=st, note=note,
                       approved_by=apid, approved_at=apat))
    db.commit()

# ââââââââââââââââââââââââââââââââââââââââ
# éçãã¡ã¤ã«éä¿¡ï¼ãã­ã³ãã¨ã³ãï¼
# ââââââââââââââââââââââââââââââââââââââââ
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# ââââââââââââââââââââââââââââââââââââââââ
# ã¨ã³ããªã¼ãã¤ã³ã
# ââââââââââââââââââââââââââââââââââââââââ
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
