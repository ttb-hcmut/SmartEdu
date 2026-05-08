from collections import deque
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.repo.graph.graphdb import GraphDB
from core.repo.sql.sql_db import SQL_DB
from core.repo.nosql.mongo_db import Mongo_DB
from core.schema.wf_state import ConceptNode, StudentState, LearningProposal
from student.memo import *

NONE_LENGTH = 20


class Page(BaseModel):
    path: str = Field(exclude=True)
    page: int
    concept: List[str] = Field(default_factory=list)
    content: str = ""

    def __str__(self):
        return f"Page {self.page}: {self.content[:50]}... Concepts: {self.concept}"


class Student_Tracker:
    """
    Student state, learning progress mangament.
    Called by tools (in considerationsd )
    """

    def __init__(self, graphdb: GraphDB, sqldb: SQL_DB, mongodb: Mongo_DB):
        self.graphdb = graphdb
        self.sqldb = sqldb
        self.mongodb = mongodb

        self._sessions: Dict[str, StudentSession] = {}

        self._session_map: Dict[str, str] = {}   # session_id -> student_id

    ################ Chat Session lifecycle ( student/api.py)

    def create_chat_session(self, student_id: str, session_id: str) -> None:
        """
        Đăng ký một Chat Session UUID mới cho student_id.
        Gọi sau khi student đã login thành công và muốn bắt đầu hội thoại mới.
        """
        self._session_map[session_id] = student_id
        # Pre-warm the student session in memory
        self._get_or_create_student_session(student_id, session_id)

    def get_student_id_by_session(self, session_id: str) -> Optional[str]:
        """Trả về student_id tương ứng với session_id, hoặc None nếu không tồn tại."""
        return self._session_map.get(session_id)

    def drop_session(self, session_id: str) -> None:
        """
        Hủy Chat Session: xóa mapping và xóa state khỏi bộ nhớ.
        Student_id vẫn giữ nguyên trong DB.
        """
        student_id = self._session_map.pop(session_id, None)
        if student_id:
            self._sessions.pop(student_id, None)



    def get_session(self, session_id: str) -> "StudentSession":
        """
        Lấy StudentSession theo Chat Session ID.
        Dùng bởi module TA — không yêu cầu student_id.
        Raise ValueError nếu session_id chưa được đăng ký.
        """
        student_id = self._resolve(session_id)
        return self._get_or_create_student_session(student_id, session_id)

    def get_student_state(self, session_id: str) -> StudentState:
        return self.get_session(session_id).student_state

    def get_chat_history(self, session_id: str) -> str:
        return self.get_session(session_id).memo.get_formatted_history()

    def get_mastery(self, session_id: str, node_name: str) -> int:
        student_id = self._resolve(session_id)
        return self.graphdb.get_mastery(student_id, node_name)

    def save_state(self, session_id: str) -> None:
        student_id = self._resolve(session_id)
        session = self._sessions[student_id]
        self.mongodb.update_student_state(student_id, session.student_state)

    def get_road_map(self, session_id: str) -> Dict:
        student_id = self._resolve(session_id)
        return self.graphdb.get_learning_graph(student_id)

    def update_learning_position(
        self, session_id: str, new_node: ConceptNode, bridge_nodes: list = None
    ):
        student_id = self._resolve(session_id)
        session = self._get_or_create_student_session(student_id, session_id)
        state = session.student_state

        if bridge_nodes:
            valid_bridge = bridge_nodes[:3]
            current_upcoming = state.get("upcoming_nodes", [])
            state["upcoming_nodes"] = valid_bridge + current_upcoming

        current_pos = state.get("current_pos")

        if current_pos and current_pos.name == new_node.name:
            self.save_state(session_id)
            return

        if current_pos is not None:
            prev = state.get("previous_nodes", [])
            prev.insert(0, current_pos)
            state["previous_nodes"] = prev[:NONE_LENGTH]

        self.graphdb.update_learn(student_id, current_pos, new_node)
        state["current_pos"] = new_node
        self._on_node_change(session)
        self.save_state(session_id)

    def current_resource(self, session_id: str, n: int = 3) -> List[Page]:
        return list(self.get_session(session_id).recent_pages)[-n:]

    def add_recent_page(self, session_id: str, page: Page) -> None:
        self.get_session(session_id).recent_pages.append(page)

    def apply_proposal(self, session_id: str, proposal_dict: Dict[str, Any]) -> None:
        proposal = LearningProposal(**proposal_dict)
        session = self.get_session(session_id)
        state = session.student_state

        if proposal.new_upcoming:
            state["upcoming_nodes"] = proposal.new_upcoming

        if proposal.new_current:
            self.update_learning_position(session_id, proposal.new_current)

        self._rebuild_context(session, proposal)
        state["pending_proposal"] = None
        self.save_state(session_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Admin / internal helpers (dùng trực tiếp student_id)
    # ──────────────────────────────────────────────────────────────────────────

    def get_student_profile(self, student_id: str):
        """Dùng từ student/api.py, không dùng từ TA."""
        return self.sqldb.get_student_by_id(student_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _resolve(self, session_id: str) -> str:
        """Map session_id → student_id. Raise 401-like ValueError nếu không tồn tại."""
        student_id = self._session_map.get(session_id)
        if not student_id:
            raise ValueError(
                f"Unknown or expired chat session: '{session_id}'. "
                "Client must call POST /student/session/start first."
            )
        return student_id

    def _get_or_create_student_session(
        self, student_id: str, session_id: str
    ) -> "StudentSession":
        if student_id not in self._sessions:
            self._ensure_student_exists(student_id)
            state = self.mongodb.get_student_state(student_id)
            history = self.mongodb.get_recent_history(student_id, 6, session_id)
            memo = Memo(
                session_history=history,
                session_id=session_id,
                save_callback=lambda entry, sid: self.mongodb.push_to_history(
                    student_id, entry, sid
                ),
            )
            self._sessions[student_id] = StudentSession(student_id, state, memo)
        else:
            # Update memo's session_id if client switched to a different chat session
            session = self._sessions[student_id]
            if session.memo.session_id != session_id:
                session.memo.session_id = session_id
                session.memo.session_history = self.mongodb.get_recent_history(
                    student_id, 6, session_id
                )
        return self._sessions[student_id]

    def _ensure_student_exists(self, student_id: str):
        if self.sqldb.get_student_by_id(student_id) is False:
            self.sqldb.create_student(student_id)
            self.mongodb.create_student(student_id)

    def _on_node_change(self, session: "StudentSession"):
        session.recent_pages.clear()
        session.student_state["active_resource"] = None

    def _rebuild_context(self, session: "StudentSession", proposal: LearningProposal):
        session.recent_pages.clear()
        session.student_state["active_resource"] = None
        existing = session.student_state.get("summary", "") or ""
        marker = f"\n[TRANSITION] {proposal.source_wf}: {proposal.reason}"
        session.student_state["summary"] = (existing + marker).strip()
