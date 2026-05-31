"""These shots are synthesis by Sonnet 4.5
These shots are the hard boundary cases only — no obvious anchor spam"""
# TA/edu/workflow/few_shot.py 
## -- Few-shot examples for TA_Router intent classification
## -- Design principles:
##    1. Hard boundary cases ONLY — no obvious anchor spam
##    2. Include state_hint + history_hint for context-dependent cases
##    3. WHY annotations are for developer docs only, NOT injected into the prompt
##    4. Compact output format to respect the 4096 token context window budget
##
## -- Context window budget estimate (TA profile, num_ctx=4096):
##    student_state  : ~200-400 tokens
##    chat_history   : ~300-600 tokens
##    prompt base    : ~150 tokens
##    few_shot output: target ≤ 500 tokens  ← THIS FILE controls this
##    query          : ~20-100 tokens
##    safety margin  : ~400 tokens
##    ────────────────────────────────────
##    total target   : ≤ 2000 tokens (leaves room for num_ctx=4096)

# ─────────────────────────────────────────────────
# Schema of each example:
#   query       : the student's raw input
#   state_hint  : (optional) relevant part of student_state that matters for this decision
#   history_hint: (optional) last TA message that affects classification
#   intent      : ground-truth label
#   why         : developer-only note, NEVER injected into prompt
# ─────────────────────────────────────────────────

_VN_EXAMPLES = [

    # ── NHÓM 1: CASE DỄ (Anchor Cases - Giúp model hình dung nhiệm vụ cơ bản) ────────────
    {
        "query": "SVM là gì?",
        "state_hint": "",
        "history_hint": "",
        "intent": "retrieve",
        "why": "[EASY_RETRIEVE] Pure factual definition question.",
    },
    {
        "query": "Tôi muốn bắt đầu học Deep Learning",
        "state_hint": "",
        "history_hint": "",
        "intent": "roadmap",
        "why": "[EASY_ROADMAP] Expressing a goal to learn a subject with no current position requires a plan.",
    },
    {
        "query": "I want to learn Machine Learning",
        "state_hint": "",
        "history_hint": "",
        "intent": "roadmap",
        "why": "[EASY_ROADMAP_BILINGUAL] English query fallback under default vn context.",
    },
    {
        "query": "Dạy tôi bài mới",
        "state_hint": "current_pos: Neural Network",
        "history_hint": "",
        "intent": "teaching",
        "why": "[EASY_TEACHING] Direct request to start or continue teaching.",
    },
    {
        "query": "Đồng ý",
        "state_hint": "pending_proposal: roadmap đến CNN",
        "history_hint": "TA: 'Bạn có đồng ý áp dụng lộ trình này không?'",
        "intent": "confirm",
        "why": "[EASY_CONFIRM] Positive confirmation with a pending proposal active.",
    },
    {
        "query": "Thời tiết hôm nay thế nào?",
        "state_hint": "",
        "history_hint": "",
        "intent": "unknown",
        "why": "[EASY_UNKNOWN] Completely off-topic query.",
    },

    # ── NHÓM 2: CASE KHÓ & BẪY (Hard/Trap/Context-dependent Cases) ────────────
    {
        "query": "Ok",
        "state_hint": "pending_proposal: roadmap đến CNN",
        "history_hint": "TA: 'Bạn có muốn áp dụng lộ trình này không?'",
        "intent": "confirm",
        "why": "[CTX] 'Ok' alone is ambiguous; pending_proposal + TA's confirmation question → confirm.",
    },
    {
        "query": "Tôi hiểu rồi",
        "state_hint": "pending_proposal: null",
        "history_hint": "TA: 'SVM phân loại dữ liệu bằng hyperplane.'",
        "intent": "unknown",
        "why": "[CTX][TRAP] Same words, but no proposal pending → student is just reacting, not confirming.",
    },
    {
        "query": "Tiếp tục đi",
        "state_hint": "current_pos: Neural Network",
        "history_hint": "TA: 'Phần 1 về Forward Pass hoàn thành. Bạn có câu hỏi không?'",
        "intent": "teaching",
        "why": "[CTX] Active lesson in history → 'tiếp tục' = resume lesson, teaching.",
    },
    {
        "query": "Tiếp tục đi",
        "state_hint": "current_pos: null",
        "history_hint": "",
        "intent": "roadmap",
        "why": "[CTX] No current position, no lesson history → 'tiếp tục' = 'where do I go?', roadmap.",
    },
    {
        "query": "Backpropagation hoạt động như thế nào?",
        "state_hint": "",
        "history_hint": "",
        "intent": "retrieve",
        "why": "[A→B] Mechanism question → factual lookup, not a full lecture. 'Như thế nào' = retrieve.",
    },
    {
        "query": "Giải thích chi tiết từng bước của Backpropagation, kèm ví dụ số",
        "state_hint": "",
        "history_hint": "",
        "intent": "teaching",
        "why": "[A→B] 'Chi tiết từng bước, kèm ví dụ số' = deep structured session, teaching.",
    },
    {
        "query": "Lộ trình học CNN là gì?",
        "state_hint": "",
        "history_hint": "",
        "intent": "retrieve",
        "why": "[TRAP] 'Lộ trình' keyword but asking about a concept definition, not requesting a personal plan.",
    },
    {
        "query": "Dạy tôi biết SVM là gì",
        "state_hint": "",
        "history_hint": "",
        "intent": "retrieve",
        "why": "[TRAP] 'Dạy tôi' but purely definitional → retrieve.",
    },
    {
        "query": "Cái này có khó không?",
        "state_hint": "",
        "history_hint": "",
        "intent": "unknown",
        "why": "[TRAP] 'Cái này' has no referent. Cannot classify.",
    },

    # ── NHÓM 3: CASE DÀI & NHIỀU DỮ KIỆN (Long, Multi-intent/Context-rich Cases) ────────────
    {
        "query": "Chào trợ lý, em đã học qua cơ bản về Python rồi, bây giờ em đang muốn tìm hiểu sâu về mảng trí tuệ nhân tạo, cụ thể là Neural Network và học sâu. Anh gợi ý cho em nên bắt đầu từ đâu và học theo lộ trình như thế nào để tối ưu nhất ạ?",
        "state_hint": "current_pos: null",
        "history_hint": "",
        "intent": "roadmap",
        "why": "[LONG_ROADMAP] Multiple context elements (learned Python, AI/NN interest) but core request is studying a new topic from scratch with a roadmap.",
    },
]

