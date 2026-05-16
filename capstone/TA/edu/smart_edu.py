import logging
from datetime import datetime
from typing import List, Optional, Any, Dict
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage

from TA.edu.workflow.prompt import ROUTER_PROMPT, RETRIEVE_REFINE_PROMPT, PROPOSAL_PRESENT_PROMPT
from TA.edu.workflow.schema import RouterDecision
from core.schema.wf_state import AgentState, ConceptNode, TAOutput

from TA.edu.workflow.retrieve import build_retrieve_wf
from TA.edu.workflow.roadmap import build_roadmap_wf
from TA.edu.workflow.teach import build_teach_wf

from TA.edu.utils import parse_student_state

logger = logging.getLogger(__name__)


def _resource_ctx(config: RunnableConfig):
    """Get session_id and student_tracker from graph config. NO student_id here."""
    c = config["configurable"]
    return c["session_id"], c["student_tracker"]


def _tracer_ctx(config: RunnableConfig):
    c = config["configurable"]
    return c.get("tracer"), c.get("chat_id", "")


def _extract_ta_context(state: AgentState, max_msgs: int = 3) -> str:
    """ Extract last N assistant messages for TA context injection"""
    messages = state.get("messages", [])
    ta_msgs = []
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai":
            ta_msgs.append(msg.content)
        elif isinstance(msg, dict) and msg.get("role") == "assistant":
            ta_msgs.append(msg["content"])
        if len(ta_msgs) >= max_msgs:
            break
    return "\n---\n".join(reversed(ta_msgs))


