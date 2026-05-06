from typing import List, Any
from typing import List, Dict, Any, Annotated
from typing_extensions import TypedDict
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver


class BaseAgent:
    def __init__(self, llm,system_prompt, tools: List[Any], format: Any = None):
        self.llm = llm
        self.tools: List[Any] = tools
        self.format = format
        
        self.memory = MemorySaver()
        
      
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt, # Inject prompt vào đây
            checkpointer=self.memory,
            response_format=format,
            debug = False

        )

    async def run(self, query: str, session_id: str = "123", chat_history = []) -> Dict[str, Any]:
        """Execute reasoning and tool calls via LangGraph"""
        
        config = {"configurable": {"thread_id": session_id}}
        
        inputs: Dict[str, List[tuple[str, str]]] = {"messages": [("user", query)]}
        
        final_state = None
        intermediate_steps = []

        async for chunk in self.agent.astream(input=inputs, config=config, stream_mode="values"):
            final_state = chunk # Lưu lại state cuối cùng
            
        
        return {
            "output": final_state["messages"][-1].content,
            "intermediate_steps": final_state["messages"], 
            "raw_state": final_state
        }
    
    async def ainvoke(self, input : str):
        res = await self.agent.ainvoke(input)
    
