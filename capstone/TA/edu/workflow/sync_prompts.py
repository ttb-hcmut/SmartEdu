"""
Script để đồng bộ các prompt từ local (hardcoded) lên Langfuse Prompt Management.
Chạy script này một lần (hoặc khi có cập nhật lớn) để push prompts.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load env vars để lấy LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../core/.env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../tracing/.env"))

from langfuse import Langfuse
from TA.edu.workflow.prompt import (
    ROUTER_PROMPT,
    RETRIEVE_REFINE_PROMPT,
    DEEP_CHECK_PROMPT,
    RESEARCH_STRATEGY_PROMPT,
    ROADMAP_PROMPT,
    TEACH_UNDERSTAND_PROMPT,
    TEACH_REVIEW_PROMPT,
    TEACH_CONTINUE_PROMPT,
    TEACH_EVAL_PROMPT_V2,
    NEXT_TOPIC_PROMPT,
    PROPOSAL_PRESENT_PROMPT,
)

def sync_all_prompts():
    secret = os.getenv("LANGFUSE_SECRET_KEY")
    public = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not secret or not public:
        print("❌ Thiếu LANGFUSE_SECRET_KEY hoặc LANGFUSE_PUBLIC_KEY. Không thể push.")
        return

    print(f"🔄 Đang kết nối tới Langfuse tại {host}...")
    try:
        langfuse = Langfuse(secret_key=secret, public_key=public, host=host)
    except Exception as e:
        print(f"❌ Kết nối thất bại: {e}")
        return

    prompts_to_sync = {
        "TA_ROUTER_PROMPT": ROUTER_PROMPT,
        "TA_RETRIEVE_REFINE_PROMPT": RETRIEVE_REFINE_PROMPT,
        "TA_DEEP_CHECK_PROMPT": DEEP_CHECK_PROMPT,
        "TA_TEACH_UNDERSTAND_PROMPT": TEACH_UNDERSTAND_PROMPT,
        "TA_TEACH_REVIEW_PROMPT": TEACH_REVIEW_PROMPT,
        "TA_TEACH_CONTINUE_PROMPT": TEACH_CONTINUE_PROMPT,
        "TA_TEACH_EVAL_PROMPT_V2": TEACH_EVAL_PROMPT_V2,
        "TA_NEXT_TOPIC_PROMPT": NEXT_TOPIC_PROMPT,
        "TA_PROPOSAL_PRESENT_PROMPT": PROPOSAL_PRESENT_PROMPT,
    }

    # Add dictionaries
    for k, v in RESEARCH_STRATEGY_PROMPT.items():
        prompts_to_sync[f"TA_RESEARCH_STRATEGY_PROMPT_{k.upper()}"] = v
        
    for k, v in ROADMAP_PROMPT.items():
        prompts_to_sync[f"TA_ROADMAP_PROMPT_{k.upper()}"] = v

    print(f"📦 Tìm thấy {len(prompts_to_sync)} prompts để đồng bộ.")

    for name, content in prompts_to_sync.items():
        print(f"   -> Đang push '{name}'...")
        try:
            # Dùng text prompt (chuyển đổi {var} thành {{var}} để tương thích Langfuse UI syntax)
            # Vì ta sẽ dùng .get_langchain_prompt() để fetch về, ta có thể giữ nguyên {} 
            # hoặc đổi sang {{}} tuỳ chọn, nhưng an toàn nhất là lưu như hiện tại (chuẩn python str.format/langchain)
            # và khi tạo prompt trên Langfuse, ta để nguyên.
            # Tuy nhiên, Langfuse docs bảo "Variables in prompts are defined using double curly braces {{variable}}."
            # Do đó ta có thể replace {} -> {{}} nếu bên trong không có khoảng trắng.
            
            # Simple conversion for standard single brackets to double brackets for Langfuse compatibility
            import re
            # replace {var} with {{var}} but ignore {{ and }}
            lf_content = re.sub(r'(?<!\{)\{([a-zA-Z0-9_]+)\}(?!\})', r'{{\1}}', content)

            langfuse.create_prompt(
                name=name,
                type="text",
                prompt=lf_content,
                labels=["production"],
                is_active=True
            )
            print(f"      ✅ Push thành công '{name}' (label: production)")
        except Exception as e:
            print(f"      ❌ Lỗi khi push '{name}': {e}")

    # Đảm bảo dữ liệu được gửi hết
    langfuse.flush()
    print("🎉 Hoàn tất đồng bộ Prompts lên Langfuse!")

if __name__ == "__main__":
    sync_all_prompts()
