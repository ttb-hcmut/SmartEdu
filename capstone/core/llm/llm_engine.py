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
    
    def invoke_with_retry(self, prompt_template, parser, input_data: dict, profile_name: str = None, max_retries: int = None):
        target_profile = (profile_name or self.config.default_profile).lower()
        llm = self._get_llm(target_profile)
        
        profile_config = self.config.profiles[target_profile]
        retries = max_retries if max_retries is not None else getattr(profile_config, 'max_retries', 3)
        
        chain = prompt_template | llm | parser
        
        for attempt in range(retries):
            try:
                return chain.invoke(input_data)
            except OutputParserException:
                if attempt == retries - 1:
                    return None
            except Exception as e:
                print(f"LLM Error: {str(e)}")
                if attempt == retries - 1:
                    return None
        return None

    async def ainvoke_with_retry(self, prompt_template, parser, input_data: dict, profile_name: str = None, max_retries: int = None):
        target_profile = (profile_name or self.config.default_profile).lower()
        llm: ChatOllama = self._get_llm(target_profile)
        
        profile_config = self.config.profiles[target_profile]
        retries = max_retries if max_retries is not None else getattr(profile_config, 'max_retries', 3)
        
        chain = prompt_template | llm | parser
        
        for attempt in range(retries):
            try:
                return await chain.ainvoke(input_data)
            except OutputParserException:
                if attempt == retries - 1:
                    return None
            except Exception as e:
                print(f"LLM Error: {str(e)}")
                if attempt == retries - 1:
                    return None
        return None