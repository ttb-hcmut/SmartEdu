import json
import logging
from langgraph.graph import StateGraph, END
from core.schema.wf_state import AgentState, ConceptNode
from TA.edu.workflow.schema import TeachEvalOutput, TeachLectureOutput
from TA.edu.workflow.prompt import (
    TEACH_UNDERSTAND_PROMPT,
    TEACH_REVIEW_PROMPT,
    TEACH_CONTINUE_PROMPT,
    TEACH_EVAL_PROMPT_V2,
    NEXT_TOPIC_PROMPT,
)
from TA.edu.utils import ainvoke_with_temp, parse_json_response, wrap_agent_structured

logger = logging.getLogger(__name__)


def build_teach_wf(agents):
    builder = StateGraph(AgentState)

    builder.add_node(
        "Teach_Understand",
        lambda state, config: teach_understand(state, agents["TA"], config),
    )
    builder.add_node(
        "Teach_Lookup",
        lambda state, config: teach_lookup(state, config),
    )
    builder.add_node(
        "Teach_RAG",
        lambda state, config: teach_rag(state, agents["RAG"], config),
    )
    builder.add_node(
        "Teach_Lecture",
        lambda state, config: teach_lecture(state, agents["TA"], config),
    )
    builder.add_node(
        "Teach_Evaluate",
        lambda state, config: teach_evaluate(state, agents["TA"], config),
    )
    builder.add_node(
        "Next_Topic",
        lambda state, config: next_topic(state, agents["TA"], config),
    )

    builder.set_entry_point("Teach_Understand")

    builder.add_conditional_edges(
        "Teach_Understand",
        lambda state: state.get("_teach_mode", "continue"),
        {
            "review": "Teach_Lookup",
            "continue": "Teach_Lookup",
            "evaluate": "Teach_Evaluate",
        },
    )

    builder.add_conditional_edges(
        "Teach_Lookup",
        _route_after_lookup,
        {
            "has_content": "Teach_Lecture",
            "no_content": "Teach_RAG",
        },
    )

    builder.add_edge("Teach_RAG", "Teach_Lecture")
    builder.add_edge("Teach_Lecture", END)
    builder.add_edge("Teach_Evaluate", "Next_Topic")
    builder.add_edge("Next_Topic", END)

    return builder.compile()


def _route_after_lookup(state: AgentState) -> str:
    ctx = state.get("_teach_context", {})
    return "has_content" if ctx.get("source") == "PDF" else "no_content"


# ─── Node 1: Intent Classification ─────────────────────────────────────────

async def teach_understand(state: AgentState, ta_agent, config):
    """LLM classifies student intent into review / continue / evaluate."""
    query = state.get("user_query", "")
    sid = config["configurable"]["session_id"]
    tracker = config["configurable"]["student_tracker"]
    tracer = config["configurable"].get("tracer")
    chat_id = config["configurable"].get("chat_id", "")
    history = tracker.get_chat_history(sid)

    prompt = TEACH_UNDERSTAND_PROMPT.format(history=history, query=query)
    res = await ainvoke_with_temp(
        agent=ta_agent,
        input_data={"messages": [("user", prompt)]},
        config=config,
        temp=0.0,
    )

    mode = res.content.strip().lower()
    if mode not in ("review", "continue", "evaluate"):
        mode = "continue"

    if tracer and chat_id:
        tracer.log_step(
            chat_id=chat_id,
            node="Teach_Understand",
            prompt=prompt,
            state=tracker.get_student_state(sid),
            output=mode,
        )

    return {"_teach_mode": mode}


# ─── Node 2: Deterministic PDF Lookup (No LLM) ─────────────────────────────

