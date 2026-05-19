from dataclasses import dataclass, field
from typing import Any, Callable, List, Dict



@dataclass
class Memo:
    state_key: str = "memo"
    history_len: int = 5 
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

    def get_formatted_history(self, mode: str = "full") -> str:
        if not self.session_history:
            return "No prior context."
            
        formatted_lines = []
        if mode == "skim":
            last_ta_idx = -1
            for i, entry in enumerate(self.session_history):
                if entry.get("role") != "student":
                    last_ta_idx = i
                    
            for idx, entry in enumerate(self.session_history, 1):
                role = entry.get("role", "unknown")
                if role == "student":
                    message = entry.get("message", "N/A")
                    formatted_lines.append(f"[{idx}] Student: {message}")
                elif (idx - 1) == last_ta_idx:
                    heading = entry.get("heading", "")
                    formatted_lines.append(f"[{idx}] TA: {heading}")
        else:
            for idx, entry in enumerate(self.session_history, 1):
                role = entry.get("role", "unknown")
                message = entry.get("message", "N/A")
                heading = entry.get("heading", "")
                
                if role == "student":
                    formatted_lines.append(f"[{idx}] Student: {message}")
                else:
                    formatted_lines.append(f"[{idx}] TA: {heading}")
            
        return "\n".join(formatted_lines)


