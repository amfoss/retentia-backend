import os
from sqlite3 import IntegrityError

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Response, status
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app import crud
from app.dependencies import get_db
from app.schemas.user import (GoogleAuthRequest, GoogleCompleteProfile,
                              GoogleVerifiedResponse, LoginRequest, UserOut)
from app.utils.session import create_session

load_dotenv()
ENV = os.getenv("ENV", "development")
COOKIE_SECURE = ENV == "production"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

router = APIRouter(prefix="/auth", tags=["Users"])

def _set_session_cookie(response: Response, db: Session, user_id: int):
    session_id = create_session(db, user_id)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )

# Existing user
@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    _set_session_cookie(response, db, user.id)
    return user

# Google auth of a new user
@router.post("/google-verify", response_model=GoogleVerifiedResponse)
def google_verify(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    print("GOOGLE_CLIENT_ID:", GOOGLE_CLIENT_ID)

    try:
        idinfo = id_token.verify_oauth2_token(
            payload.token, requests.Request(), GOOGLE_CLIENT_ID
        )

    except (GoogleAuthError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    google_id = idinfo["sub"]

    if crud.get_user(db, google_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists. Please log in with your username and password.",
        )

    return GoogleVerifiedResponse(
        token=payload.token,
        email=idinfo["email"],
        name=idinfo.get("given_name") or idinfo.get("name", ""),
    )
        
@router.post("/complete-profile", response_model=UserOut)
def complete_profile(
    payload: GoogleCompleteProfile,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        idinfo = id_token.verify_oauth2_token(
            payload.token, requests.Request(), GOOGLE_CLIENT_ID
        )
    except (GoogleAuthError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    google_id = idinfo["sub"]
    email = idinfo["email"]
    name = idinfo.get("given_name") or idinfo.get("name", "")

    if crud.get_user(db, google_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists. Please log in.",
        )

    try:
        user = crud.create_google_user(
            db=db,
            google_id=google_id,
            email=email,
            name=name,
            username=payload.username,
            password=payload.password,
            grade=payload.grade,
            institute=payload.institute,
            city=payload.city,
            marketing=payload.marketing,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already taken.",
        )

    _set_session_cookie(response, db, user.id)
    return user
        