async def teach_lookup(state: AgentState, config):
    """
    Deterministic PDF lookup. No LLM needed.
    Calls GetConcept + GetPages directly via Python.
    """
    sid = config["configurable"]["session_id"]
    tracker = config["configurable"]["student_tracker"]
    tracer = config["configurable"].get("tracer")
    chat_id = config["configurable"].get("chat_id", "")
    teach_tools = config["configurable"].get("teach_tools", {})
    session = tracker.get_session(sid)
    student_state = session.student_state

    current_node = student_state.get("current_pos")
    mode = state.get("_teach_mode", "continue")
    active_resource = student_state.get("active_resource")

    no_content = {
        "_teach_context": {"source": "NO_CONTENT", "content": "", "page": None, "mode": mode}
    }

    if not current_node:
        logger.info("[Teach_Lookup] No current_pos, routing to RAG")
        return no_content

    concept_tool = teach_tools.get("get_concept")
    pages_tool = teach_tools.get("get_pages")

    if not concept_tool or not pages_tool:
        logger.warning("[Teach_Lookup] teach_tools not injected, routing to RAG")
        return no_content

    # Step 1: Find pages containing the concept
    try:
        concept_result = concept_tool._run(concept=current_node.name)
        parsed = json.loads(concept_result)
    except Exception as e:
        logger.warning(f"[Teach_Lookup] GetConcept failed: {e}")
        return no_content

    if isinstance(parsed, dict) and "error" in parsed:
        logger.info(f"[Teach_Lookup] Concept '{current_node.name}' not in PDF, routing to RAG")
        return no_content

    if not parsed or not isinstance(parsed, list) or len(parsed) == 0:
        return no_content

    # Step 2: Read page content
    hard_ref_str = parsed[0].get("hard_ref")
    if not hard_ref_str:
        return no_content

    try:
        ref_data = json.loads(hard_ref_str)
        p_list = ref_data.get("p_num", [])
        page_num = p_list[0] if isinstance(p_list, list) and p_list else p_list
        storage_uri = ref_data.get("id")  # In hard_ref, 'id' is the minio path
    except Exception as e:
        logger.warning(f"[Teach_Lookup] Failed to parse hard_ref: {e}")
        return no_content

    if not storage_uri or not page_num:
        return no_content

    try:
        page_content = pages_tool._run(
            pages=[page_num, page_num + 1],
            destination=storage_uri,
        )
    except Exception as e:
        logger.warning(f"[Teach_Lookup] GetPages failed: {e}")
        return no_content

    if "error" in page_content.lower() or len(page_content.strip()) < 50:
        logger.info("[Teach_Lookup] PDF content too short, routing to RAG")
        return no_content

    if tracer and chat_id:
        tracer.log_step(
            chat_id=chat_id,
            node="Teach_Lookup",
            prompt=f"Lookup concept: {current_node.name}",
            state=tracker.get_student_state(sid),
            output=f"PDF source: {ref_data.get('name')}, page {page_num}, {len(page_content)} chars",
        )

    return {
        "_teach_context": {
            "source": "PDF",
            "content": page_content,
            "page": page_num,
            "storage_uri": storage_uri,
            "mode": mode,
        }
    }


# ─── Node 3: RAG Fallback (reuses rag_core from retrieve.py) ───────────────

async def teach_rag(state: AgentState, rag_agent, config):
    """
    Fallback when PDF has no content.
    Reuses the exact same rag_core logic from WF_Retrieve.
    """
    from TA.edu.workflow.retrieve import rag_core

    sid = config["configurable"]["session_id"]
    tracker = config["configurable"]["student_tracker"]
    tracer = config["configurable"].get("tracer")
    chat_id = config["configurable"].get("chat_id", "")
    current_node = tracker.get_student_state(sid).get("current_pos")
    mode = state.get("_teach_mode", "continue")

    concept_name = current_node.name if current_node else "the current topic"

    # Build a focused query for rag_core
    mock_message = {"role": "user", "content": f"Explain the concept of {concept_name} in detail."}
    temp_state = {
        **state,
        "messages": state["messages"] + [mock_message],
        "user_query": f"Explain {concept_name}",
    }

    rag_result = await rag_core(temp_state, rag_agent, config)

    rag_content = rag_result.get("worker_results", {}).get("RAG", {}).get("content", "")

    if tracer and chat_id:
        tracer.log_step(
            chat_id=chat_id,
            node="Teach_RAG",
            prompt=f"RAG fallback for: {concept_name}",
            state=tracker.get_student_state(sid),
            output=f"RAG retrieved {len(rag_content)} chars",
        )

    return {
        "worker_results": rag_result.get("worker_results", {}),
        "_teach_context": {
            "source": "RAG",
            "content": rag_content,
            "page": None,
            "mode": mode,
        },
    }


# ─── Node 4: LLM Lecture Generation ────────────────────────────────────────

async def teach_lecture(state: AgentState, ta_agent, config):
    """
    LLM generates a lecture from pre-fetched content (PDF or RAG).
    No tool calling — content is already available in _teach_context.
    """
    sid = config["configurable"]["session_id"]
    tracker = config["configurable"]["student_tracker"]
    tracer = config["configurable"].get("tracer")
    chat_id = config["configurable"].get("chat_id", "")
    session = tracker.get_session(sid)
    student_state = session.student_state
    history = tracker.get_chat_history(sid)

    ctx = state.get("_teach_context", {})
    content = ctx.get("content", "")
    source = ctx.get("source", "unknown")
    mode = ctx.get("mode", "continue")

    current_node = student_state.get("current_pos")
    previous_nodes = student_state.get("previous_nodes", [])
    current_str = current_node.name if current_node else "None"

    if mode == "review":
        prev_str = "\n".join(
            f"  {i+1}. {n.name} ({n.type})" for i, n in enumerate(previous_nodes[:6])
        ) or "  (no previous nodes)"

        prompt = TEACH_REVIEW_PROMPT.format(
            previous_nodes=prev_str,
            current_node=current_str,
            source=source,
            content=content[:3000],
            history=history,
        )
    else:
        prev_str = "\n".join(
            f"  {i+1}. {n.name} ({n.type})" for i, n in enumerate(previous_nodes[:3])
        ) or "  (no previous nodes)"

        prompt = TEACH_CONTINUE_PROMPT.format(
            previous_nodes=prev_str,
            current_node=current_str,
            source=source,
            content=content[:3000],
            history=history,
        )

    # No tools bound — pure text generation from pre-fetched content
    structured_llm = wrap_agent_structured(ta_agent, 0.5, TeachLectureOutput)
    res = await structured_llm.ainvoke([("user", prompt)], config=config)

    lecture_text = res.lecture
    if res.challenge_question:
        lecture_text += f"\n\n**Câu hỏi kiểm tra:** {res.challenge_question}"

    if tracer and chat_id:
        tracer.log_step(
            chat_id=chat_id,
            node=f"Teach_Lecture ({mode})",
            prompt=prompt[:500],
            state=tracker.get_student_state(sid),
            output=lecture_text[:500],
        )

    result_key = "Teach_Review" if mode == "review" else "Teach_Lecture"
    current_results = state.get("worker_results", {})
    return {
        "worker_results": {**current_results, result_key: lecture_text},
        "_teach_context": {**ctx, "lecture_output": res.model_dump()},
        "status_flag": "SUCCESS",
    }


