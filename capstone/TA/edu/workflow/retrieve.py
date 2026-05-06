from langgraph.graph import StateGraph, END
from typing import Dict, Any

from core.schema.wf_state import AgentState, ConceptNode
from TA.edu.workflow.prompt import RESEARCH_STRATEGY_PROMPT, DEEP_CHECK_PROMPT
from TA.edu.workflow.schema import RAGCore, RAGDeep, DeepDecision
from TA.edu.utils import parse_student_state


def build_retrieve_wf(agents):
    builder = StateGraph(AgentState)

    builder.add_node("RAG_Core", lambda state, run_config: rag_core(state, agents["RAG"], run_config))
    builder.add_node("Deep_Decision", lambda state, run_config: deep_decision(state, agents["TA"], run_config))
    builder.add_node("rag_deep", lambda state, run_config: rag_deep(state, agents["RAG"], run_config))

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
    
    res = await ta_agent.ainvoke(
        {"messages": [("user", prompt)]},
        config=config
    )
    
    content = res.content if hasattr(res, 'content') else str(res)
    decision = "deep" if "DEEP" in content.upper().strip() else "skip"
    
    return {"_deep_route": decision}

async def rag_core(state: AgentState, rag_agent, config):
    query = state["messages"][-1].content
    
    prompt = f"{RESEARCH_STRATEGY_PROMPT['core']}\nQuery: {query}"
    
    res = await rag_agent.ainvoke(
        {"messages": [("user", prompt)]}, 
        config=config
    )
    
    content = res.content if hasattr(res, 'content') else str(res)
    
    from TA.edu.utils import parse_json_response
    parsed = parse_json_response(content)
    
    rag_res = RAGCore(
        thought=parsed.get("thought", ""),
        entity_ids=parsed.get("entity_ids", []),
        content=parsed.get("content", content),
        status=parsed.get("status", "SUCCESS" if parsed.get("content") else "FAIL")
    ) 
    
    current_worker_results = state.get("worker_results", {})
    
    return {
        "worker_results": {**current_worker_results, "RAG": rag_res.model_dump()},
        "status_flag": rag_res.status
    }

async def rag_deep(state: AgentState, rag_agent, config):
    rag_data: Dict[str, Any] = state.get("worker_results", {}).get("RAG", {})
    student_state = state.get("student_state", {})
    current_pos_obj = student_state.get("current_pos")
    
    student_state_str = parse_student_state(student_state)
    
    query = state.get("user_query", state["messages"][-1].content)

    prompt = RESEARCH_STRATEGY_PROMPT["deep"].format(
        query=query, 
        current_pos=current_pos_obj.name if current_pos_obj else "None",
        entity_ids=str(rag_data.get("entity_ids", []))
    )
    
    res = await rag_agent.ainvoke(
        {"messages": [("user", f"{prompt}\nContext: {rag_data.get('content', '')}")]},
        config=config
    )

    content = res.content if hasattr(res, 'content') else str(res)
    from TA.edu.utils import parse_json_response
    parsed = parse_json_response(content)

    deep_res = RAGDeep(
        is_deep=parsed.get("is_deep", False),
        bridge_concepts=parsed.get("bridge_concepts", []),
        knowledge_gap_score=parsed.get("knowledge_gap_score", 0.0)
    )

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