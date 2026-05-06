import json
from langgraph.graph import StateGraph, END
from core.schema.wf_state import AgentState, ConceptNode
from TA.edu.workflow.schema import TeachEvalOutput
from TA.edu.workflow.prompt import (
    TEACH_UNDERSTAND_PROMPT,
    TEACH_REVIEW_PROMPT,
    TEACH_CONTINUE_PROMPT,
    TEACH_EVAL_PROMPT_V2,
    NEXT_TOPIC_PROMPT,
)
from TA.edu.utils import ainvoke_with_temp, parse_json_response, wrap_agent_structured


def build_teach_wf(agents):
    builder = StateGraph(AgentState)

    builder.add_node(
        "Teach_Understand",
        lambda state, config: teach_understand(state, agents["TA"], config),
    )
    builder.add_node(
        "teach_review",
        lambda state, config: teach_lecture(state, agents["TA"], config, mode="review"),
    )
    builder.add_node(
        "teach_continue",
        lambda state, config: teach_lecture(state, agents["TA"], config, mode="continue"),
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
            "review": "teach_review",
            "continue": "teach_continue",
            "evaluate": "Teach_Evaluate",
        },
    )

    builder.add_edge("teach_review", END)
    builder.add_edge("teach_continue", END)
    builder.add_edge("Teach_Evaluate", "Next_Topic")
    builder.add_edge("Next_Topic", END)

    return builder.compile()


# ─── Node 1: Intent Classification ─────────────────────────────────────────

async def teach_understand(state: AgentState, ta_agent, config):
    """LLM classifies student intent into review / continue / evaluate."""
    query = state.get("user_query", "")
    sid = config["configurable"]["student_id"]
    tracker = config["configurable"]["student_tracker"]
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

    return {"_teach_mode": mode}


# ─── Node 2 & 3: Lecture (review / continue) ───────────────────────────────

async def teach_lecture(state: AgentState, ta_agent, config, mode: str):
    """
    Unified lecture node for both 'review' and 'continue' modes.
    Both use the same tool set (get_concept, get_pdf_pages, navigate_frontend_page).
    No structured output — returns raw string for streaming.
    """
    sid = config["configurable"]["student_id"]
    tracker = config["configurable"]["student_tracker"]
    session = tracker.get_session(sid)
    student_state = session.student_state
    history = tracker.get_chat_history(sid)

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
            history=history,
        )
    else:
        prev_str = "\n".join(
            f"  {i+1}. {n.name} ({n.type})" for i, n in enumerate(previous_nodes[:3])
        ) or "  (no previous nodes)"

        prompt = TEACH_CONTINUE_PROMPT.format(
            previous_nodes=prev_str,
            current_node=current_str,
            history=history,
        )

    # Agent has tools bound (get_concept, get_pdf_pages, navigate_frontend_page)
    # LangGraph handles tool execution loop automatically
    res = await ta_agent.ainvoke({"messages": [("user", prompt)]}, config=config)

    content = res.content if hasattr(res, "content") else str(res)

    result_key = "Teach_Review" if mode == "review" else "Teach_Lecture"
    current_results = state.get("worker_results", {})
    return {
        "worker_results": {**current_results, result_key: content},
        "status_flag": "SUCCESS",
    }


# ─── Node 4: Evaluation ────────────────────────────────────────────────────

async def teach_evaluate(state: AgentState, ta_agent, config):

    sid = config["configurable"]["student_id"]
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


# ─── Node 5: Next Topic Selection ──────────────────────────────────────────

async def next_topic(state: AgentState, ta_agent, config):
    sid = config["configurable"]["student_id"]
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
        student_state.setdefault("finished_communities", []).append(current_node)

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
    results = graphdb.run_query("test", cypher, {"name": current_node.name})

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