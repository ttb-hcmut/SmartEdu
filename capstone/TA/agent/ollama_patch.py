"""
Wrapper LangChain ProviderStrategy for Ollama schema
Must be imported BEFORE any create_agent() call

If you come this far, please read this issue to understand further:
https://github.com/langchain-ai/langchain/issues/34239

The issue is still unsolved from the root, this is just a convenient runtime decorator
"""
from __future__ import annotations
from typing import Any

_PATCHED = False


def ollama_patcher() -> None:
    """ Patch ProviderStrategy.to_model_kwargs + _supports_provider_strategy for Ollama"""
    global _PATCHED
    if _PATCHED:
        return

    from langchain.agents.structured_output import ProviderStrategy
    import langchain.agents.factory as factory_mod
    from langchain_ollama import ChatOllama
    from langchain_core.language_models.chat_models import BaseChatModel

    # Fix native JSON schema to Ollama: {"format": <json_schema_dict>}
    _original_to_model_kwargs = ProviderStrategy.to_model_kwargs

    def _ollama_to_model_kwargs(self) -> dict[str, Any]:
        """ Return Ollama-native format kwarg instead of OpenAI response_format"""
        return {"format": self.schema_spec.json_schema}

    ProviderStrategy.to_model_kwargs = _ollama_to_model_kwargs

    # DANGEROUS: Forcefully override ProviderStrategy for ChatOllama models input schema
    # This changing the original library behaviour. 
    # To do this: langchain version >=1.2.10
    # This only wwork in newest agent factory where middleware interfere the graph state layer of agent
    _original_supports = factory_mod._supports_provider_strategy

    def _patched_supports_provider_strategy(model, tools=None) -> bool:
        """ Force ProviderStrategy for ChatOllama models"""
        if isinstance(model, ChatOllama):
            return True
        if isinstance(model, BaseChatModel):
            inner = getattr(model, "bound", None) or getattr(model, "first", None)
            if isinstance(inner, ChatOllama):
                return True
        return _original_supports(model, tools=tools)

    factory_mod._supports_provider_strategy = _patched_supports_provider_strategy

    _PATCHED = True


ollama_patcher()
