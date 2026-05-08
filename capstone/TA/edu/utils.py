
import json
from typing import Dict, Any

def parse_agent_steps(messages: list) -> list:

    parsed = []
    
    for i, msg in enumerate(messages):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.get("name")
                tool_input = tool_call.get("args")
                
                observation = "No output found"
                if i + 1 < len(messages) and messages[i+1].type == "tool":
                    if messages[i+1].tool_call_id == tool_call.get("id"):
                        observation = messages[i+1].content
                
                parsed.append({
                    "agent_action": {
                        "tool": tool_name,
                        "input": tool_input,
                        "log": f"Calling tool {tool_name} with args {tool_input}"
                    },
                    "observation": str(observation)[:500] + "..." if len(str(observation)) > 500 else observation
                })
                
    return parsed



def parse_json_response(content: str) -> Dict[str, Any]:
    import re
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r'```(?:json)?\s*(.*?)```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    start_idx = content.find('{')
    end_idx = content.rfind('}')
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        try:
            return json.loads(content[start_idx:end_idx + 1])
        except json.JSONDecodeError:
            pass

    return {"status": "ERROR", "data": content}

def trilingual_format(vn: str, en: str) -> str:
    return f"**{vn}** ({en}) - **{vn}**"

async def ainvoke_with_temp(agent, input_data: dict, config: dict, temp: float):
    llm = agent.last
    actual_llm = llm.bound if hasattr(llm, "bound") else llm
    old_temp = getattr(actual_llm, "temperature", None)
    
    if hasattr(actual_llm, "temperature"):
        actual_llm.temperature = temp
        
    try:
        return await agent.ainvoke(input_data, config=config)
    finally:
        if old_temp is not None and hasattr(actual_llm, "temperature"):
            actual_llm.temperature = old_temp

def wrap_agent_structured(agent, temp: float, schema):
    """
    Extract the base LLM from an agent chain (prompt | llm.bind_tools(...))
    and bind a structured output schema onto it — cleanly separated from
    the tool-calling pipeline so ChatOllama doesn't confuse tool format
    with JSON output format.
    """
    llm = agent.last
    actual_llm = llm.bound if hasattr(llm, "bound") else llm
    return actual_llm.bind(temperature=temp).with_structured_output(schema)

def compact_explore(raw_tool_output: str) -> str:
    """Parse raw explorer output and keep only minimal required fields"""
    if not raw_tool_output:
        return ""
    return raw_tool_output[:2500] + "\n...(truncated)" if len(raw_tool_output) > 2500 else raw_tool_output

def filter_mastery(roadmap_data: dict, mastery_map: dict) -> dict:
    """Filter mastery_map based on backbone nodes to reduce context"""
    backbone_names = {n.get("name") for n in roadmap_data.get("steps", []) if isinstance(n, dict)}
    
    relevant_mastery = {}
    if mastery_map:
        for k, v in mastery_map.items():
            if k in backbone_names:
                relevant_mastery[k] = v
            elif any(k.lower() in name.lower() or name.lower() in k.lower() for name in backbone_names):
                relevant_mastery[k] = v
                
    return relevant_mastery

def parse_student_state(state: dict) -> str:
    parsed_state = {}
    
    current = state.get("current_pos")
    if current:
        parsed_state["current_target"] = {
            "name": current.name,
            "type": current.type,
            "description": current.description,
            "node_mastery": current.mastery
        }
        
        mastery_map = state.get("mastery_map", {})
        if current.name in mastery_map:
            parsed_state["current_target"]["global_mastery_score"] = mastery_map[current.name]

    parsed_state["path"] = {
        "recently_completed": [n.name for n in state.get("previous_nodes", [])[:3]],
        "upcoming": [n.name for n in state.get("upcoming_nodes", [])[:3]]
    }

    if state.get("summary"):
        parsed_state["student_profile"] = state.get("summary")

    if state.get("active_resource"):
        parsed_state["active_resource"] = state.get("active_resource")

    return str(parsed_state)
        