# ─── Node 5: Evaluation ────────────────────────────────────────────────────

async def teach_evaluate(state: AgentState, ta_agent, config):

    sid = config["configurable"]["session_id"]
    tracker = config["configurable"]["student_tracker"]
    history = tracker.get_chat_history(sid)

    prompt = TEACH_EVAL_PROMPT_V2.format(history=history)

    structured_llm = wrap_agent_structured(ta_agent, temp=0.1, schema=TeachEvalOutput)
    eval_res = await structured_llm.ainvoke(
        [("user", prompt)], config=config
    )

    current_results = state.get("worker_results", {})
    return {
        "worker_results": {**current_results, "Teach_Eval": eval_res.model_dump()},
        "_teach_context": {"eval_result": eval_res.model_dump()},
    }


# ─── Node 6: Next Topic Selection ──────────────────────────────────────────

async def next_topic(state: AgentState, ta_agent, config):
    sid = config["configurable"]["session_id"]
    tracker = config["configurable"]["student_tracker"]
    session = tracker.get_session(sid)
    student_state = session.student_state
    eval_data = state.get("_teach_context", {}).get("eval_result", {})

    current_node = student_state.get("current_pos")
    current_str = current_node.name if current_node else "None"

    if not eval_data.get("passed", False):
        return {
            "worker_results": {
                **state.get("worker_results", {}),
                "Next_Topic": {"action": "STAY", "reason": "Evaluation not passed"},
            }
        }

    recommend_result = _get_recommendations(tracker.graphdb, current_node)

    prompt = NEXT_TOPIC_PROMPT.format(
        passed=eval_data.get("passed"),
        user_eval=eval_data.get("user_eval", ""),
        current_node=current_str,
        recommend_list=recommend_result,
    )

    res = await ainvoke_with_temp(
        agent=ta_agent,
        input_data={"messages": [("user", prompt)]},
        config=config,
        temp=0.3,
    )

    content = res.content if hasattr(res, "content") else str(res)
    selected = parse_json_response(content)

    if isinstance(selected, list):
        selected_names = selected
    elif isinstance(selected, dict) and "data" in selected:
        selected_names = []
    else:
        selected_names = []

    next_nodes = [ConceptNode(name=name) for name in selected_names if isinstance(name, str)]

    if current_node:
        tracker.add_finished_community(sid, current_node)

    proposal = None
    if next_nodes:
        proposal = {
            "type": "advance",
            "new_current": next_nodes[0].model_dump(),
            "new_upcoming": [n.model_dump() for n in next_nodes[1:]],
            "reason": f"Eval passed. Next: {next_nodes[0].name}",
            "source_wf": "Teach",
            "auto_apply": True,
        }

    result = {
        "worker_results": {
            **state.get("worker_results", {}),
            "Next_Topic": {
                "action": "ADVANCE" if next_nodes else "NO_CANDIDATES",
                "selected_nodes": [n.name for n in next_nodes],
            },
        },
        "student_state": student_state,
    }
    if proposal:
        result["pending_proposal"] = proposal
    return result


def _get_recommendations(graphdb, current_node) -> str:
    if not current_node:
        return "No current position."

    cypher = """
    MATCH (n:Entity {name: $name})-[r]->(m:Entity)
    WHERE type(r) <> 'CONTENT' AND m.rrole IS NULL
    OPTIONAL MATCH (m)-[r2]->(other:Entity)
    WHERE type(r2) <> 'CONTENT' AND other.rrole IS NULL
    WITH m, count(r2) AS out_degree
    ORDER BY out_degree DESC
    LIMIT 10
    RETURN m.name AS name, m.content AS content,
           m.typeNode AS type, out_degree
    """
    results = graphdb.run_query(graphdb.db_name, cypher, {"name": current_node.name})

    if not results:
        return "No neighboring nodes found."

    lines = []
    for i, r in enumerate(results, 1):
        desc = r.get("content", "")[:50] if r.get("content") else "N/A"
        lines.append(
            f"{i}. [{r.get('type', '')}] {r['name']} "
            f"| connections: {r.get('out_degree', 0)} | {desc}"
        )
    return "\n".join(lines)