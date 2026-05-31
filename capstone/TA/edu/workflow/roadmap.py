import time
import logging
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from core.schema.wf_state import AgentState
from TA.edu.helper.schema import RoadmapExplore, RoadmapCritique, RoadmapFinal
from TA.edu.helper.prompt import ROADMAP_PROMPT
from TA.edu.helper.few_shot import get_language_instruction
from TA.edu.helper.utils import filter_mastery, safe_parse_structured, extract_llm_raw_text
from TA.edu.helper.context import extract_ta_context


from TA.tracing.tracer import AgentTracer
import os

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
    """ Invoke global RAG agent with current_node=Roadmap_Explore for schema routing"""
    import os
    import traceback
    
    start = time.time()
    log_filename = config.get("configurable", {}).get("log_filename") or os.getenv("TEST_LOG_FILENAME")
    
    try:
        query = state.get("user_query", state["messages"][-1].content)
        student_state = state.get("student_state", {})
        current_pos = student_state.get("current_pos")

        language = state.get("language", "vn")
        language_instruction = get_language_instruction(language)

        if current_pos is None:
            instruction = ROADMAP_PROMPT['explore_new'].format(
                language_instruction=language_instruction,
                student_query=query
            )
        else:
            instruction = ROADMAP_PROMPT['explore_existing'].format(
                language_instruction=language_instruction,
                current_pos=current_pos.name if hasattr(current_pos, 'name') else str(current_pos),
                student_query=query
            )

        try:
            result = await rag_agent.ainvoke(
                {"messages": [("user", instruction)], "current_node": "Roadmap_Explore"},
                config={"recursion_limit": 30, **config},
            )
            structured: RoadmapExplore = result["structured_response"]
        except Exception as e:
            logger.warning(f"[roadmap_explore_logic] Structured output failed: {e}. Attempting json_repair.")
            structured = safe_parse_structured(extract_llm_raw_text(e), RoadmapExplore)
        
        report_lines = [
            f"========================= Agent \"{rag_agent.name}\" Runtime Report ==========================",
            f"[SMART_EDU_LOG] Node: Roadmap_Explore | Action: global_agent.ainvoke | Time: {time.time() - start:.4f}s",
            f"Start node: {structured.start_node.name if structured.start_node else 'None'}",
            f"Goal: {structured.goal}",
            f"Steps: {[node.name for node in structured.steps] if structured.steps else []}",
            f"Reasoning: {structured.thought}",
            f"*************** END Report ***************"
        ]
        report_str = "\n" + "\n".join(report_lines) + "\n"
        logger.info(report_str)
        
        if log_filename:
            log_dict = {
                "agent_name": rag_agent.name,
                "node": "Roadmap_Explore",
                "thought": structured.thought,
                "prompt": instruction[:300],
                "output": structured.model_dump()
            }
            AgentTracer.logging(log_dict, type="info", file_name=log_filename)

        current_results = state.get("worker_results", {})

        return {
            "worker_results": {**current_results, "Roadmap": structured.model_dump()},
            "messages": [{"role": "assistant", "content": structured.ai_message}],
            "status_flag": "SUCCESS",
        }
    except Exception as e:
        if log_filename:
            AgentTracer.logging(traceback.format_exc(), type="err", file_name=log_filename)
        raise e


async def roadmap_evaluator_logic(state: AgentState, ta_agent, config: RunnableConfig):
    """ No-tool node: direct structured output with RoadmapCritique"""
    current_results = state.get("worker_results", {})
    roadmap_data = current_results.get("Roadmap", {})
    student_state = state.get("student_state", {})
    mastery_map = student_state.get("mastery_map", {})

    relevant_mastery = filter_mastery(roadmap_data, mastery_map)

    language = state.get("language", "vn")
    language_instruction = get_language_instruction(language)

    instruction = ROADMAP_PROMPT['evaluate'].format(
        language_instruction=language_instruction,
        proposed_steps=roadmap_data.get("steps", []),
        student_mastery=relevant_mastery,
        course_relevance=roadmap_data.get("raw_context", "")
    )

    ## -- Direct structured output, no tool loop
    structured_llm = ta_agent.model.with_structured_output(RoadmapCritique)
    try:
        critique: RoadmapCritique = await structured_llm.ainvoke(
            [("user", instruction)], config=config
        )
    except Exception as e:
        logger.warning(f"[roadmap_evaluator_logic] Structured output failed: {e}. Attempting json_repair.")
        critique = safe_parse_structured(extract_llm_raw_text(e), RoadmapCritique)

    log_filename = config.get("configurable", {}).get("log_filename") or os.getenv("TEST_LOG_FILENAME")
    if log_filename:
        AgentTracer.logging({
            "agent_name": ta_agent.name,
            "node": "Roadmap_Evaluator",
            "thought": critique.thought if hasattr(critique, "thought") else "",
            "prompt": instruction[:300],
            "output": critique.model_dump() if hasattr(critique, "model_dump") else critique
        }, type="info", file_name=log_filename)

    updated_roadmap = {**roadmap_data, "critique": critique.model_dump()}
    return {
        "worker_results": {**current_results, "Roadmap": updated_roadmap},
        "messages": [{"role": "assistant", "content": critique.ai_message}],
    }


async def ta_advice_logic(state: AgentState, ta_agent, config: RunnableConfig):
    """ No-tool node: direct structured output with RoadmapFinal, TA history injected"""
    current_results = state.get("worker_results", {})
    roadmap_data = current_results.get("Roadmap", {})
    critique = roadmap_data.get("critique", {})

    critique_str = f"Feasible: {critique.get('is_feasible')}\nReasoning: {critique.get('reasoning')}"

    language = state.get("language", "vn")
    language_instruction = get_language_instruction(language)

    instruction = ROADMAP_PROMPT['advice'].format(
        language_instruction=language_instruction,
        backbone=roadmap_data.get('steps', []),
        critique=critique_str
    )

    ## -- Inject prior TA messages for coherence (TA model only)
    ta_context = extract_ta_context(state)
    if ta_context:
        instruction = f"[Prior TA reasoning]:\n{ta_context}\n\n{instruction}"

    ## -- Direct structured output, no tool loop
    structured_llm = ta_agent.model.with_structured_output(RoadmapFinal)
    try:
        advice: RoadmapFinal = await structured_llm.ainvoke(
            [("user", instruction)], config=config
        )
    except Exception as e:
        logger.warning(f"[ta_advice_logic] Structured output failed: {e}. Attempting json_repair.")
        advice = safe_parse_structured(extract_llm_raw_text(e), RoadmapFinal)

    log_filename = config.get("configurable", {}).get("log_filename") or os.getenv("TEST_LOG_FILENAME")
    if log_filename:
        AgentTracer.logging({
            "agent_name": ta_agent.name,
            "node": "TA_Advice",
            "thought": advice.thought if hasattr(advice, "thought") else "",
            "prompt": instruction[:300],
            "output": advice.model_dump() if hasattr(advice, "model_dump") else advice
        }, type="info", file_name=log_filename)

    updated_roadmap = {**roadmap_data, "advice": advice.model_dump()}
    return {
        "worker_results": {**current_results, "Roadmap": updated_roadmap},
        "messages": [{"role": "assistant", "content": advice.ai_message}],
        "status_flag": "SUCCESS",
    }