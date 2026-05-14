# Nhiệm vụ: trong TA/ xây hệ thống SmartEdu thông minh


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



└── capstone
    ├── arch.md
    ├── core
    │   ├── api
    │   │   └── life_span.py
    │   ├── config.py
    │   ├── dependencies.py
    │   ├── llm
    │   │   ├── config.py
    │   │   ├── llm_engine.py
    │   │   └── prompt
    │   │       ├── agents.py
    │   │       └── graph.py
    │   ├── model
    │   │   └── embedding.py
    │   ├── repo
    │   │   ├── docker-compose.yaml
    │   │   ├── graph
    │   │   │   ├── graphdb.py
    │   │   │   ├── insert.py
    │   │   │   ├── neo4j.yaml
    │   │   │   └── utils
    │   │   ├── milvus_db
    │   │   │   ├── etcd_data
    │   │   │   ├── mil.py
    │   │   │   └── milvus.yml
    │   │   ├── nosql
    │   │   │   └── mongo.yml
    │   │   ├── sql
    │   │   │   ├── mysql.yml
    │   │   │   └── sql_db
    │   │   ├── storage
    │   │   │   └── minio_repo.py
    │   │   └── util
    │   │       └── __init__.py
    │   ├── schema
    │   │   ├── factory.py
    │   │   ├── graph
    │   │   │   ├── __init__.py
    │   │   │   ├── graph.py
    │   │   │   ├── ontology.py
    │   │   │   └── type.py
    │   │   └── wf_state.py
    │   └── util
    │       └── file_extractor.py
    ├── data
    │   ├── Chapter 1 - Introduction.pdf
    │   ├── Chapter 2 - Decision Tree.pdf
    │   ├── Chapter 3 - Bayesian Learning.pdf
    │   ├── Chapter 4 - Genetic Algorithms.pdf
    │   ├── Chapter 5 - Graphical Models.pdf
    │   ├── Chapter 6 - SVM.pdf
    │   └── Dimensionality Reduction.pdf
    ├── knowledge
    │   ├── api
    │   │   ├── health.py
    │   │   └── route.py
    │   ├── engine
    │   │   ├── __init__.py
    │   │   ├── extract.py
    │   │   ├── graph
    │   │   │   ├── graph_constructor.py
    │   │   │   ├── helper
    │   │   │   │   ├── analyzer.py
    │   │   │   │   ├── normalize.py
    │   │   │   │   └── taxonomy.py
    │   │   │   ├── prompt.py
    │   │   │   ├── template.html
    │   │   │   └── visualize_kg.py
    │   │   └── subjects.csv
    │   ├── knowledge_construction_service.py
    │   └── service
    │       └── course_ingest.py
    ├── main.py
    ├── README.md
    ├── run_test.py
    ├── subjects.csv
    └── TA
        ├── agent
        │   ├── base.py
        │   └── injector.py
        ├── api
        │   └── route.py
        ├── des.md
        ├── edu  # hiện đang work folder này
        │   ├── smart_edu.py  # Lớp bên ngoài init graph tổng 
        │   ├── utils.py      # Các hàm tool
        │   └── workflow
        │       ├── prompt.py   # config prompt
        │       ├── retrieve.py # Workflow 1
        │       ├── roadmap.py  # Workflow 2
        │       ├── schema.py   # 
        │       └── teach.py    # Workflow 3
        ├── ta_module.py
        └── tools
            ├── factory.py
            └── neo
                ├── __init__.py
                ├── base.py
                ├── explore.py
                ├── retriever.py
                └── schema.py
