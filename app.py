import sqlite3
from datetime import datetime, timedelta, timezone

import html
import bcrypt
import jwt
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()

# ===== Health Check =====
@app.get("/health")
def health():
    """Basic health check endpoint used to verify the service is running."""
    return {"status": "ok"}

# ===== Configuration =====
SECRET_KEY = "Zovoejxlo_yt"   # Key used to sign JWTs; MUST be replaced with a random value in production
TOKEN_EXPIRE_MINUTES = 24 * 60                # Login token lifetime
DB_PATH = "app.db"                       # SQLite database file

# ===== Database =====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    # Seed a demo account Qs1r / Zjx123456
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
    # 1. Look up the user with a parameterized query (prevents SQL injection)
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (req.username,),
    ).fetchone()
    conn.close()

    # 2. If the user does not exist or the password is wrong, return 401 uniformly
    if row is None or not bcrypt.checkpw(req.password.encode("utf-8"), row[2]):
        return {"error": "Invalid username or password"}

    # 3. Issue a JWT
    payload = {
        "sub": str(row[0]),                    # User ID
        "username": row[1],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return {"token": token, "token_type": "Bearer"}


# ===== JWT Validation Gate =====
# HTTPBearer security scheme so that Swagger UI exposes an "Authorize" button
# and always forwards the Authorization header with the request.
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing token")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ===== Endpoint 2: Protected data endpoint =====
@app.get("/api/data")
def get_data(user: dict = Depends(get_current_user)):
    return {"data": [{"id": user["sub"], "username": html.escape(user["username"])}],
            "message": "Authentication successful, data returned"}

# ===== Endpoint 3: Profile endpoint (self-selected) =====
@app.get("/api/profile")
def get_profile(user: dict = Depends(get_current_user)):
    return {"profile": {"id": user["sub"], "username": html.escape(user["username"]),
                        "member_since": "2026-10-19"}}
