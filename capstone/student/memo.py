from dataclasses import dataclass, field
from typing import Any, Callable, List, Dict



@dataclass
class Memo:
    state_key: str = "memo"
    history_len: int = 6 
    session_history: List[Dict] = field(default_factory=list) 
    save_callback: Callable = None
    session_id: str = "default"

    async def save(self, entry: Dict) -> None:
        message = entry.get("message", "")
        heading = entry.get("heading", "")
        if not message or not heading:
            return
            
        self.session_history.append(entry)
        if len(self.session_history) > self.history_len:
            self.session_history.pop(0) 
        
        if self.save_callback:
            self.save_callback(entry, self.session_id)

    def get_formatted_history(self) -> str:
        if not self.session_history:
            return "No prior context."
            
        formatted_lines = []
        for idx, entry in enumerate(self.session_history, 1):
            role = entry.get("role", "unknown")
            message = entry.get("message", "N/A")
            heading = entry.get("heading", "")
            
            if role == "student":
                formatted_lines.append(f"[{idx}] Student: {message}")
            else:
                formatted_lines.append(f"[{idx}] TA: {heading}")
            
        return "\n".join(formatted_lines)


class StudentSession:
    def __init__(self, student_id: str, student_state: StudentState, memo: Memo):
        self.student_id = student_id
        self.student_state = student_state
        self.recent_pages: deque = deque(maxlen=5)
        self.memo = memo