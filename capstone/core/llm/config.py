from dataclasses import dataclass, field
from typing import Dict


@dataclass
class LLMProfile:
    model_name: str
    temperature: float = 0.0
    num_ctx: int = 4096
    max_retries: int = 3
    prompt: str = ""

@dataclass
class LLMConfig:
    profiles: Dict[str, LLMProfile] = field(default_factory=lambda: {
        "graph": LLMProfile(
            model_name="gpt-oss:120b-cloud", 
            temperature=0.2, 
            num_ctx=4096, 
            max_retries=3        ),
        "ta": LLMProfile(
            model_name="qwen3.5:4b", 
            temperature=0.67, 
            num_ctx=4096, 
            max_retries=2
        ),
        "evaluator": LLMProfile(
            model_name="qwen3:8b", 
            temperature=0.3, 
            num_ctx=2048, 
            max_retries=2
        ),
        "generator": LLMProfile(
            model_name="gpt-oss:120b-cloud", 
            temperature=0.4, 
            num_ctx=4096, 
            max_retries=2
        ),
        "rag": LLMProfile(
            model_name="qwen3.5:4b", 
            temperature=0.3, 
            num_ctx=2048, 
            max_retries=2
        ),
        "worker": LLMProfile(
            model_name="gemma3:1b", 
            temperature=0.0, 
            num_ctx=512, 
            max_retries=3
        )
    })


    default_profile: str = "graph"

config_instance = LLMConfig()