class SmartEdu:
    def __init__(self, agents, teach_tools: Dict = None):
        self.agents = agents
        self.teach_tools = teach_tools or {}
        self.app = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)

        builder.add_node("TA_Router", self.ta_router_node)

        builder.add_node("WF_Retrieve", build_retrieve_wf(agents=self.agents))
        builder.add_node("WF_Roadmap", build_roadmap_wf(agents=self.agents))
        builder.add_node("WF_Teach", build_teach_wf(agents=self.agents))

        builder.add_node("TA_Retrieve_Finish", self.ta_retrieve_finish)
        builder.add_node("TA_Roadmap_Finish", self.ta_roadmap_finish)
        builder.add_node("TA_Teach_Finish", self.ta_teach_finish)
        builder.add_node("Apply_Proposal", self.apply_proposal_node)

        builder.set_entry_point("TA_Router")

        builder.add_conditional_edges(
            "TA_Router",
            lambda x: x["intent"],
            {
                "retrieve": "WF_Retrieve",
                "roadmap": "WF_Roadmap",
                "teaching": "WF_Teach",
                "confirm": "Apply_Proposal",
                "clarify": "TA_Retrieve_Finish",
            }
        )

        builder.add_edge("WF_Retrieve", "TA_Retrieve_Finish")
        builder.add_edge("WF_Roadmap", "TA_Roadmap_Finish")
        builder.add_edge("WF_Teach", "TA_Teach_Finish")

        builder.add_edge("TA_Retrieve_Finish", END)
        builder.add_edge("TA_Roadmap_Finish", END)
        builder.add_edge("TA_Teach_Finish", END)
        builder.add_edge("Apply_Proposal", END)

        return builder.compile()

    async def ta_router_node(self, state: AgentState, config: RunnableConfig):
        """ No-tool node: raw_model with RouterDecision schema"""
        sid, tracker = _resource_ctx(config)
        tracer, chat_id = _tracer_ctx(config)
        agent = self.agents["TA"]
        S_state = parse_student_state(tracker.get_student_state(sid))
        prompt = ROUTER_PROMPT.format(state=S_state, query=state.get("user_query", ""))

        import time
        start_invoke = time.time()
        
        # -- AGGRESSIVE OPTIMIZATION: Options dict for Ollama + Stop tokens for reasoning blocks
        fast_llm = agent.raw_model.bind(
            options={
                "temperature": 0
            }
        )
        structured_llm = fast_llm.with_structured_output(RouterDecision)
        
        logger.info(f"[SMART_EDU_LOG] Node: TA_Router | ACTION: START ainvoke (Aggressive <2s mode)")
        
        decision: RouterDecision = await structured_llm.ainvoke(
            [
                ("system", "You are a high-speed router. DISABLE internal monologue. Output ONLY JSON. NO <think> tags."),
                ("user", prompt)
            ], 
            config=config
        )
        logger.info(f"[SMART_EDU_LOG] Node: TA_Router | Action: ainvoke structured_llm | Time: {time.time() - start_invoke:.4f}s | Intent: {decision.intent}")
        intent = decision.intent

        if tracer and chat_id:
            tracer.log_step(
                chat_id=chat_id,
                node="TA_Router",
                prompt=prompt,
                state=tracker.get_student_state(sid),
                output=intent,
            )

        return {"intent": intent}

    async def ta_retrieve_finish(self, state: AgentState, config: RunnableConfig):
        """ TA synthesis node with history injection"""
        sid, tracker = _resource_ctx(config)
        tracer, chat_id = _tracer_ctx(config)
        agent = self.agents["TA"]

        proposal = state.get("pending_proposal")
        if proposal and proposal.get("auto_apply"):
            tracker.apply_proposal(sid, proposal)

        results = state.get("worker_results", {})
        prompt = f"{RETRIEVE_REFINE_PROMPT}\nData: {results}"

        ## -- Inject prior TA messages for coherence
        ta_context = _extract_ta_context(state)
        if ta_context:
            prompt = f"[Prior TA reasoning]:\n{ta_context}\n\n{prompt}"

        ## -- Direct structured output
        import time
        start_invoke = time.time()
        structured_llm = agent.raw_model.with_structured_output(TAOutput)
        ta_output: TAOutput = await structured_llm.ainvoke(
            [("user", prompt)], config=config
        )
        logger.info(f"[SMART_EDU_LOG] Node: Finish_Node | Action: ainvoke structured_llm | Time: {time.time() - start_invoke:.4f}s")

        if tracer and chat_id:
            tracer.log_step(
                chat_id=chat_id,
                node="TA_Retrieve_Finish",
                prompt=prompt,
                state=tracker.get_student_state(sid),
                tool_result=results,
                output=ta_output.message,
            )

        self._append_summary(sid, tracker, "Retrieve", state)
        await self._save_ta_memo(sid, tracker, ta_output)
        tracker.save_state(sid)

        return {"messages": [AIMessage(content=ta_output.message)], "pending_proposal": None}

    async def ta_roadmap_finish(self, state: AgentState, config: RunnableConfig):
        """ TA synthesis node with history injection"""
        sid, tracker = _resource_ctx(config)
        tracer, chat_id = _tracer_ctx(config)
        agent = self.agents["TA"]

        roadmap_data = state.get("worker_results", {}).get("Roadmap", {})
        steps = roadmap_data.get("steps", [])
        advice = roadmap_data.get("advice", {})
        start_node = roadmap_data.get("start_node")

        proposal = None
        if steps:
            new_upcoming = [ConceptNode(name=s) if isinstance(s, str) else ConceptNode(**s) for s in steps]
            new_current = ConceptNode(name=start_node) if start_node else (new_upcoming[0] if new_upcoming else None)

            proposal = {
                "type": "roadmap",
                "new_current": new_current.model_dump() if new_current else None,
                "new_upcoming": [n.model_dump() for n in new_upcoming],
                "reason": advice.get("pedagogical_advice", "") if isinstance(advice, dict) else str(advice),
                "source_wf": "Roadmap",
                "auto_apply": False,
            }
            session = tracker.get_session(sid)
            session.student_state["pending_proposal"] = proposal

        if proposal:
            prompt = PROPOSAL_PRESENT_PROMPT.format(
                type=proposal["type"],
                reason=proposal["reason"][:200],
                new_current=proposal["new_current"]["name"] if proposal["new_current"] else "N/A",
                new_upcoming=", ".join(n["name"] for n in proposal["new_upcoming"][:5]),
                source_wf=proposal["source_wf"],
            )
        else:
            prompt = f"Friendly narrative response for this roadmap and pedagogical advice:\n{advice}"

        ## -- Inject prior TA messages for coherence
        ta_context = _extract_ta_context(state)
        if ta_context:
            prompt = f"[Prior TA reasoning]:\n{ta_context}\n\n{prompt}"

        ## -- Direct structured output
        import time
        start_invoke = time.time()
        structured_llm = agent.raw_model.with_structured_output(TAOutput)
        ta_output: TAOutput = await structured_llm.ainvoke(
            [("user", prompt)], config=config
        )
        logger.info(f"[SMART_EDU_LOG] Node: Finish_Node | Action: ainvoke structured_llm | Time: {time.time() - start_invoke:.4f}s")

        if tracer and chat_id:
            tracer.log_step(
                chat_id=chat_id,
                node="TA_Roadmap_Finish",
                prompt=prompt,
                state=tracker.get_student_state(sid),
                tool_result=roadmap_data,
                output=ta_output.message,
            )

        self._append_summary(sid, tracker, "Roadmap", state)
        await self._save_ta_memo(sid, tracker, ta_output)
        tracker.save_state(sid)

        return {"messages": [AIMessage(content=ta_output.message)], "pending_proposal": proposal}

    async def ta_teach_finish(self, state: AgentState, config: RunnableConfig):
        """ TA synthesis node with history injection"""
        sid, tracker = _resource_ctx(config)
        tracer, chat_id = _tracer_ctx(config)
        agent = self.agents["TA"]

        proposal = state.get("pending_proposal")
        if proposal and proposal.get("auto_apply"):
            tracker.apply_proposal(sid, proposal)

        worker_results = state.get("worker_results", {})
        teach_res = (
            worker_results.get("Teach_Lecture")
            or worker_results.get("Teach_Review")
            or {}
        )

        prompt = (
            "Below is the lecture material generated by the teaching module. "
            "Present it to the student with a brief heading summary "
            f"and the lecture content (polished if needed).\n\nLecture Data:\n{teach_res}"
        )

        ## -- Inject prior TA messages for coherence
        ta_context = _extract_ta_context(state)
        if ta_context:
            prompt = f"[Prior TA reasoning]:\n{ta_context}\n\n{prompt}"

        ## -- Direct structured output
        import time
        start_invoke = time.time()
        structured_llm = agent.raw_model.with_structured_output(TAOutput)
        ta_output: TAOutput = await structured_llm.ainvoke(
            [("user", prompt)], config=config
        )
        logger.info(f"[SMART_EDU_LOG] Node: Finish_Node | Action: ainvoke structured_llm | Time: {time.time() - start_invoke:.4f}s")

        ## -- Auto FE navigation from Teach_Lookup data
        teach_ctx = state.get("_teach_context", {})
        page = teach_ctx.get("page")
        storage_uri = teach_ctx.get("storage_uri")
        if page and not ta_output.ui_action:
            ta_output.ui_action = {"navigate_page": page, "document": storage_uri}

        if tracer and chat_id:
            tracer.log_step(
                chat_id=chat_id,
                node="TA_Teach_Finish",
                prompt=prompt,
                state=tracker.get_student_state(sid),
                tool_result=worker_results,
                output=ta_output.message,
            )

        self._append_summary(sid, tracker, "Teach", state)
        await self._save_ta_memo(sid, tracker, ta_output)
        tracker.save_state(sid)

        return {"messages": [AIMessage(content=ta_output.message)], "pending_proposal": None, "ui_action": ta_output.ui_action}

    async def apply_proposal_node(self, state: AgentState, config: RunnableConfig):
        sid, tracker = _resource_ctx(config)
        tracer, chat_id = _tracer_ctx(config)
        session = tracker.get_session(sid)
        proposal = session.student_state.get("pending_proposal")

        if not proposal:
            msg = "Không có đề xuất nào đang chờ xác nhận."
            ta_output = TAOutput(summary="No pending proposal", message=msg)
            await self._save_ta_memo(sid, tracker, ta_output)
            return {"messages": [AIMessage(content=msg)]}

        tracker.apply_proposal(sid, proposal)

        current = session.student_state.get("current_pos")
        upcoming = session.student_state.get("upcoming_nodes", [])

        msg = f"Đã áp dụng lộ trình mới.\n"
        if current:
            msg += f"Vị trí hiện tại: {current.name}\n"
        if upcoming:
            msg += f"Tiếp theo: {', '.join(n.name for n in upcoming[:3])}"

        ta_output = TAOutput(summary=f"Applied proposal: {current.name if current else 'N/A'}", message=msg)

        if tracer and chat_id:
            tracer.log_step(
                chat_id=chat_id,
                node="Apply_Proposal",
                prompt="",
                state=tracker.get_student_state(sid),
                tool_result=proposal,
                output=msg,
            )

        self._append_summary(sid, tracker, "Confirm_Applied", state)
        await self._save_ta_memo(sid, tracker, ta_output)
        tracker.save_state(sid)

        return {"messages": [AIMessage(content=ta_output.message)], "pending_proposal": None}

    @staticmethod
    def _append_summary(session_id: str, tracker, wf_name: str, state: AgentState):
        session = tracker.get_session(session_id)
        current_pos = session.student_state.get("current_pos")
        pos_name = current_pos.name if current_pos else "N/A"
        status = state.get("status_flag", "DONE")

        entry = f"[{datetime.now().isoformat()}] WF:{wf_name} | Topic: {pos_name} | Result: {status}"

        existing = session.student_state.get("summary", "") or ""
        session.student_state["summary"] = (existing + "\n" + entry).strip()

    @staticmethod
    async def _save_ta_memo(session_id: str, tracker, ta_output: TAOutput):
        """Standard memo save for all finish nodes — uses TAOutput."""
        session = tracker.get_session(session_id)
        await session.memo.save({
            "role": "TA",
            "heading": ta_output.summary,
            "message": ta_output.message,
        })

    async def execute(
        self,
        initial_state: AgentState,
        session_id: str,
        student_tracker,
        tracer=None,
        chat_id: str = "",
        callbacks: Optional[List[Any]] = None,
        update_callback = None,
    ):
        run_config: RunnableConfig = {
            "configurable": {
                "session_id": session_id,
                "student_tracker": student_tracker,
                "tracer": tracer,
                "chat_id": chat_id,
                "teach_tools": self.teach_tools,
            },
            "callbacks": callbacks or [],
        }
        try:
            final_state = dict(initial_state)
            async for chunk in self.app.astream(initial_state, config=run_config, stream_mode="updates"):
                for node_name, state_update in chunk.items():
                    if update_callback:
                        await update_callback(node_name, state_update)
                    # Manually merge the state_update into final_state
                    for key, val in state_update.items():
                        if key == "messages":
                            if "messages" not in final_state:
                                final_state["messages"] = []
                            final_state["messages"].extend(val)
                        elif isinstance(val, dict) and isinstance(final_state.get(key), dict):
                            final_state[key].update(val)
                        else:
                            final_state[key] = val
            return final_state
        except Exception as e:
            logger.exception(
                "SmartEdu execution FAILED | session=%s | input=%r",
                session_id,
                initial_state.get("user_query", "")[:120],
            )
            if tracer and chat_id:
                tracer.log_step(
                    chat_id=chat_id,
                    node="__error__",
                    prompt="",
                    state={},
                    output=str(e),
                )
            # Ensure return dict has the expected keys for TAModule.run
            return {
                **final_state, 
                "status_flag": "FAIL", 
                "_error": str(e),
                "messages": final_state.get("messages", [])
            }