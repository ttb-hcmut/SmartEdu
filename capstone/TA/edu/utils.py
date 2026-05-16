
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)



def parse_agent_steps(messages: list) -> list:
    """ Extract tool call history from agent messages for tracing"""
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


def trilingual_format(vn: str, en: str) -> str:
    return f"**{vn}** ({en}) - **{vn}**"


def compact_explore(raw_tool_output: str) -> str:
    """ Truncate raw explorer output for context window"""
    if not raw_tool_output:
        return ""
    return raw_tool_output[:2500] + "\n...(truncated)" if len(raw_tool_output) > 2500 else raw_tool_output


def filter_mastery(roadmap_data: dict, mastery_map: dict) -> dict:
    """ Filter mastery_map to only backbone-relevant entries"""
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
    """ Serialize student state to compact string for prompt injection"""
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