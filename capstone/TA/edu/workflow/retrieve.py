import time
import logging
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from typing import Dict, Any

from core.schema.wf_state import AgentState, ConceptNode
from TA.edu.workflow.prompt import RESEARCH_STRATEGY_PROMPT, DEEP_CHECK_PROMPT
from TA.edu.workflow.schema import RAGCore, RAGDeep, DeepDecision
from TA.edu.utils import parse_student_state

logger = logging.getLogger(__name__)


def build_retrieve_wf(agents):
    builder = StateGraph(AgentState)

    async def _rag_core(state, config):
        return await rag_core(state, agents["RAG"], config)

    async def _deep_decision(state, config):
        return await deep_decision(state, agents["TA"], config)

    async def _rag_deep(state, config):
        return await rag_deep(state, agents["RAG"], config)

    builder.add_node("RAG_Core", _rag_core)
    builder.add_node("Deep_Decision", _deep_decision)
    builder.add_node("rag_deep", _rag_deep)

    builder.set_entry_point("RAG_Core")
    builder.add_edge("RAG_Core", "Deep_Decision")

    builder.add_conditional_edges(
        "Deep_Decision",
        lambda state: state.get("_deep_route", "skip"),
        {
            "deep": "rag_deep",
            "skip": END
        }
    )
    builder.add_edge("rag_deep", END)

    return builder.compile()


async def deep_decision(state: AgentState, ta_agent, config):
    """Classify DEEP vs SKIP — no tools, raw text output."""
    rag_data = state.get("worker_results", {}).get("RAG", {})

    if state.get("status_flag") == "FAIL" or not rag_data.get("entity_ids"):
        return {"_deep_route": "skip"}

    query = state.get("user_query", state["messages"][-1].content)
    student_state = state.get("student_state", {})

    student_state = parse_student_state(student_state)

    prompt = DEEP_CHECK_PROMPT.format(
        query=query,
        rag_summary=str(rag_data.get("content", ""))[:300],
        current_pos=student_state
    )

    ## -- Direct structured output, no tool loop needed
    structured_llm = ta_agent.raw_model.with_structured_output(DeepDecision)
    decision: DeepDecision = await structured_llm.ainvoke(
        [("user", prompt)], config=config
    )

    return {"_deep_route": decision.decision.lower()}


async def rag_core(state: AgentState, rag_agent, config):
    """Dynamic factory: create_react_agent handles tool loop + returns structured_response."""
    query = state["messages"][-1].content
    prompt = f"{RESEARCH_STRATEGY_PROMPT['core']}\nQuery: {query}"

    ## -- Fresh react agent per call, schema-bound
    start_create = time.time()
    react = create_react_agent(
        model=rag_agent.raw_model,
        tools=rag_agent.tools,
        prompt=rag_agent.prompt,
        response_format=RAGCore,
        debug=True,
    )
    logger.info(f"[SMART_EDU_LOG] Node: rag_core | Action: create_react_agent | Time: {time.time() - start_create:.4f}s")

    start_invoke = time.time()
    result = await react.ainvoke(
        {"messages": [("user", prompt)]},
        config={"recursion_limit": 10, **config},
    )
    logger.info(f"[SMART_EDU_LOG] Node: rag_core | Action: ainvoke | Time: {time.time() - start_invoke:.4f}s | Result keys: {list(result.keys())}")

    ## -- Pydantic object from LangGraph, no manual parsing
    structured: RAGCore = result["structured_response"]
    current_worker_results = state.get("worker_results", {})

    return {
        "worker_results": {**current_worker_results, "RAG": structured.model_dump()},
        "status_flag": structured.status,
    }


async def rag_deep(state: AgentState, rag_agent, config):
    """Dynamic factory: create_react_agent handles tool loop + returns structured_response."""
    rag_data: Dict[str, Any] = state.get("worker_results", {}).get("RAG", {})
    student_state = state.get("student_state", {})
    current_pos_obj = student_state.get("current_pos")

    query = state.get("user_query", state["messages"][-1].content)

    prompt = RESEARCH_STRATEGY_PROMPT["deep"].format(
        query=query,
        current_pos=current_pos_obj.name if current_pos_obj else "None",
        entity_ids=str(rag_data.get("entity_ids", []))
    )

    ## -- Fresh react agent per call, schema-bound
    start_create = time.time()
    react = create_react_agent(
        model=rag_agent.raw_model,
        tools=rag_agent.tools,
        prompt=rag_agent.prompt,
        response_format=RAGDeep,
        debug=True,
    )
    logger.info(f"[SMART_EDU_LOG] Node: rag_deep | Action: create_react_agent | Time: {time.time() - start_create:.4f}s")

    start_invoke = time.time()
    result = await react.ainvoke(
        {"messages": [("user", f"{prompt}\nContext: {rag_data.get('content', '')}")]},
        config={"recursion_limit": 8, **config},
    )
    logger.info(f"[SMART_EDU_LOG] Node: rag_deep | Action: ainvoke | Time: {time.time() - start_invoke:.4f}s | Result keys: {list(result.keys())}")

    deep_res: RAGDeep = result["structured_response"]

    bridge_nodes = [
        ConceptNode(name=c["name"]) if isinstance(c, dict) else ConceptNode(name=c.name)
        for c in deep_res.bridge_concepts
        if (isinstance(c, dict) and c.get("name")) or (hasattr(c, "name") and c.name)
    ]

    proposal = None
    if deep_res.is_deep and bridge_nodes:
        proposal = {
            "type": "bridge",
            "new_current": bridge_nodes[0].model_dump(),
            "new_upcoming": [n.model_dump() for n in bridge_nodes[1:]],
            "reason": f"Knowledge gap: {deep_res.knowledge_gap_score:.1f}",
            "source_wf": "Retrieve",
            "auto_apply": True,
        }
    elif bridge_nodes and current_pos_obj:
        proposal = {
            "type": "bridge",
            "new_current": current_pos_obj.model_dump(),
            "new_upcoming": [n.model_dump() for n in bridge_nodes],
            "reason": f"Bridge concepts needed",
            "source_wf": "Retrieve",
            "auto_apply": True,
        }

    merged_rag_data = {**rag_data, **deep_res.model_dump()}
    current_worker_results = state.get("worker_results", {})

    result = {"worker_results": {**current_worker_results, "RAG": merged_rag_data}}
    if proposal:
        result["pending_proposal"] = proposal
    return result