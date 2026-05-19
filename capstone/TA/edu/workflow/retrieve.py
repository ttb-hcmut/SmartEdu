import time
import logging
from langgraph.graph import StateGraph, END
from typing import Dict, Any

from core.schema.wf_state import AgentState, ConceptNode
import TA.edu.workflow.prompt as prompt_lib
from TA.edu.workflow.schema import RAGCore, RAGDeep, DeepDecision
from TA.edu.workflow.few_shot import get_language_instruction
from TA.edu.utils import parse_student_state, safe_parse_structured, extract_llm_raw_text


from TA.tracing.tracer import AgentTracer

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
    """ Classify DEEP vs SKIP, no tools, direct structured output"""
    rag_data = state.get("worker_results", {}).get("RAG", {})

    if state.get("status_flag") == "FAIL" or not rag_data.get("entity_ids"):
        return {"_deep_route": "skip"}

    query = state.get("user_query", state["messages"][-1].content)
    student_state = state.get("student_state", {})

    student_state = parse_student_state(student_state)

    language = state.get("language", "vn")
    language_instruction = get_language_instruction(language)

    prompt = prompt_lib.DEEP_CHECK_PROMPT.format(
        language_instruction=language_instruction,
        query=query,
        rag_summary=str(rag_data.get("content", ""))[:300],
        current_pos=student_state
    )

    ## -- Direct structured output, no tool loop needed
    structured_llm = ta_agent.model.with_structured_output(DeepDecision)
    try:
        decision: DeepDecision = await structured_llm.ainvoke(
            [("user", prompt)], config=config
        )
        route = decision.decision.lower()
    except Exception as e:
        logger.warning(f"[deep_decision] Structured output failed: {e}. Attempting json_repair.")
        raw_text = extract_llm_raw_text(e)
        try:
            decision = safe_parse_structured(raw_text, DeepDecision)
            route = decision.decision.lower()
        except Exception:
            # Last resort: keyword scan
            upper = raw_text.upper()
            route = "deep" if "DEEP" in upper else "skip"
            logger.info(f"[deep_decision] Keyword fallback → route='{route}'")

    log_filename = config.get("configurable", {}).get("log_filename") or os.getenv("TEST_LOG_FILENAME")
    if log_filename:
        AgentTracer.logging({
            "agent_name": ta_agent.name,
            "node": "Deep_Decision",
            "thought": decision.thought if 'decision' in locals() and hasattr(decision, "thought") else "",
            "prompt": prompt[:300],
            "output": decision.model_dump() if 'decision' in locals() and hasattr(decision, "model_dump") else {"decision": route}
        }, type="info", file_name=log_filename)

    return {"_deep_route": route}



async def rag_core(state: AgentState, rag_agent, config):
    """ Invoke global RAG agent with current_node=RAG_Core for schema routing"""
    import os
    import traceback
    
    start = time.time()
    log_filename = config.get("configurable", {}).get("log_filename") or os.getenv("TEST_LOG_FILENAME")
    
    try:
        query = state["messages"][-1].content
        language = state.get("language", "vn")
        language_instruction = get_language_instruction(language)
        
        core_prompt = prompt_lib.RESEARCH_STRATEGY_PROMPT['core'].format(
            language_instruction=language_instruction
        )
        prompt = f"{core_prompt}\nQuery: {query}"
        
        try:
            result = await rag_agent.ainvoke(
                {"messages": [("user", prompt)], "current_node": "RAG_Core"},
                config={"recursion_limit": 40, **config},  
            )
            structured: RAGCore = result["structured_response"]
        except Exception as e:
            logger.warning(f"[rag_core] Structured output failed: {e}. Attempting json_repair.")
            structured = safe_parse_structured(extract_llm_raw_text(e), RAGCore)

        
        report_lines = [
            f"========================= Agent \"{rag_agent.name}\" Runtime Report ==========================",
            f"[SMART_EDU_LOG] Node: rag_core | Action: global_agent.ainvoke | Time: {time.time() - start:.4f}s",
            f"Status: {structured.status}",
            f"Reasoning: {structured.thought}",
            f"Entity IDs: {structured.entity_ids}",
            f"Content length: {len(structured.content) if structured.content else 0}",
            f"*************** END Report ***************"
        ]
        report_str = "\n" + "\n".join(report_lines) + "\n"
        logger.info(report_str)
        
        if log_filename:
            log_dict = {
                "agent_name": rag_agent.name,
                "node": "rag_core",
                "thought": structured.thought,
                "prompt": prompt[:300],
                "output": structured.model_dump()
            }
            AgentTracer.logging(log_dict, type="info", file_name=log_filename)

        current_worker_results = state.get("worker_results", {})
        result_state = {
            "worker_results": {**current_worker_results, "RAG": structured.model_dump()},
            "status_flag": structured.status,
        }

        # Store in session context (in-memory, for within-request recall by TA tools)
        session_context = config.get("configurable", {}).get("session_context")
        chat_id = config.get("configurable", {}).get("chat_id", "")
        if session_context and chat_id:
            session_context.store_tool_result(
                chat_id=chat_id,
                tool_name="rhetorical_retriever",
                args={"query": query},
                output=structured.content or "",
                node="RAG_Core",
            )

        # Persist to MongoDB atomically (background, concurrent-safe $push)
        student_id = config.get("configurable", {}).get("student_id", "")
        tracker = config.get("configurable", {}).get("student_tracker")
        if tracker and student_id and chat_id:
            import asyncio
            asyncio.create_task(
                asyncio.to_thread(
                    tracker.mongodb.push_session_tool_result,
                    student_id,
                    config.get("configurable", {}).get("session_id", ""),
                    chat_id,
                    {
                        "tool_name": "rhetorical_retriever",
                        "node": "RAG_Core",
                        "args": {"query": query},
                        "output": (structured.content or "")[:1000],  # Cap stored payload
                    }
                )
            )

        return result_state
    except Exception as e:
        if log_filename:
            AgentTracer.logging(traceback.format_exc(), type="err", file_name=log_filename)
        raise e


