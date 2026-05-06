from collections import deque
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from core.repo.graph.graphdb import GraphDB
from core.repo.sql.sql_db import SQL_DB
from core.repo.nosql.mongo_db import Mongo_DB
from core.schema.wf_state import ConceptNode, StudentState, LearningProposal
from student.memo import *

NONE_LENGTH = 5

class Page(BaseModel):
    path: str = Field(exclude=True) 
    page: int
    concept: List[str] = Field(default_factory=list) 
    content: str = ""

    def __str__(self):
        return f"Page {self.page}: {self.content[:50]}... Concepts: {self.concept}"




class Student_Tracker:
    def __init__(self, graphdb: GraphDB, sqldb: SQL_DB, mongodb: Mongo_DB):
        self.graphdb = graphdb
        self.sqldb = sqldb
        self.mongodb = mongodb
        self._sessions: Dict[str, StudentSession] = {}

    def get_session(self, student_id: str, session_id: str = "default") -> StudentSession:
        if student_id not in self._sessions:
            self._ensure_student_exists(student_id)
            state = self.mongodb.get_student_state(student_id)
            history = self.mongodb.get_recent_history(student_id, 6, session_id)
            memo = Memo(
                session_history=history,
                save_callback=lambda entry: self.mongodb.push_to_history(student_id, entry, session_id)
            )
            self._sessions[student_id] = StudentSession(student_id, state, memo)
        return self._sessions[student_id]

    def _ensure_student_exists(self, student_id: str):
        if self.sqldb.get_student_by_id(student_id) is False:
            self.sqldb.create_student(student_id)
            self.mongodb.create_student(student_id)

    def get_student_state(self, student_id: str) -> StudentState:
        return self.get_session(student_id).student_state

    def get_student_profile(self, student_id: str):
        return self.sqldb.get_student_by_id(student_id)

    def save_state(self, student_id: str):
        session = self.get_session(student_id)
        self.mongodb.update_student_state(student_id, session.student_state)

    def get_road_map(self, student_id: str) -> Dict:
        return self.graphdb.get_learning_graph(student_id)

    def update_learning_position(self, student_id: str, new_node: ConceptNode, bridge_nodes: list = None):
        session = self.get_session(student_id)
        state = session.student_state

        if bridge_nodes:
            valid_bridge = bridge_nodes[:3]
            current_upcoming = state.get("upcoming_nodes", [])
            state["upcoming_nodes"] = valid_bridge + current_upcoming

        current_pos = state.get("current_pos")

        if current_pos and current_pos.name == new_node.name:
            self.save_state(student_id)
            return

        if current_pos is not None:
            prev = state.get("previous_nodes", [])
            prev.insert(0, current_pos)
            state["previous_nodes"] = prev[:NONE_LENGTH]

        self.graphdb.update_learn(student_id, current_pos, new_node)
        state["current_pos"] = new_node
        self._on_node_change(session)
        self.save_state(student_id)

    def get_mastery(self, student_id: str, node_name: str) -> int:
        return self.graphdb.get_mastery(student_id, node_name)

    def current_resource(self, student_id: str, n=3) -> List[Page]:
        session = self.get_session(student_id)
        return list(session.recent_pages)[-n:]

    def add_recent_page(self, student_id: str, page: Page):
        session = self.get_session(student_id)
        session.recent_pages.append(page)

    def _on_node_change(self, session: StudentSession):
        session.recent_pages.clear()
        session.student_state["active_resource"] = None

    def get_chat_history(self, student_id: str) -> str:
        session = self.get_session(student_id)
        return session.memo.get_formatted_history()

    def apply_proposal(self, student_id: str, proposal_dict: Dict[str, Any]):
        proposal = LearningProposal(**proposal_dict)

        session = self.get_session(student_id)
        state = session.student_state

        if proposal.new_upcoming:
            state["upcoming_nodes"] = proposal.new_upcoming

        if proposal.new_current:
            self.update_learning_position(student_id, proposal.new_current)

        self._rebuild_context(session, proposal)
        state["pending_proposal"] = None
        self.save_state(student_id)

    def _rebuild_context(self, session: StudentSession, proposal: LearningProposal):
        session.recent_pages.clear()
        session.student_state["active_resource"] = None

        existing = session.student_state.get("summary", "") or ""
        marker = f"\n[TRANSITION] {proposal.source_wf}: {proposal.reason}"
        session.student_state["summary"] = (existing + marker).strip()

    def drop_session(self, student_id: str):
        self._sessions.pop(student_id, None)
