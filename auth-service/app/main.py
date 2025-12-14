from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
import logging
import os
from app.database import SessionLocal, engine
from app.models import Base, User
from app.schemas import UserCreate, Token
from app.auth import hash_password, verify_password, create_access_token
from app.oauth import oauth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Ensure SessionMiddleware is installed so authlib (oauth) can use request.session
SESSION_SECRET = os.getenv("SESSION_SECRET_KEY", os.getenv("SECRET_KEY", "change-me-in-prod"))
# Development-friendly cookie settings (use stricter settings in production)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    https_only=False,        # set True in production on HTTPS
    same_site="lax",         # allows OAuth provider GET redirect to send cookie
    session_cookie="session" # optional explicit cookie name
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

## Sign-up / Create user
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User exists")

    new_user = User(
        username=user.username,
        hashed_password=hash_password(user.password),
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created", "id": new_user.id}

## Login
@app.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.username, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}

# OAuth: start Google login (redirects to provider)
@app.get("/login/google")
async def login_google(request: Request):
    logger.info("Session before authorize_redirect: %s", dict(request.session))
    redirect_uri = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, str(redirect_uri))

# OAuth callback - exchange code, create/find local user and return access token
@app.get("/auth/google")
async def auth_google(request: Request, db: Session = Depends(get_db)):
    # Diagnostic logs to debug mismatching_state CSRF errors
    logger.info("Session at callback start: %s", dict(request.session))
    logger.info("Callback query params: %s", dict(request.query_params))
    logger.info("Callback cookies: %s", dict(request.cookies))
    # list session keys so you can see stored _state keys
    logger.info("Session keys: %s", list(request.session.keys()))
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as ex:
        logger.exception("authorize_access_token failed")
        raise HTTPException(status_code=400, detail="OAuth exchange failed")

    # Try to get userinfo: prefer ID token parsing for OIDC, fallback to userinfo endpoint
    userinfo = None
    try:
        userinfo = await oauth.google.parse_id_token(request, token)
    except Exception:
        try:
            userinfo = await oauth.google.userinfo(token=token)
        except Exception:
            userinfo = token.get("userinfo") or {}

    logger.info("Userinfo from provider: %s", userinfo)

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email returned from provider")

    user = db.query(User).filter(User.username == email).first()
    if not user:
        user = User(username=email, hashed_password=hash_password(""), role="user")
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}