async def rag_deep(state: AgentState, rag_agent, config):
    """ Invoke global RAG agent with current_node=RAG_Deep for schema routing"""
    import os
    import traceback
    
    start = time.time()
    log_filename = config.get("configurable", {}).get("log_filename") or os.getenv("TEST_LOG_FILENAME")
    
    try:
        rag_data: Dict[str, Any] = state.get("worker_results", {}).get("RAG", {})
        student_state = state.get("student_state", {})
        current_pos_obj = student_state.get("current_pos")

        query = state.get("user_query", state["messages"][-1].content)
        language = state.get("language", "vn")
        language_instruction = get_language_instruction(language)

        prompt = prompt_lib.RESEARCH_STRATEGY_PROMPT["deep"].format(
            language_instruction=language_instruction,
            query=query,
            current_pos=current_pos_obj.name if current_pos_obj else "None",
            entity_ids=str(rag_data.get("entity_ids", []))
        )
        
        try:
            result = await rag_agent.ainvoke(
                {"messages": [("user", f"{prompt}\nContext: {rag_data.get('content', '')}")], "current_node": "RAG_Deep"},
                config={"recursion_limit": 15, **config},
            )
            structured: RAGDeep = result["structured_response"]
        except Exception as e:
            logger.warning(f"[rag_deep] Structured output failed: {e}. Attempting json_repair.")
            structured = safe_parse_structured(extract_llm_raw_text(e), RAGDeep)

        
        report_lines = [
            f"========================= Agent \"{rag_agent.name}\" Runtime Report ==========================",
            f"[SMART_EDU_LOG] Node: rag_deep | Action: global_agent.ainvoke | Time: {time.time() - start:.4f}s",
            f"Is Deep: {structured.is_deep}",
            f"Reasoning: {structured.thought}",
            f"Bridge Concepts: {len(structured.bridge_concepts) if structured.bridge_concepts else 0}",
            f"*************** END Report ***************"
        ]
        report_str = "\n" + "\n".join(report_lines) + "\n"
        logger.info(report_str)
        
        if log_filename:
            log_dict = {
                "agent_name": rag_agent.name,
                "node": "rag_deep",
                "thought": structured.thought,
                "prompt": prompt[:300],
                "output": structured.model_dump()
            }
            AgentTracer.logging(log_dict, type="info", file_name=log_filename)

        bridge_nodes = [
            ConceptNode(name=c["name"]) if isinstance(c, dict) else ConceptNode(name=c.name)
            for c in structured.bridge_concepts
            if (isinstance(c, dict) and c.get("name")) or (hasattr(c, "name") and c.name)
        ]

        proposal = None
        if structured.is_deep and bridge_nodes:
            proposal = {
                "type": "bridge",
                "new_current": bridge_nodes[0].model_dump(),
                "new_upcoming": [n.model_dump() for n in bridge_nodes[1:]],
                "reason": f"Knowledge gap: {structured.knowledge_gap_score:.1f}",
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

        merged_rag_data = {**rag_data, **structured.model_dump()}
        current_worker_results = state.get("worker_results", {})

        result_dict = {"worker_results": {**current_worker_results, "RAG": merged_rag_data}}
        if proposal:
            result_dict["pending_proposal"] = proposal
        return result_dict

    except Exception as e:
        if log_filename:
            AgentTracer.logging(traceback.format_exc(), type="err", file_name=log_filename)
        raise e