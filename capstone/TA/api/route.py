from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from student.auth import get_current_student, User

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str      # Chat Session UUID — opaque, issued by POST /student/session/start
    user_input: str


class ChatResponse(BaseModel):
    message: str
    ui_action: dict | None = None


def _get_session_id(payload: ChatRequest, request: Request, current_student: User) -> str:
    """
    Verify that the Bearer token's student_id owns this session_id.
    This prevents a student from hijacking another student's session.
    """
    tracker = request.app.state.student_tracker
    owner = tracker.get_student_id_by_session(payload.session_id)
    if owner is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Call POST /student/session/start first.",
        )
    if owner != current_student.id:
        raise HTTPException(status_code=403, detail="Session does not belong to this token.")

    return payload.session_id


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ta(request: Request, payload: ChatRequest, current_student: User = Depends(get_current_student)):
    """
    Chat endpoint.
    - Requires Bearer JWT in Authorization header.
    - Requires a valid session_id previously issued by /student/session/start.
    - student_id is NEVER exposed to the TA module.
    """
    try:
        # Validate ownership
        session_id = _get_session_id(payload, request, current_student)

        ta_module = request.app.state.TA
        if not ta_module:
            raise HTTPException(status_code=500, detail="TAModule is not initialized.")

        result = await ta_module.run(
            user_input=payload.user_input,
            session_id=session_id,
        )
        return ChatResponse(message=result["message"], ui_action=result.get("ui_action"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
