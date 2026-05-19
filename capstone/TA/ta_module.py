from TA.agent.injector import AgentInjector
from TA.tools.factory import ToolFactory
from TA.tools.context_tools import _current_session_context
from TA.edu.smart_edu import SmartEdu
from TA.tracing import AgentTracer
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
from core.schema.wf_state import AgentState, TAOutput
from student.Student_Tracker import Student_Tracker
import asyncio


class TAModule:
    def __init__(self, llm, graph_db, milvus_db, embedder, minio, student_tracker: Student_Tracker, config):
        self.student_tracker = student_tracker

        self.tools_factory = ToolFactory(graph_db, milvus_db, embedder, minio, tracker=student_tracker)

        self.agents = AgentInjector.initialize_all_agents(
            llm_engine=llm, tools_factory=self.tools_factory, config=config.AGENTS
        )
        self.engine: SmartEdu = SmartEdu(
            agents=self.agents,
            teach_tools=self.tools_factory.get_teach_lookup_tools(),
        )

        # Cache tracer per session_id — reuse across turns trong cùng chat session
        self._tracers: dict[str, AgentTracer] = {}

    def _get_tracer(self, session_id: str) -> AgentTracer:
        """Lấy hoặc tạo mới AgentTracer cho chat session."""
        if session_id not in self._tracers:
            self._tracers[session_id] = AgentTracer(session_id=session_id)
        return self._tracers[session_id]

    async def run(self, 
                    user_input: str, 
                    session_id: str, 
                    update_callback=None,
                    language: str = "vn"):

        session = self.student_tracker.get_session(session_id)
        tracer = self._get_tracer(session_id)

        chat_id = tracer.begin_chat(query=user_input)

        # Bug 3 fix: use session.context directly (loaded from MongoDB on session init)
        student_id = self.student_tracker._resolve(session_id)
        session_context = session.context

        await session.memo.save({
            "role": "student",
            "message": user_input,
            "heading": user_input[:100] + "..." + user_input[-100:] if len(user_input) > 200 else user_input,
        })

        history_str = session.memo.get_formatted_history()
        student_state = session.student_state

        initial_state: AgentState = {
            "messages": [
                SystemMessage(content=f"Chat History Context:\n{history_str}"),
                HumanMessage(content=user_input)
            ],
            "student_state": student_state,
            "worker_results": {},
            "intent": user_input,
            "thought": "",
            "status_flag": "On-going",
            "user_query": user_input,
            "language": language,
        }

        callbacks = []
        if tracer.langfuse_handler:
            callbacks.append(tracer.langfuse_handler)

        # Bug 2 fix: inject session_context via ContextVar (async-safe, picked up by context tools)
        _ctx_token = _current_session_context.set(session_context)
        try:
            final_state = await self.engine.execute(
                initial_state=initial_state,
                session_id=session_id,
                student_id=student_id,
                student_tracker=self.student_tracker,
                session_context=session_context,
                chat_id=chat_id,
                tracer=tracer,
                callbacks=callbacks,
                update_callback=update_callback
            )
        finally:
            _current_session_context.reset(_ctx_token)

        if final_state.get("status_flag") == "FAIL":
            error_msg = final_state.get("_error", "Unknown TA workflow error.")
            return {"message": f"System error encountered: {error_msg}", "ui_action": None}

        last_msg = final_state["messages"][-1]
        response = last_msg.content if isinstance(last_msg, BaseMessage) else last_msg.get("content", "")
        
        status = final_state.get("status_flag", "SUCCESS")
        intent = final_state.get("intent", "")
        ui_action = final_state.get("ui_action")

        # ── Kết thúc trace, flush ra file ───────────────────────────────
        await tracer.end_chat(
            chat_id=chat_id,
            final_output=response,
            intent=intent,
            status=status,
        )

        return {"message": response, "ui_action": ui_action}