_ENG_EXAMPLES = [

    # ── NHÓM 1: CASE DỄ (Anchor Cases - Giúp model hình dung nhiệm vụ cơ bản) ────────────
    {
        "query": "What is SVM?",
        "state_hint": "",
        "history_hint": "",
        "intent": "retrieve",
        "why": "[EASY_RETRIEVE] Pure factual definition question.",
    },
    {
        "query": "I want to learn Machine Learning",
        "state_hint": "",
        "history_hint": "",
        "intent": "roadmap",
        "why": "[EASY_ROADMAP] Expressing a goal to learn a subject with no current position requires a plan.",
    },
    {
        "query": "I want to start learning Deep Learning",
        "state_hint": "",
        "history_hint": "",
        "intent": "roadmap",
        "why": "[EASY_ROADMAP] Expressing desire to start a new subject.",
    },
    {
        "query": "Start a new lesson for me",
        "state_hint": "current_pos: Neural Network",
        "history_hint": "",
        "intent": "teaching",
        "why": "[EASY_TEACHING] Direct request to start teaching.",
    },
    {
        "query": "I agree",
        "state_hint": "pending_proposal: roadmap to CNN",
        "history_hint": "TA: 'Do you agree to apply this roadmap?'",
        "intent": "confirm",
        "why": "[EASY_CONFIRM] Positive confirmation with a pending proposal active.",
    },
    {
        "query": "How is the weather today?",
        "state_hint": "",
        "history_hint": "",
        "intent": "unknown",
        "why": "[EASY_UNKNOWN] Completely off-topic query.",
    },

    # ── NHÓM 2: CASE KHÓ & BẪY (Hard/Trap/Context-dependent Cases) ────────────
    {
        "query": "Sure",
        "state_hint": "pending_proposal: roadmap to CNN",
        "history_hint": "TA: 'Do you want to apply this learning path?'",
        "intent": "confirm",
        "why": "[CTX] Affirmative + pending proposal → confirm.",
    },
    {
        "query": "I see",
        "state_hint": "pending_proposal: null",
        "history_hint": "TA: 'SVM classifies data using a hyperplane.'",
        "intent": "unknown",
        "why": "[CTX][TRAP] Reaction with no pending proposal → unknown.",
    },
    {
        "query": "Continue",
        "state_hint": "current_pos: Neural Network",
        "history_hint": "TA: 'Part 1 on Forward Pass is done. Any questions?'",
        "intent": "teaching",
        "why": "[CTX] Active lesson → 'continue' = resume lesson.",
    },
    {
        "query": "Continue",
        "state_hint": "current_pos: null",
        "history_hint": "",
        "intent": "roadmap",
        "why": "[CTX] No lesson context → 'continue' = where do I go next? roadmap.",
    },
    {
        "query": "How does backpropagation work?",
        "state_hint": "",
        "history_hint": "",
        "intent": "retrieve",
        "why": "[A→B] 'How does X work' = mechanism factual lookup, not a full lecture.",
    },
    {
        "query": "Walk me through backpropagation step by step with a numeric example",
        "state_hint": "",
        "history_hint": "",
        "intent": "teaching",
        "why": "[A→B] 'Walk me through, step by step, numeric example' = deep structured session.",
    },
    {
        "query": "What does a Deep Learning roadmap look like?",
        "state_hint": "",
        "history_hint": "",
        "intent": "retrieve",
        "why": "[TRAP] Asking ABOUT a roadmap concept = retrieve, not requesting a personal plan.",
    },
    {
        "query": "Teach me what SVM is",
        "state_hint": "",
        "history_hint": "",
        "intent": "retrieve",
        "why": "[TRAP] 'Teach me' + purely definitional → retrieve.",
    },
    {
        "query": "Is this difficult?",
        "state_hint": "",
        "history_hint": "",
        "intent": "unknown",
        "why": "[TRAP] 'Is this difficult' has no referent. Cannot classify.",
    },

    # ── NHÓM 3: CASE DÀI & NHIỀU DỮ KIỆN (Long, Multi-intent/Context-rich Cases) ────────────
    {
        "query": "Hello assistant! I have already mastered basic Python and some statistics. Now I want to shift my career to AI, specifically deep learning and computer vision. Could you guide me on where to start and suggest a comprehensive roadmap for me?",
        "state_hint": "current_pos: null",
        "history_hint": "",
        "intent": "roadmap",
        "why": "[LONG_ROADMAP] Multiple context elements (Python, stats background) but core request is requesting a learning path for AI/deep learning.",
    },
]

