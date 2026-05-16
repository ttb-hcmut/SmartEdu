from langchain.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from TA.tools.factory import ToolFactory
from core.llm.llm_engine import CoreLLMEngine



class AgentInjector:
    @staticmethod
    def initialize_all_agents(llm_engine: CoreLLMEngine, tools_factory: ToolFactory, config):
        """
        ## -- Build agents WITHOUT response_format (schema bound dynamically per node)
        ## -- Expose raw_model, tools, prompt for dynamic factory use
        """
        agents = {}
        for agent_name, agent_prompt, _schema in config:
            llm_instance = llm_engine._get_llm(agent_name)
            agent_tools: list[BaseTool] = tools_factory.get_tools(agent_name=agent_name)

            ## -- Create schema-free react agent; nodes bind schema at call time
            agent = create_react_agent(
                name=agent_name,
                model=llm_instance,
                tools=agent_tools,
                prompt=agent_prompt,
                debug = True
            )

            ## -- Attach references for dynamic factory in workflow nodes
            setattr(agent, "raw_model", llm_instance)
            setattr(agent, "tools", agent_tools)
            setattr(agent, "prompt", agent_prompt)
            agents[agent_name] = agent

        return agents