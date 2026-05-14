# User definition:
## WF logic
Workflow 1: Retrieve:
Step 1:  Retriever tự compose câu hỏi và retrieve câu trả lời # input: query
Step 2: Nếu work, TA trả lời ng dùng fail thì phải suy nghĩ câu hỏi để làm rõ ý # input: state + prompt chuyên biệt hướng dẫn cách trl

Workflow 2: Roadmap
Step 1: RAG khám phá dựa trên yêu cầu của người dùng và update vị trí từ Evaluator  # input: (query , state[last_state]) Nếu chỉ đưa message cảm giác ko ổn, nhg đưa hết thì quá nhiều.
Step 2: Evaluator nhận kq explorer và phản biện # input: (query , state[last_state])
Step 3: TA nhận kq cả hai và đưa ra advice cho ng dùng # input: (query , state[last_state])

Workflow 3: Teaching
Step 1:  Evaluator lấy tình trạng hiện tại ng dùng, quan trọng là vị trí node hiện tại update vô Student State # input: None
Step 2: TA đọc student state, access document chứa node hiện tại và giảng (kiểu như bookRAG). Tôi thấy graph ko chứa đc đầy đủ thông tin nên vẫn nên mở cả pdf cho người dùng và TA thấy và giảng dựa trên đó # prompt hướng dẫn dùng tool mở pdf text và raw trên minio
Step 3: Người dùng tương tác và Evaluator nhận thông tin, assess, cuối cùng gọi tool update kq cuối cùng. Dựa vào thang Bloom để setup review time (const đi). 

*** TA sẽ quyết định người dùng muốn làm gì để route đến Workflow thích hợp

