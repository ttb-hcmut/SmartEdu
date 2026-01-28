import asyncio
import aiohttp
import time
import os
import spacy

# --- CONFIGURATION ---
USER_AGENT = "EduCapstoneBot/1.0 (dev_mode@student.edu)"
API_URL = "https://www.wikidata.org/w/api.php"
LIMIT = 10
SUBJECT_FILE = "subjects.csv"

# --- 1. SETUP SPACY & STOPWORDS ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("⚠️ Downloading Spacy model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Các tính từ chung chung cần loại bỏ
GENERIC_ADJECTIVES = {
    "good", "bad", "great", "poor", "excellent",
    "simple", "complex", "basic", "advanced", 
    "general", "specific", "various", "different",
    "main", "key", "important", "significant", "the", "a", "an"
}

# --- 2. UTILS ---
if not os.path.exists(SUBJECT_FILE):
    with open(SUBJECT_FILE, "w", encoding="utf-8") as f:
        defaults = [
            "programming", "software", "algorithm", "computer", "science", 
            "mathematics", "university", "technology", "framework", "library",
            "education", "intelligence", "learning", "data", "system", "city",
            "field", "discipline", "branch", "concept", "method", "term"
        ]
        f.write("\n".join(defaults))

def load_filter_keywords(filepath):
    keywords = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                clean = line.strip().lower()
                if clean: keywords.add(clean)
    except Exception:
        pass
    return keywords

def nlp_normalize(text: str) -> str:
    """
    Làm sạch chuỗi input: Bỏ mạo từ, tính từ chung, đưa về số ít.
    """
    doc = nlp(text)
    clean_tokens = []
    
    for token in doc:
        if token.pos_ in ["PUNCT", "SPACE"]:
            continue
            
        # Bỏ mạo từ (DET) đầu câu hoặc tính từ chung chung (ADJ)
        if (token.pos_ == "DET") or \
           (token.pos_ == "ADJ" and token.lemma_.lower() in GENERIC_ADJECTIVES):
            continue

        # Lemmatize: Đưa danh từ số nhiều về số ít
        if token.tag_ == "NNS":
            clean_tokens.append(token.lemma_)
        else:
            clean_tokens.append(token.text)
            
    result = " ".join(clean_tokens)
    return result if result.strip() else text

# --- 3. ASYNC WORKER ---
async def _fetch_single(session, semaphore, search_text, filter_keywords):

    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": search_text,
        "limit": 5,
        "type": "item"
    }
    
    async with semaphore:
        try:
            async with session.get(API_URL, params=params) as response:
                if response.status != 200:
                    return search_text, {"id": None, "error": f"HTTP {response.status}"}
                
                data = await response.json()
                candidates = data.get("search", [])
                
                if not candidates:
                    return search_text, {"id": None, "error": "Not found", "used_query": search_text}

                for cand in candidates:
                    desc = cand.get("description", "").lower()
                    if any(kw in desc for kw in filter_keywords):
                        return search_text, {
                            "id": cand["id"],
                            "label": cand["label"],
                            "desc": cand.get("description", ""),
                            "status": "MATCH"}
                
                top_cand = candidates[0]
                return search_text, {
                    "id": top_cand["id"],
                    "label": top_cand["label"],
                    "desc": top_cand.get("description", ""),
                    "status": "FALLBACK"
                }
                    
        except Exception as e:
            return search_text, {"id": None, "error": str(e)}

async def wiki_resolver(queries: list, filter_filepath: str, concurrency: int = None) -> dict:
    filter_keywords = load_filter_keywords(filter_filepath)
    if concurrency is None:
        concurrency = LIMIT
    semaphore = asyncio.Semaphore(concurrency)
    
    headers = {"User-Agent": USER_AGENT}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for q in queries:

            tasks.append(_fetch_single(session, semaphore, q, filter_keywords))
            
        results = await asyncio.gather(*tasks)
        return {k: v for k, v in results}

# --- 4. TEST ---
if __name__ == "__main__":
    real_queries = [
        "The Good Algorithms",       # -> Algorithm
        "Advanced Python Programming", # -> Python Programming
        "Simple Linear Regression",  # -> Linear Regression
        "Decision Trees",            # -> Decision Tree (Số ít)
        "Hanoi",
        "Mars",
        "Deep Learning"              # -> Deep Learning (Giữ nguyên)
    ]

    print(f"Processing {len(real_queries)} queries...")
    start = time.time()
    
    # Windows fix cho asyncio loop
    try:
        results = asyncio.run(wiki_resolver(real_queries, SUBJECT_FILE))
    except RuntimeError: # Jupyter/Special enviroment handling
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(wiki_resolver(real_queries, SUBJECT_FILE))

    end = time.time()
    print(f"Completed in: {end - start:.2f} seconds\n")
    
    for query in real_queries:
        data = results.get(query)
        print(f"Origin: '{query}'")
        if data:
            print(f" -> Cleaned: '{data.get('cleaned_name')}'")
            print(f" -> Found: {data.get('label')} ({data.get('id')}) - {data.get('desc')}")
        else:
            print(" -> Error/Not found")
        print("-" * 40)