FEW_SHOT_EXAMPLES = {
    "vn": _VN_EXAMPLES,
    "eng": _ENG_EXAMPLES,
}


def format_few_shot(language: str = "vn") -> str:
    """
    Format few-shot examples for injection into the Router prompt.

    Compact format to respect context window budget (target ≤ 500 tokens):
      [S: state_hint] [H: history_hint] "query" → intent

    WHY annotations are intentionally EXCLUDED from output — they are
    developer docs only. The compact format is what the LLM sees.
    """
    examples = FEW_SHOT_EXAMPLES.get(language, FEW_SHOT_EXAMPLES["vn"])
    lines = []
    for e in examples:
        parts = []
        if e.get("state_hint"):
            parts.append(f'[S: {e["state_hint"]}]')
        if e.get("history_hint"):
            parts.append(f'[H: {e["history_hint"]}]')
        parts.append(f'"{e["query"]}" → {e["intent"]}')
        lines.append("  " + " ".join(parts))
    return "\n".join(lines)


LANGUAGE_INSTRUCTIONS = {
    "vn": "Bạn PHẢI trả lời bằng Tiếng Việt trong mọi trường hợp.",
    "eng": "You MUST respond in English in all cases.",
}


def get_language_instruction(language: str = "vn") -> str:
    return LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["vn"])
