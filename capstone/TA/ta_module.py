from TA.agent.injector import AgentInjector
from TA.tools.factory import ToolFactory
from TA.edu.smart_edu import SmartEdu
from core.schema.wf_state import StudentState, AgentState
from langchain_core.runnables import RunnableConfig
from student.Student_Tracker import Student_Tracker

class TAModule:
    def __init__(self, llm, graph_db, milvus_db, embedder, minio, student_tracker: Student_Tracker, config):
        self.student_tracker = student_tracker
        
        self.tools_factory = ToolFactory(graph_db, milvus_db, embedder, minio, tracker=student_tracker)
        
        self.agents = AgentInjector.initialize_all_agents(
            llm_engine=llm, tools_factory=self.tools_factory, config=config.AGENTS
        )
        self.engine: SmartEdu = SmartEdu(agents=self.agents)

    async def run(self, user_input: str, student_id: str = "default"):
        session = self.student_tracker.get_session(student_id)

        await session.memo.save({
            "role": "student",
            "message": user_input,
            "heading": user_input[:100] + "..." + user_input[-100:] if len(user_input) > 200 else user_input,
        })

        history_str = session.memo.get_formatted_history()
        student_state = session.student_state

        initial_state: AgentState = {
            "messages": [
                {"role": "system", "content": f"Chat History Context:\n{history_str}"},
                {"role": "user", "content": user_input}
            ],
            "student_state": student_state,
            "worker_results": {},
            "intent": user_input,
            "status_flag": "On-going",
            "user_query": user_input,
        }

        final_state = await self.engine.execute(
            initial_state=initial_state,
            student_id=student_id,
            student_tracker=self.student_tracker
        )

        return final_state["messages"][-1].content
