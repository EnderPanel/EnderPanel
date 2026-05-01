from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import pyotp
import qrcode
import io
import base64
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from models.user import User
from utils.security import (
    clear_auth_cookie,
    create_access_token,
    get_current_user,
    hash_password,
    is_legacy_password_hash,
    set_auth_cookie,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=8, max_length=128)

def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "avatar": f"/api/avatars/{user.avatar}" if user.avatar else None,
        "totp_enabled": bool(user.totp_secret)
    }

@router.post("/register")
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    is_first_user = db.query(User).count() == 0

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        is_admin=is_first_user
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = create_access_token({"sub": db_user.username})
    set_auth_cookie(response, token)
    return {"access_token": token, "token_type": "bearer", "user": user_to_dict(db_user)}

@router.post("/login")
@limiter.limit("10/minute")
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    totp_code: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    if is_legacy_password_hash(user.hashed_password):
        user.hashed_password = hash_password(form_data.password)
        db.commit()
        db.refresh(user)

    if user.totp_secret:
        if not totp_code:
            raise HTTPException(status_code=401, detail="totp_required")
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(totp_code):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    token = create_access_token({"sub": user.username})
    set_auth_cookie(response, token)
    return {"access_token": token, "token_type": "bearer", "user": user_to_dict(user)}


@router.post("/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"success": True}

@router.get("/2fa/generate")
def generate_2fa(current_user: User = Depends(get_current_user)):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.username, issuer_name="EnderPanel")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{img_str}"
    }

class Enable2FA(BaseModel):
    secret: str
    code: str

@router.post("/2fa/enable")
def enable_2fa(data: Enable2FA, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    totp = pyotp.TOTP(data.secret)
    if not totp.verify(data.code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
    current_user.totp_secret = data.secret
    db.commit()
    return {"success": True}

class Disable2FA(BaseModel):
    password: str

@router.post("/2fa/disable")
def disable_2fa(data: Disable2FA, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
        
    current_user.totp_secret = None
    db.commit()
    return {"success": True}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return user_to_dict(current_user)
