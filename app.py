import sqlite3
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import FastAPI, Depends, HTTPException, Header

app = FastAPI()

# ===== 配置 =====
SECRET_KEY = "Zovoejxlo_yt"   # 签名 JWT 的密钥，生产环境必须换成随机值
TOKEN_EXPIRE_MINUTES = 24 * 60                # 登录令牌有效期
DB_PATH = "app.db"                       # SQLite 数据库文件

# ===== 数据库 =====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    # 预置一个演示账号 Qs1r / Zjx123456
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        password_hash = bcrypt.hashpw(b"Zjx123456", bcrypt.gensalt())
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                     ("Qs1r", password_hash))
    conn.commit()
    conn.close()

init_db()



from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
def login(req: LoginRequest):
    # 1. 用参数化查询找用户 (防 SQLi)
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (req.username,),
    ).fetchone()
    conn.close()

    # 2. 用户不存在或密码不对, 统一返回 401
    if row is None or not bcrypt.checkpw(req.password.encode("utf-8"), row[2]):
        return {"error": "用户名或密码错误"}

    # 3. 签发 JWT
    payload = {
        "sub": str(row[0]),                    # 用户ID
        "username": row[1],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return {"token": token, "token_type": "Bearer"}


# ===== JWT 校验关卡 =====
def get_current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少令牌")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效令牌")

# ===== 接口 2: 受保护的数据接口 =====
@app.get("/api/data")
def get_data(user: dict = Depends(get_current_user)):
    return {"data": [{"id": user["sub"], "username": user["username"]}],
            "message": "认证成功, 已返回数据"}

# ===== 接口 3: 个人资料接口 (自选接口) =====
@app.get("/api/profile")
def get_profile(user: dict = Depends(get_current_user)):
    return {"profile": {"id": user["sub"], "username": user["username"],
                        "member_since": "2026-10-19"}}
