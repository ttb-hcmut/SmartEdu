"""
Prompt management and synchronization
Reference from https://langfuse.com/docs/prompt-management
"""

import os
import asyncio
from dotenv import load_dotenv

# Load env vars để lấy LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../core/.env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../tracing/.env"))

from langfuse import Langfuse
from TA.edu.workflow.prompt import (
    _ROUTER_PROMPT,
    _RETRIEVE_REFINE_PROMPT,
    _DEEP_CHECK_PROMPT,
    _RESEARCH_STRATEGY_PROMPT,
    _ROADMAP_PROMPT,
    _TEACH_UNDERSTAND_PROMPT,
    _TEACH_REVIEW_PROMPT,
    _TEACH_CONTINUE_PROMPT,
    _TEACH_EVAL_PROMPT_V2,
    _NEXT_TOPIC_PROMPT,
    _PROPOSAL_PRESENT_PROMPT,
)

def sync_all_prompts():
    secret = os.getenv("LANGFUSE_SECRET_KEY")
    public = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not secret or not public:
        print("Error: NO KEY")
        return

    print(f"Langfuse at {host}...")
    try:
        langfuse = Langfuse(secret_key=secret, public_key=public, host=host)
    except Exception as e:
        print(f"Error: {e}")
        return

    prompts_to_sync = {
        "TA_ROUTER_PROMPT": _ROUTER_PROMPT,
        "TA_RETRIEVE_REFINE_PROMPT": _RETRIEVE_REFINE_PROMPT,
        "TA_DEEP_CHECK_PROMPT": _DEEP_CHECK_PROMPT,
        "TA_TEACH_UNDERSTAND_PROMPT": _TEACH_UNDERSTAND_PROMPT,
        "TA_TEACH_REVIEW_PROMPT": _TEACH_REVIEW_PROMPT,
        "TA_TEACH_CONTINUE_PROMPT": _TEACH_CONTINUE_PROMPT,
        "TA_TEACH_EVAL_PROMPT_V2": _TEACH_EVAL_PROMPT_V2,
        "TA_NEXT_TOPIC_PROMPT": _NEXT_TOPIC_PROMPT,
        "TA_PROPOSAL_PRESENT_PROMPT": _PROPOSAL_PRESENT_PROMPT,
    }

    # Add dictionaries
    for k, v in _RESEARCH_STRATEGY_PROMPT.items():
        prompts_to_sync[f"TA_RESEARCH_STRATEGY_PROMPT_{k.upper()}"] = v
        
    for k, v in _ROADMAP_PROMPT.items():
        prompts_to_sync[f"TA_ROADMAP_PROMPT_{k.upper()}"] = v

    print(f"Prompt file exist {len(prompts_to_sync)} to sync.")

    for name, content in prompts_to_sync.items():
        print(f"   -> Đang push '{name}'...")
        try:

            import re
            lf_content = re.sub(r'(?<!\{)\{([a-zA-Z0-9_]+)\}(?!\})', r'{{\1}}', content)

            langfuse.create_prompt(
                name=name,
                type="text",
                prompt=lf_content,
                labels=["production"]
            )
            print(f"✅✅✅ Push success '{name}'")
        except Exception as e:
            print(f"Error: {e}")

    langfuse.flush() # Queueing for async push
    print("Complete full sync!")

if __name__ == "__main__":
    sync_all_prompts()
