import logging
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig

from core.schema.wf_state import AgentState
from TA.edu.workflow.schema import RoadmapExplore, RoadmapCritique, RoadmapFinal
from TA.edu.workflow.prompt import ROADMAP_PROMPT
from TA.edu.utils import filter_mastery

logger = logging.getLogger(__name__)


def build_roadmap_wf(agents):
    builder = StateGraph(AgentState)

    async def _roadmap_explore(state, config):
        return await roadmap_explore_logic(state, agents["RAG"], config)

    async def _roadmap_evaluator(state, config):
        return await roadmap_evaluator_logic(state, agents["TA"], config)

    async def _ta_advice(state, config):
        return await ta_advice_logic(state, agents["TA"], config)

    builder.add_node("Roadmap_Explore", _roadmap_explore)
    builder.add_node("Roadmap_Evaluator", _roadmap_evaluator)
    builder.add_node("TA_Advice", _ta_advice)

    builder.set_entry_point("Roadmap_Explore")
    builder.add_edge("Roadmap_Explore", "Roadmap_Evaluator")
    builder.add_edge("Roadmap_Evaluator", "TA_Advice")
    builder.add_edge("TA_Advice", END)

    return builder.compile()


async def roadmap_explore_logic(state: AgentState, rag_agent, config):
    """## -- Dynamic factory: bind RoadmapExplore schema, RAG tools for exploration"""
    query = state.get("user_query", state["messages"][-1].content)
    student_state = state.get("student_state", {})
    current_pos = student_state.get("current_pos")

    if current_pos is None:
        instruction = ROADMAP_PROMPT['explore_new'].format(student_query=query)
    else:
        instruction = ROADMAP_PROMPT['explore_existing'].format(
            current_pos=current_pos.name if hasattr(current_pos, 'name') else str(current_pos),
            student_query=query
        )

    ## -- Dynamic react agent with RoadmapExplore schema
    react = create_react_agent(
        model=rag_agent.raw_model,
        tools=rag_agent.tools,
        prompt=rag_agent.prompt,
        response_format=RoadmapExplore,
    )

    result = await react.ainvoke(
        {"messages": [("user", instruction)]},
        config=config,
    )

    ## -- Extract validated Pydantic object
    structured: RoadmapExplore = result["structured_response"]
    current_results = state.get("worker_results", {})

    return {
        "worker_results": {**current_results, "Roadmap": structured.model_dump()},
        "messages": [{"role": "assistant", "content": structured.ai_message}],
        "status_flag": "SUCCESS",
    }


async def roadmap_evaluator_logic(state: AgentState, ta_agent, config: RunnableConfig):
    """## -- No-tool node: raw_model with RoadmapCritique schema"""
    current_results = state.get("worker_results", {})
    roadmap_data = current_results.get("Roadmap", {})
    student_state = state.get("student_state", {})
    mastery_map = student_state.get("mastery_map", {})

    relevant_mastery = filter_mastery(roadmap_data, mastery_map)

    instruction = ROADMAP_PROMPT['evaluate'].format(
        proposed_steps=roadmap_data.get("steps", []),
        student_mastery=relevant_mastery,
        course_relevance=roadmap_data.get("raw_context", "")
    )

    ## -- Direct structured output, no tool loop
    structured_llm = ta_agent.raw_model.with_structured_output(RoadmapCritique)
    critique: RoadmapCritique = await structured_llm.ainvoke(
        [("user", instruction)], config=config
    )

    updated_roadmap = {**roadmap_data, "critique": critique.model_dump()}
    return {
        "worker_results": {**current_results, "Roadmap": updated_roadmap},
        "messages": [{"role": "assistant", "content": critique.ai_message}],
    }


async def ta_advice_logic(state: AgentState, ta_agent, config: RunnableConfig):
    """## -- No-tool node: raw_model with RoadmapFinal schema, TA history injected"""
    current_results = state.get("worker_results", {})
    roadmap_data = current_results.get("Roadmap", {})
    critique = roadmap_data.get("critique", {})

    critique_str = f"Feasible: {critique.get('is_feasible')}\nReasoning: {critique.get('reasoning')}"

    instruction = ROADMAP_PROMPT['advice'].format(
        backbone=roadmap_data.get('steps', []),
        critique=critique_str
    )

    ## -- Inject prior TA messages for coherence (TA model only)
    ta_context = _extract_ta_context(state)
    if ta_context:
        instruction = f"[Prior TA reasoning]:\n{ta_context}\n\n{instruction}"

    ## -- Direct structured output, no tool loop
    structured_llm = ta_agent.raw_model.with_structured_output(RoadmapFinal)
    advice: RoadmapFinal = await structured_llm.ainvoke(
        [("user", instruction)], config=config
    )

    updated_roadmap = {**roadmap_data, "advice": advice.model_dump()}
    return {
        "worker_results": {**current_results, "Roadmap": updated_roadmap},
        "messages": [{"role": "assistant", "content": advice.ai_message}],
        "status_flag": "SUCCESS",
    }


def _extract_ta_context(state: AgentState, max_msgs: int = 3) -> str:
    """## -- Extract last N assistant messages from state for TA context injection"""
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