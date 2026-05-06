from langchain.tools import BaseTool

from TA.agent.base import BaseAgent
from TA.tools.factory import ToolFactory
from core.llm.llm_engine import CoreLLMEngine

from langchain_core.prompts import ChatPromptTemplate

class AgentInjector:
    @staticmethod
    def initialize_all_agents(llm_engine : CoreLLMEngine, tools_factory : ToolFactory, config):
        agents = {}
        for agent_name, agent_prompt, schema in config:
            llm_instance = llm_engine._get_llm(agent_name)
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", agent_prompt),
                ("placeholder", "{messages}")
            ])
            agent_tools: list[BaseTool] = tools_factory.get_tools(agent_name = agent_name )
            llm_with_tools = llm_instance.bind_tools(agent_tools)
            agents[agent_name] = prompt_template | llm_with_tools
            """
            agents[agent_name] = BaseAgent(
                llm=llm_instance,
                system_prompt=agent_prompt,
                tools=agent_tools,
                format=schema
            ).agent"""
        return agents