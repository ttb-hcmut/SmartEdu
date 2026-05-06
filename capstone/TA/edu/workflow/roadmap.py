from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from core.schema.wf_state import AgentState
from TA.edu.workflow.schema import RoadmapExplore, RoadmapCritique, RoadmapFinal
from TA.edu.workflow.prompt import ROADMAP_PROMPT

from TA.edu.utils import *


def build_roadmap_wf(agents):
    builder = StateGraph(AgentState)

    builder.add_node(
        "Roadmap_Explore", 
        lambda state, config: roadmap_explore_logic(state, agents["RAG"], config)
    )
    
    builder.add_node(
        "Roadmap_Evaluator", 
        lambda state, config: roadmap_evaluator_logic(state, agents["TA"], config)
    )
    
    builder.add_node(
        "TA_Advice", 
        lambda state, config: ta_advice_logic(state, agents["TA"], config)
    )

    builder.set_entry_point("Roadmap_Explore")
    builder.add_edge("Roadmap_Explore", "Roadmap_Evaluator")
    builder.add_edge("Roadmap_Evaluator", "TA_Advice")
    builder.add_edge("TA_Advice", END)

    return builder.compile()

async def roadmap_explore_logic(state: AgentState, rag_agent, config):
    query = state.get("user_query", state["messages"][-1].content)
    student_state = state.get("student_state", {})
    
    current_pos = student_state.get("current_pos")
    
    instruction = ROADMAP_PROMPT['explore'].format(
        current_pos=current_pos if current_pos else "null",
        student_query=query
    )

    res = await rag_agent.ainvoke({"messages": [("user", instruction)]}, config=config)
    
    tool_results_text = ""
    if hasattr(res, "tool_calls") and res.tool_calls:
        tools = rag_agent.last.kwargs.get("tools", [])
        tool_map = {getattr(t, "name", ""): t for t in tools}
        
        for tcall in res.tool_calls:
            tool_name = tcall["name"]
            if tool_name in tool_map:
                try:
                    t_result = await tool_map[tool_name].ainvoke(tcall["args"])
                    tool_results_text += f"\n--- {tool_name} ---\n{t_result}\n"
                except Exception as e:
                    tool_results_text += f"\n--- {tool_name} Error ---\n{str(e)}\n"
            else:
                tool_results_text += f"\n--- Error: {tool_name} not found ---\n"
                
    if not tool_results_text.strip():
        tool_results_text = "No additional data retrieved from Neo4j."

    structured_llm = rag_agent.last.bind(temperature=0.0).with_structured_output(RoadmapExplore)
    
    format_prompt = f"""You are an expert educational planner.
I have retrieved the following raw data from our Neo4j Knowledge Graph based on the student's request:
---
{tool_results_text}
---

STUDENT CONTEXT:
- Query: {query}
- Current Position: {current_pos if current_pos else 'null'}

YOUR TASK:
1. Analyze the raw Neo4j data above.
2. Formulate a structured learning roadmap that directly answers the student's Query.
3. Identify an appropriate 'start_node' (the first concept to learn, based on their Current Position).
4. Extract the sequence of concepts as 'steps' for the roadmap.
5. Provide a brief 'reasoning' for why this path is chosen.

CRITICAL:
- ONLY use concepts that exist in the provided Neo4j data.
- Output MUST be structured exactly as the RoadmapExplore schema requires.
"""
    
    final_res = await structured_llm.ainvoke([("user", format_prompt)], config=config)
    
    
    compact_data = compact_explore(raw_tool_output=tool_results_text)
    
    roadmap_dict = final_res.model_dump()
    roadmap_dict["raw_context"] = compact_data
    
    current_results = state.get("worker_results", {})
    return {
        "worker_results": {**current_results, "Roadmap": roadmap_dict},
        "status_flag": "SUCCESS"
    }

async def roadmap_evaluator_logic(state: AgentState, ta_agent, config: RunnableConfig):
    from TA.edu.utils import filter_mastery
    
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
    
    structured_llm = ta_agent.with_structured_output(RoadmapCritique)
    res = await structured_llm.ainvoke({"messages": [("user", instruction)]}, config=config)
    
    updated_roadmap = {**roadmap_data, "critique": res.model_dump()}


    return {"worker_results": {**current_results, "Roadmap": updated_roadmap}}
async def ta_advice_logic(state: AgentState, ta_agent, config: RunnableConfig):
    current_results = state.get("worker_results", {})
    roadmap_data = current_results.get("Roadmap", {})
    critique = roadmap_data.get("critique", {})
    
    critique_str = f"Feasible: {critique.get('is_feasible')}\nReasoning: {critique.get('reasoning')}"
    
    instruction = ROADMAP_PROMPT['advice'].format(
        backbone=roadmap_data.get('steps', []),
        critique=critique_str
    )
    
    structured_llm = ta_agent.with_structured_output(RoadmapFinal)
    res = await structured_llm.ainvoke({"messages": [("user", instruction)]}, config=config)
    
    updated_roadmap = {**roadmap_data, "advice": res.model_dump()}
    return {
        "worker_results": {**current_results, "Roadmap": updated_roadmap}, 
        "status_flag": "SUCCESS"
    }