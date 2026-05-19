import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from core.config import Mongo_conf
from typing import Dict, List, Any

"""
student document structure in 'students' collection:
{
    "_id": student_id,
    "state": {
        "finished_communities": [],
        "current_pos": None,
        "active_resource": None,
        "mastery_map": {},
        "previous_nodes": [],
        "upcoming_nodes": [],
        "summary": str,
        "pending_proposal": None
    },
    "memo": {
        "<session_id>": [
            {
                "role": "student" | "TA",
                "heading": str,
                "message": str,
                "timestamp": datetime
            }
        ]
    }
}
"""


class Mongo_DB:
    def __init__(self, config: Mongo_conf = Mongo_conf()):
        self.client = MongoClient(config.uri)
        self.db = self.client[config.db_name]
        self.students: Collection = self.db['students']
        self.learning_logs: Collection = self.db['learning_logs']

    def create_student(self, student_id: str):
        doc = self.students.find_one({"_id": student_id})
        if not doc:
            self.students.insert_one({
                "_id": student_id,
                "state": {
                    "finished_communities": [],
                    "current_pos": None,
                    "active_resource": None,
                    "mastery_map": {},
                    "previous_nodes": [],
                    "upcoming_nodes": [],
                    "summary": "Student just started",
                    "pending_proposal": None
                },
                "memo": {}
            })

    def get_student_state(self, student_id: str) -> dict:
        doc = self.students.find_one({"_id": student_id}, {"state": 1})
        if not doc:
            self.create_student(student_id)
            doc = self.students.find_one({"_id": student_id}, {"state": 1})
        return doc.get("state", {})

    def update_student_state(self, student_id: str, state_dict: dict):
        self.students.update_one(
            {"_id": student_id},
            {"$set": {"state": state_dict}},
            upsert=True
        )

    def log_event(self, student_id: str, action: str, node_id: str, data: dict = None):
        log_entry = {
            "student_id": student_id,
            "action": action,
            "node_id": node_id,
            "data": data or {},
            "timestamp": datetime.datetime.utcnow()
        }
        self.learning_logs.insert_one(log_entry)

    # Nested student object with state and memo
    def push_to_history(self, student_id: str, entry: Dict[str, Any], session_id: str = "default"):
        """Push a chat entry into the nested memo under the given session_id."""
        entry_with_ts = {**entry, "timestamp": datetime.datetime.utcnow()}
        self.students.update_one(
            {"_id": student_id},
            {"$push": {f"memo.{session_id}": entry_with_ts}},
            upsert=True
        )

    def get_recent_history(self, student_id: str, limit: int = 6, session_id: str = "default") -> List[Dict[str, Any]]:
        """Get the most recent chat history entries from the nested memo."""
        doc = self.students.find_one(
            {"_id": student_id},
            {f"memo.{session_id}": {"$slice": -limit}}
        )
        if not doc or "memo" not in doc:
            return []
        return doc["memo"].get(session_id, [])

    def push_session_tool_result(
        self, student_id: str, session_id: str, chat_id: str, entry: dict
    ) -> None:
        """Atomically append one tool result entry via $push — concurrent-safe."""
        entry_with_ts = {**entry, "timestamp": datetime.datetime.utcnow().isoformat()}
        self.students.update_one(
            {"_id": student_id},
            {"$push": {f"session_context.{session_id}.tool_results.{chat_id}": entry_with_ts}},
            upsert=True,
        )

    def push_session_thought(
        self, student_id: str, session_id: str, chat_id: str, entry: dict
    ) -> None:
        """Atomically append one thought entry via $push — concurrent-safe."""
        entry_with_ts = {**entry, "timestamp": datetime.datetime.utcnow().isoformat()}
        self.students.update_one(
            {"_id": student_id},
            {"$push": {f"session_context.{session_id}.thoughts.{chat_id}": entry_with_ts}},
            upsert=True,
        )

    def get_session_context(self, student_id: str, session_id: str) -> dict:
        """Load persisted SessionContext data (tool_results + thoughts), returns empty dict if none."""
        doc = self.students.find_one(
            {"_id": student_id},
            {f"session_context.{session_id}": 1},
        )
        if not doc:
            return {}
        return doc.get("session_context", {}).get(session_id, {})