## User:
Qua teach.py thiết kế wf3, Teach. Đây là workflow khó nhất. Cần ngắn gọn đáp ứng real time nhg vẫn cần đầy đủ. TA cần quyết định đc 3 option:
- Giảng nội dung note: Hiểu nội dung note, dùng explore current node, ko có phải recommend new. Tự giảng và đưa ra các caau hỏi để thử thách người dùng 
- Qua Gen tạo bài tập: Tự prompt bài tập hợp lý để agent làm. Để tăng tốc độ nên làm song song (TA vừa giảng vừa gửi lên agent["Generator])
- access resource qua tool Minio (show text đầy đủ, show giao diện slide đúng trang có nội dung cần tìm), sử dụng các tool tương tác MiniO

## user:
Wf Teach chia làm 2 giai đoạn chính:
Phase 1: Understand
1. Hiểu cần làm gì: Kiếm tìm thông tin theo yêu cầu người dùng, hay ôn lại hay dạy tiếp
2. Ôn lại: Lấy prev_node và prev page (n = 3)
3. Tiếp: 
- nếu history trống, review lại node hiện tại
- 
4. Kiếm tìm: làm giống retrieve. Có thể gọi lại tôi cx đang cân nhắc hợp nhất WF1 và WF3, do tôi đã quên là cần phải tra xem concept có trong current page hay current node hay ở ngoài. Nếu ở ngoài cần gọi tool để đo khoảng cách

Phase 2: Present
1. Prompt Agent check nội dung cần show (Ko nhất thiết cần current_node, có thể là kq retrieve)
2. Nếu là current node: 
- Gọi tool current_resources(n=1): gọi current_resource trong Student_Tracker
- current_resource trả về các trang, prompt agent mở đúng trang
3. Nếu ko:
- get_concept_page(): tool này khá khác vs get_content của RAG, nó sẽ lấy từ ref trong node vừa lấy đc (khả năng cao phải lưu rag_node đâu đó trong student_tracker, vdu có temp memo gì đó)
4. Giảng: Prompt để nó nói từng dòng 1

Lưu ý:
1. So sánh hay các ope liên quan tới resources phải = path, nhg ko show cho agent (ko cần thiết)
2. Ít tool nhất có thể

## Tổng hợp thiết kế
1. life_span.py: app khởi tạo các  (bản chất là các resource manager do khác vs logical instances resource chỉ 1) như db, student_tracker và LLM_engine rồi inject vô TA module
2. TA/ta_module.py: TA_Module đóng vai trò như interface instance của cả logical module:
init: 
- nhận resources, khởi tạo agent và tool thông qua việc inject resource vào các factory gọi từ TA/tools/factory.py và TA/agent/injector.py
- Inject agent và workflow engine SmartEdu (Langgraph chân chính chứa logic chạy agent)
- nhận query từ FE (hiện chưa có module fe), invoke workflow với session xác định do bản thân nó quản lý (hiện đang chưa có session, assume việc học là tiếp diễn liên tục)

3. TA/edu/smart_edu.py: 
- chứa logic workflow của 3 wf trong folder TA/edu/workflow/
- hiện nhận student_tracker trong config để thực hiện những hành vi deterministic mà rủi ro khi gọi trong tools (hiện đang bị mắc lỗi chưa có id từ logic non\-singleton cũ). Hiện tôi đang phân vân giữa việc để argschema của toàn bộ tool bằng 1 BaseToolInput(BaseModel): -id -filter: str = None (vdu tìm node có mastery thấp hơn ...... để string để tránh vc nhiều filter dễ gây rủi ro)
- trả về output là string


========================================== Không được tóm tắt hay bỏ phần trên =========================================

# SmartEdu TA - Architecture & Implementation Document
(Tài liệu tóm tắt thiết kế, logic workflow, prompt và kế hoạch hoàn thiện Database)

## 1. Kiến trúc Hệ thống & Workflow Logic
Hệ thống sử dụng kiến trúc Singleton cho các core resources và Dependency Injection để truyền state một cách an toàn. Tài nguyên được chia tách: Core GraphDB (chứa kiến thức) và Student GraphDB/MongoDB (chứa tiến độ học).

### Workflow 1: Retrieve (Truy xuất kiến thức)
- **Luồng (Pipeline):** `RAG_Core` -> `Deep_Decision` -> `rag_deep`.
- **Prompt & Hoạt động:** 
  - Sử dụng `RESEARCH_STRATEGY_PROMPT['core']` để Agent tìm kiếm trên Graph. 
  - Nếu thành công, `DEEP_CHECK_PROMPT` phân tích khoảng cách (gap) giữa `current_pos` của user và kiến thức mới. 
  - Nếu độ chênh lệch lớn (`is_deep=true`), chạy tiếp `RESEARCH_STRATEGY_PROMPT['deep']` để sinh ra `bridge_concepts` (kiến thức bắc cầu) và tạo Proposal.

### Workflow 2: Roadmap (Tư vấn lộ trình)
- **Luồng (Pipeline):** Explore -> Evaluate -> Advice.
- **Prompt & Hoạt động:** 
  - **Explore**: Gọi tool (`RecommendNew`, `CourseBackbone`, `CourseRelevance`) để tìm hub nodes.
  - **Evaluate**: Dùng prompt phản biện tính khả thi dựa vào prerequisites và Mastery của user.
  - **Advice**: Tổng hợp lời khuyên và trả về `pending_proposal` chờ user xác nhận (`confirm`).

### Workflow 3: Teaching (Dạy học thời gian thực - V3)
- **Luồng (Pipeline):** Understand -> Lecture (Review/Continue) -> Evaluate -> Next_Topic.
- **Prompt & Hoạt động:** 
  - **Understand**: `TEACH_UNDERSTAND_PROMPT` phân loại chat history để xác định intent.
  - **Lecture**: `TEACH_REVIEW_PROMPT` và `TEACH_CONTINUE_PROMPT` hướng dẫn Agent tự dùng tool lấy tài liệu PDF, lật trang FE và giảng bài. Không dùng structured output để hỗ trợ Streaming text.
  - **Evaluate**: Dùng `TEACH_EVAL_PROMPT_V2` chấm điểm năng lực user. Ép kiểu JSON (`TeachEvalOutput`).
  - **Next_Topic**: Dùng `NEXT_TOPIC_PROMPT` để chọn node liền kề, cập nhật `student_state` và đưa ra Proposal.

## 2. Thiết kế Tool & Context Bounded
- **Context Bounded**: Dùng Queue (maxlen=5) cho `recent_pages`, `previous_nodes`. Lịch sử hội thoại được nhúng trong `Memo` để chặn token overflow.
- **Agentic Tools**: 
  - Mọi args_schema của Tool **KHÔNG** chứa `student_id`.
  - ID được luân chuyển an toàn thông qua biến `RunnableConfig` (`app.ainvoke(config=run_config)`).

---

## 3. Detailed Implementation Plan (Kế hoạch Code)
Dựa trên codebase mới nhất, hệ thống cần được hoàn thiện qua 3 giai đoạn:

### Giai đoạn 1: Hoàn thiện Schema Database (MongoDB & Neo4j)
**1. MongoDB (Nested Memo schema):**
- **Vấn đề:** Thiết kế mới yêu cầu lưu lịch sử chat (`memo`) lồng vào bên trong `student_states` gom theo nhóm `session_id`, thay vì nằm rải rác ở collection `chat_history`.
- **Sửa `core/repo/nosql/mongo_db.py`**:
  - `create_student`: Thêm field `"memo": {}`.
  - `push_to_history`: Đổi logic để `$push` dictionary (gồm `role`, `heading`, `message`, `timestamp`) vào key `f"memo.{session_id}"` của document `student_states`.
  - `get_recent_history`: Lấy list từ `memo.session_id` và cắt lấy `limit` item cuối.
- **Sửa `student/memo.py`**:
  - Truyền thêm `session_id` vào `save_callback` để DB biết đang tương tác ở phiên nào.

**2. Xung đột Neo4j (Core Graph vs Student Graph):**
- **Vấn đề Cực kỳ quan trọng:** `ToolFactory` đang truy vấn trên `graph_db` (chứa Course), nhưng query Cypher trong `TA/tools/neo/explore.py` lại có đoạn `OPTIONAL MATCH (s:Student)-[:MASTERY]->(n)`. Lệnh này sẽ trả về null vì Student nằm ở DB khác (`graph_db_student` do `Student_Tracker` quản lý).
- **Sửa `TA/tools/neo/explore.py`**:
  - Xóa toàn bộ line `OPTIONAL MATCH (s:Student)...` khỏi mọi query Cypher.
  - Cypher chỉ thuần túy query cấu trúc Graph (Hubs, Backbone, v.v.).
  - Ở tầng Python (trong hàm `_run`), sử dụng `self.tracker.get_mastery(student_id, node['name'])` để map mức độ thành thạo vào `ConceptNode` trước khi trả về cho LLM.

### Giai đoạn 2: Refactor Singleton Dependency Injection
- **Sửa `TA/tools/neo/base.py`**: Đổi `tracker: Student_Tracker = Student_Tracker()` thành `tracker: Optional[Any] = Field(default=None, exclude=True)` để không tạo instance rác.
- **Sửa `TA/tools/factory.py`**: Thêm `tracker` vào params khởi tạo. Chèn `tracker=self.tracker` vào constructor của các tool Neo4j.
- **Sửa `TA/ta_module.py`**: Khởi tạo `ToolFactory` với `tracker=self.student_tracker`.

### Giai đoạn 3: Bọc LLM Evaluator (Ollama Fix)
- **Sửa `TA/edu/utils.py`**: Bổ sung hàm `llm_(base, temp, schema)` để sinh ra model instance chuyên bind output JSON.
- **Sửa `TA/edu/workflow/teach.py`**: Áp dụng hàm `wrap_agent_structured` cho node `teach_evaluate` để đảm bảo ChatOllama không crash ở runtime.

---

## Nhật ký cập nhật
- **Trạng thái**: Đã kiểm tra và hoàn tất toàn bộ 3 Giai đoạn trên.
- **Bổ sung bổ trợ**: Đã sửa lỗi caching `session_id` trong `student/memo.py` và `Student_Tracker.py`. Thêm `session_id` vào class `Memo` và update lại lambda `save_callback` cùng logic của hàm `get_session()` để đảm bảo DB lưu đúng session khi có thay đổi phiên làm việc của user.
