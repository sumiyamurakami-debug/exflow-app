"""
ExFlow - 経費管理システム バックエンド
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

# ════════════════════════════════════════
# 設定
# ════════════════════════════════════════
SECRET_KEY        = os.getenv("SECRET_KEY", "expflow-secret-please-change-in-production")
DATABASE_URL      = os.getenv("DATABASE_URL", "sqlite:///./expflow.db")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_TOKEN  = os.getenv("LINE_CHANNEL_TOKEN", "")

# ════════════════════════════════════════
# データベース
# ════════════════════════════════════════
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

# ════════════════════════════════════════
# モデル（データベーステーブル定義）
# ════════════════════════════════════════
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

# ════════════════════════════════════════
# 認証ユーティリティ
# ════════════════════════════════════════
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
        raise HTTPException(status_code=401, detail="認証トークンが無効です")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="ユーザーが見つかりません")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    return user

# ════════════════════════════════════════
# リクエスト/レスポンス スキーマ
# ════════════════════════════════════════
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

# ════════════════════════════════════════
# ヘルパー
# ════════════════════════════════════════
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

# ════════════════════════════════════════
# FastAPI アプリケーション
# ════════════════════════════════════════
app = FastAPI(
    title="ExFlow API",
    description="経費管理システム REST API",
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

# ────────────────────────────────────────
# 認証エンドポイント
# ────────────────────────────────────────
@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """ログイン → JWTトークンを返す"""
    user = db.query(User).filter(User.email == req.email, User.is_active == True).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが間違っています")
    return {
        "access_token": create_token(user.id),
        "token_type":   "bearer",
        "user": {
            "id": user.id, "name": user.name, "email": user.email,
            "department": user.department, "role": user.role
        }
    }

# ────────────────────────────────────────
# ユーザー
# ────────────────────────────────────────
@app.get("/api/users/me")
def get_me(current: User = Depends(get_current_user)):
    return {"id": current.id, "name": current.name, "email": current.email,
            "department": current.department, "role": current.role}

@app.get("/api/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [{"id": u.id, "name": u.name, "department": u.department, "role": u.role}
            for u in db.query(User).filter(User.is_active == True).all()]

# ────────────────────────────────────────
# 経費科目
# ────────────────────────────────────────
@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [{"id": c.id, "code": c.code, "name": c.name}
            for c in db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()]

# ────────────────────────────────────────
# 経費 CRUD
# ────────────────────────────────────────
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
    # 権限フィルター（社員は自分の経費のみ）
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
    if not e: raise HTTPException(404, "経費が見つかりません")
    if current.role != "admin" and e.user_id != current.id:
        raise HTTPException(403, "アクセス権限がありません")
    return expense_to_dict(e, db)

@app.put("/api/expenses/{expense_id}")
def update_expense(
    expense_id: int, req: ExpenseUpdate,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "経費が見つかりません")
    if e.user_id != current.id and current.role != "admin":
        raise HTTPException(403, "アクセス権限がありません")
    if e.status == "approved":
        raise HTTPException(400, "承認済みの経費は変更できません")
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
    if not e: raise HTTPException(404, "経費が見つかりません")
    if e.user_id != current.id and current.role != "admin":
        raise HTTPException(403, "アクセス権限がありません")
    if e.status == "approved":
        raise HTTPException(400, "承認済みの経費は削除できません")
    db.delete(e); db.commit()
    return {"message": "削除しました"}

@app.post("/api/expenses/{expense_id}/approve")
def approve_expense(expense_id: int, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "経費が見つかりません")
    e.status = "approved"; e.approved_by = current.id; e.approved_at = datetime.utcnow()
    db.commit(); db.refresh(e)
    return expense_to_dict(e, db)

@app.post("/api/expenses/{expense_id}/reject")
def reject_expense(expense_id: int, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    e = db.query(Expense).filter(Expense.id == expense_id).first()
    if not e: raise HTTPException(404, "経費が見つかりません")
    e.status = "rejected"; e.approved_by = current.id; e.approved_at = datetime.utcnow()
    db.commit(); db.refresh(e)
    return expense_to_dict(e, db)

# ────────────────────────────────────────
# 分析・集計
# ────────────────────────────────────────
@app.get("/api/analytics/summary")
def analytics_summary(
    year: int = 2026, month: int = 2,
    db: Session = Depends(get_db), current: User = Depends(get_current_user)
):
    """ダッシュボード用サマリー"""
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
    """月別推移データ"""
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    all_exp = [e for e in q.all() if e.expense_date and e.expense_date.year == year]

    return [
        {
            "month": m, "label": f"{m}月",
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
    """日別推移データ"""
    import calendar
    q = db.query(Expense)
    if current.role != "admin":
        q = q.filter(Expense.user_id == current.id)
    ym      = f"{year}-{str(month).zfill(2)}"
    all_exp = [e for e in q.all() if e.expense_date and e.expense_date.isoformat()[:7] == ym]
    days    = calendar.monthrange(year, month)[1]

    return [
        {
            "day": d, "label": f"{d}日",
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
    """科目別集計"""
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

# ────────────────────────────────────────
# CSV エクスポート
# ────────────────────────────────────────
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
    status_map  = {"approved": "承認済み", "pending": "承認待ち", "rejected": "否認"}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["経費ID","申請者","部署","発生日","科目","科目コード","使用場所","金額（円）","ステータス","備考","登録日"])
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

    content = "\ufeff" + output.getvalue()   # BOM付きUTF-8（Excel対応）
    filename = f"expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ────────────────────────────────────────
# LINE Webhook
# ────────────────────────────────────────
@app.post("/api/line/webhook")
async def line_webhook(request: Request, db: Session = Depends(get_db)):
    """LINE公式アカウントからのWebhookを受信"""
    body = await request.body()

    # 署名検証（LINE_CHANNEL_SECRETが設定されている場合）
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

        # 画像・動画メッセージを受信
        if msg.get("type") in ("image", "video"):
            user = db.query(User).filter(User.line_user_id == line_uid).first()
            if user:
                # TODO: LINE Content APIからメディアを取得 → S3保存 → Google Cloud Vision OCR
                # 現状は確認待ちのプレースホルダーとして登録
                e = Expense(
                    user_id=user.id, amount=0, category_id=1,
                    expense_date=date.today(), status="pending",
                    note="⚠ LINE送信レシート（金額・科目を確認・修正してください）",
                    receipt_url=f"line-media://{msg.get('id')}"
                )
                db.add(e); db.commit()

    return {"status": "ok"}

# ════════════════════════════════════════
# 起動時の処理（DB初期化 + シードデータ投入）
# ════════════════════════════════════════
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            _seed(db)
            print("✅ 初期データを投入しました")
    finally:
        db.close()

def _seed(db: Session):
    # ── 経費科目 ──
    cats = [
        Category(code="EXP-001", name="交通費",      sort_order=1),
        Category(code="EXP-002", name="宿泊費",      sort_order=2),
        Category(code="EXP-003", name="会議費",      sort_order=3),
        Category(code="EXP-004", name="接待交際費",  sort_order=4),
        Category(code="EXP-005", name="消耗品費",    sort_order=5),
        Category(code="EXP-006", name="通信費",      sort_order=6),
        Category(code="EXP-007", name="書籍・資料費",sort_order=7),
        Category(code="EXP-008", name="研修費",      sort_order=8),
        Category(code="EXP-009", name="慶弔費",      sort_order=9),
        Category(code="EXP-010", name="その他",      sort_order=10),
    ]
    for c in cats: db.add(c)
    db.commit()

    # ── ユーザー ──
    users_data = [
        ("田中 花子", "tanaka@example.com",  "password123", "営業部", "employee"),
        ("鈴木 一郎", "suzuki@example.com",  "password123", "総務部", "employee"),
        ("佐藤 次郎", "sato@example.com",    "password123", "技術部", "employee"),
        ("山田 社長", "yamada@example.com",  "admin1234",   "経営",   "admin"),
    ]
    for name, email, pw, dept, role in users_data:
        db.add(User(name=name, email=email, password_hash=hash_password(pw),
                    department=dept, role=role))
    db.commit()

    uid  = {u.email: u.id for u in db.query(User).all()}
    cid  = {c.code:  c.id for c in db.query(Category).all()}

    # ── サンプル経費データ ──
    samples = [
        # 2026/01 – 承認済み
        (uid["tanaka@example.com"],  1840, cid["EXP-001"], "東京メトロ",            date(2026,1,6),  "approved", "新宿→渋谷 客先訪問",      uid["yamada@example.com"], datetime(2026,1,7,9,0)),
        (uid["tanaka@example.com"],  5400, cid["EXP-003"], "スターバックス 新宿",    date(2026,1,8),  "approved", "チーム会議費",             uid["yamada@example.com"], datetime(2026,1,9,9,0)),
        (uid["tanaka@example.com"], 15000, cid["EXP-004"], "銀座 鉄板焼き 光",       date(2026,1,10), "approved", "ABC商事との接待",          uid["yamada@example.com"], datetime(2026,1,12,14,0)),
        (uid["suzuki@example.com"],  3500, cid["EXP-001"], "新幹線 東京→名古屋",     date(2026,1,14), "approved", "名古屋出張 往路",          uid["yamada@example.com"], datetime(2026,1,15,9,0)),
        (uid["suzuki@example.com"], 12000, cid["EXP-002"], "名古屋 東横イン",        date(2026,1,14), "approved", "出張宿泊 1泊",             uid["yamada@example.com"], datetime(2026,1,15,9,0)),
        (uid["tanaka@example.com"],  2800, cid["EXP-005"], "ヤマダ電機 LABI",        date(2026,1,16), "approved", "USBハブ・ケーブル類",      uid["yamada@example.com"], datetime(2026,1,17,10,0)),
        (uid["sato@example.com"],    8800, cid["EXP-008"], "Udemy",                  date(2026,1,20), "approved", "Pythonプログラミング講座", uid["yamada@example.com"], datetime(2026,1,21,9,0)),
        (uid["tanaka@example.com"],   660, cid["EXP-006"], "NTTドコモ",              date(2026,1,25), "approved", "業務用スマホ通信費（1月）",uid["yamada@example.com"], datetime(2026,1,26,10,0)),
        (uid["suzuki@example.com"],  3200, cid["EXP-007"], "紀伊國屋書店",            date(2026,1,28), "approved", "ビジネス書 3冊",           uid["yamada@example.com"], datetime(2026,1,29,9,0)),
        # 2026/02 – 承認済み
        (uid["tanaka@example.com"],  2100, cid["EXP-001"], "東京メトロ",              date(2026,2,3),  "approved", "客先訪問（池袋）",          uid["yamada@example.com"], datetime(2026,2,4,9,0)),
        (uid["tanaka@example.com"],  7500, cid["EXP-003"], "WeWork 渋谷",             date(2026,2,5),  "approved", "外部MTG 会議室代",          uid["yamada@example.com"], datetime(2026,2,6,9,0)),
        (uid["sato@example.com"],   22000, cid["EXP-004"], "六本木 Restaurant XYZ",   date(2026,2,7),  "approved", "DEF株式会社接待",          uid["yamada@example.com"], datetime(2026,2,8,10,0)),
        (uid["suzuki@example.com"],  1650, cid["EXP-005"], "Amazon",                  date(2026,2,10), "approved", "コピー用紙（500枚×2）",    uid["yamada@example.com"], datetime(2026,2,11,9,0)),
        # 2026/02 – 承認待ち
        (uid["tanaka@example.com"],  5800, cid["EXP-003"], "ドトール 渋谷店",          date(2026,2,12), "pending",  "営業チームMTG",    None, None),
        (uid["sato@example.com"],    1200, cid["EXP-006"], "SoftBank",                date(2026,2,13), "pending",  "業務用スマホ通信費（2月）",None, None),
        (uid["tanaka@example.com"], 18000, cid["EXP-004"], "麻布十番 和食 さくら",     date(2026,2,15), "pending",  "GHI商事接待",     None, None),
        (uid["suzuki@example.com"],  4200, cid["EXP-001"], "新幹線 東京→大阪",        date(2026,2,17), "pending",  "大阪出張 往路",    None, None),
        (uid["tanaka@example.com"],   980, cid["EXP-007"], "Amazon",                  date(2026,2,18), "pending",  "技術書 1冊",        None, None),
    ]
    for uid_, amt, cid_, loc, dt_, st, note, apid, apat in samples:
        db.add(Expense(user_id=uid_, amount=amt, category_id=cid_, location=loc,
                       expense_date=dt_, status=st, note=note,
                       approved_by=apid, approved_at=apat))
    db.commit()

# ════════════════════════════════════════
# 静的ファイル配信（フロントエンド）
# ════════════════════════════════════════
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# ════════════════════════════════════════
# エントリーポイント
# ════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
