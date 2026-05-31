from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import time
import os
from uuid_v7.base import uuid7

def generate_uuidv7() -> str:
    return str(uuid7())

class ChatMessage(BaseModel):
    role: str
    heading: str
    message: str
    timestamp: str

class Chat(BaseModel):
    id: str = Field(default_factory=generate_uuidv7)
    invoke: str = ""
    messages: List[ChatMessage] = Field(default_factory=list)

class Session(BaseModel):
    id: str = Field(default_factory=generate_uuidv7)
    name: str = "New Session"
    chats: List[Chat] = Field(default_factory=list)

class Memo:
    def __init__(self, session_id: str, session_data: Optional[Dict] = None, save_callback: Optional[Callable] = None):
        self.session_id = session_id
        self.save_callback = save_callback
        if session_data:
            self.session = Session(**session_data)
        else:
            self.session = Session(id=session_id)

    def get_formatted_history(self, mode: str = "full") -> str:
        if not self.session.chats:
            return "No prior context."
            
        formatted_lines = []
        for chat in self.session.chats:
            for msg in chat.messages:
                if msg.role == "student":
                    formatted_lines.append(f"Student: {msg.message}")
                elif msg.role == "TA":
                    if mode == "skim":
                        formatted_lines.append(f"TA: {msg.heading}")
                    else:
                        formatted_lines.append(f"TA: {msg.message}")
                        
        return "\n".join(formatted_lines)
