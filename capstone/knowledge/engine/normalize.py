import asyncio
import aiohttp
import time
import os

# --- CẤU HÌNH ---
USER_AGENT = "EduNodeApp/1.0 (dev_test_mode@example.com)"
API_URL = "https://www.wikidata.org/w/api.php"
LIMIT = 10
SUBJECT_FILE = "subjects.csv"

if not os.path.exists(SUBJECT_FILE):
    with open(SUBJECT_FILE, "w", encoding="utf-8") as f:
        random = [
            "programming", "software", "algorithm", "computer", "science", 
            "mathematics", "university", "technology", "framework", "library",
            "education", "intelligence", "learning", "data", "system", "city"
        ]
        f.write("\n".join(random))

def load_filter_keywords(filepath):
    """Đọc file CSV/TXT và trả về set các từ khóa (lowercase)"""
    keywords = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                clean_line = line.strip().lower()
                if clean_line:
                    keywords.add(clean_line)
    except Exception as e:
        print(f"⚠️ Không đọc được file filter: {e}")
    return keywords

async def _fetch_single(session, semaphore, text, filter_keywords):
    """
    Tìm kiếm và LỌC kết quả dựa trên description.
    """
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": text,
        "limit": 5  
    }
    
    async with semaphore:
        try:
            async with session.get(API_URL, params=params) as response:
                if response.status != 200:
                    return {"query": text, "id": None, "error": f"HTTP {response.status}"}
                
                data = await response.json()
                candidates = data.get("search", [])
                
                if not candidates:
                    return {"query": text, "id": None, "error": "Not found in Wikidata"}

           
                for cand in candidates:
                    desc = cand.get("description", "").lower()
                    
      
                    if any(kw in desc for kw in filter_keywords):
                        return {
                            "query": text,
                            "id": cand["id"],
                            "label": cand["label"],
                            "desc": cand.get("description", ""),
                            "match_type": "filtered" 
                        }
                
                return {
                    "query": text, 
                    "id": None, 
                    "error": "Filtered out (No matching subject description)"
                }
                    
        except Exception as e:
            return {"query": text, "id": None, "error": str(e)}

async def resolve_wikidata_ids(queries: list[str], filter_filepath: str, concurrency: int = None) -> list[dict]:
    filter_keywords = load_filter_keywords(filter_filepath)
    print(f"🔥 Đã load {len(filter_keywords)} từ khóa bộ lọc chủ đề.")

    if concurrency is None:
        concurrency = LIMIT
    semaphore = asyncio.Semaphore(concurrency)
    headers = {"User-Agent": USER_AGENT}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Truyền filter_keywords vào từng task
        tasks = [_fetch_single(session, semaphore, q, filter_keywords) for q in queries]
        results = await asyncio.gather(*tasks)
        return results

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    # Test case khó: 
    # "Java" -> Có thể là đảo Java (Indonesia) hoặc ngôn ngữ lập trình.
    # "Python" -> Có thể là con trăn hoặc ngôn ngữ lập trình.
    real_queries = [
        "Java",      # Hy vọng ra Programming Language
        "Python",    # Hy vọng ra Programming Language
        "Hanoi",     # Hy vọng ra City
        "Mars",      # Hy vọng tạch (vì ko có keyword 'planet' trong file mẫu)
        "TensorFlow"
    ]

    print(f"--- Đang xử lý {len(real_queries)} từ khóa ---")
    start = time.time()
    
    results = asyncio.run(resolve_wikidata_ids(real_queries, SUBJECT_FILE))
    
    end = time.time()
    print(f"Hoàn thành trong: {end - start:.2f} giây\n")
    
    for item in results:
        status = "✅" if item["id"] else "❌"
        desc_text = item.get('desc', 'No desc')
        print(f"{status} Query: {item['query']:<12} -> Label: {item.get('label', 'N/A'):<20} | Desc: {desc_text}")