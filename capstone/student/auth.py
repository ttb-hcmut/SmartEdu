"""
student/auth.py
───────────────
Description shall be fullfilled soon !
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../core/.env"))

_SECRET_KEY: str = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION99292ee29e2923iu3uibfui3bfiu")
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/student/login")


class User(BaseModel):
    id: str
    username: str
    name: Optional[str] = None
    email: Optional[str] = None


def create_access_token(student_id: str, extra: Optional[dict] = None) -> str:
    """Mint a JWT using PyJWT."""
    exp = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": student_id,
        "exp": exp,
    }
    if extra:
        payload.update(extra)
        
    encoded_jwt = jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    return encoded_jwt


def get_current_student(request: Request, token: str = Depends(oauth2_scheme)) -> User:
    """Validate token and return User object. Raises HTTPException on failure."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode payload using PyJWT
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        student_id: str = payload.get("sub")
        if student_id is None:
            raise credentials_exc
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exc
        
    # Get database instance
    tracker = request.app.state.student_tracker
    sql = tracker.sqldb
    
    # Query student profile
    student_profile = sql.get_student_by_id(student_id)
    if not student_profile:
        raise credentials_exc
        
    return User(**student_profile)
