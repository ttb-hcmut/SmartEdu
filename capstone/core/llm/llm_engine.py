from typing import Any, Dict
from langchain_ollama import ChatOllama
from langchain_core.exceptions import OutputParserException
from core.llm.config import LLMConfig


class CoreLLMEngine:
    def __init__(self, config: LLMConfig = LLMConfig()):
        self.config = config
        self._instances: Dict[str, Any] = {}

    def _get_llm(self, profile_name: str) -> ChatOllama:
        profile_name = profile_name.lower()
        if profile_name not in self._instances:
            if profile_name not in self.config.profiles:
                raise ValueError(f"Profile '{profile_name}' not found in configuration.")
            
            profile = self.config.profiles[profile_name]

            ## -- Build kwargs, omit None values
            kwargs: Dict[str, Any] = {
                "model": profile.model_name,
                "temperature": profile.temperature,
                "num_ctx": profile.num_ctx,
                "reasoning": False,
            }
            if profile.num_predict is not None:
                kwargs["num_predict"] = profile.num_predict
            if profile.keep_alive is not None:
                kwargs["keep_alive"] = profile.keep_alive

            self._instances[profile_name] = ChatOllama(**kwargs)
        return self._instances[profile_name]