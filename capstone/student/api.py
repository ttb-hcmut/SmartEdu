"""
student/api.py
──────────────
Student-facing REST endpoints:
  POST /register         → tạo account mới
  POST /login            → trả về JWT Access Token
  POST /session/start    → (Authenticated) Khởi tạo/lấy chat session, trả về session_id
  DELETE /session/end    → (Authenticated) Hủy chat session hiện tại khỏi memory

Flow chuẩn OAuth-like:
  Client ──── POST /login ────► Backend ──── JWT(student_id) ────► Client
  Client ──── POST /session/start [Bearer JWT] ─► Backend ──── session_id ──► Client
  Client ──── POST /ta/chat [session_id] ────────────────────────────────────► TA
"""

import uuid
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from student.auth import create_access_token, get_current_student, User

router = APIRouter(tags=["Student Auth"])


################## Request / Response schemas
class RegisterRequest(BaseModel):
    student_id: str          # e.g. "s123" or UUID — caller decides
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SessionResponse(BaseModel):
    session_id: str          # UUID, opaque to the caller


################## Endpoints
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: Request, payload: RegisterRequest):
    """
    Create a new student account.
    Stores hashed password in SQL; creates Mongo document for state.
    """
    tracker = request.app.state.student_tracker
    sql = tracker.sqldb
    mongo = tracker.mongodb

    if sql.get_student_by_id(payload.student_id) is not False:
        raise HTTPException(status_code=409, detail="Student ID already exists.")

    sql.create_student(student_id=payload.student_id, username=payload.student_id, password=payload.password)
    mongo.create_student(payload.student_id)
    return {"detail": "Registered successfully."}


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login.
    Uses SQL_DB's built-in SHA256 authenticate method.
    """
    tracker = request.app.state.student_tracker
    sql = tracker.sqldb

    if not sql.authenticate(username=form_data.username, password=form_data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = create_access_token(form_data.username)
    return TokenResponse(access_token=token)


@router.post("/session/start", response_model=SessionResponse)
async def start_session(
    request: Request,
    current_student: User = Depends(get_current_student),
):
    """
    (Authenticated) Allocate a new Chat Session ID and register it in the tracker.
    Returns the session_id the client should use when calling /ta/chat.
    """
    tracker = request.app.state.student_tracker
    session_id = str(uuid.uuid4())
    tracker.create_chat_session(student_id=current_student.id, session_id=session_id)
    return SessionResponse(session_id=session_id)


@router.delete("/session/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(
    session_id: str,
    request: Request,
    current_student: User = Depends(get_current_student),
):
    """
    (Authenticated) Drop a specific chat session from in-memory tracker.
    Student can only drop their own sessions.
    """
    tracker = request.app.state.student_tracker
    # Verify ownership before dropping
    owner = tracker.get_student_id_by_session(session_id)
    if owner != current_student.id:
        raise HTTPException(status_code=403, detail="Session does not belong to this student.")
    tracker.drop_session(session_id)
