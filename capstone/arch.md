└── capstone
    ├── arch.md
    ├── core
    │   ├── api
    │   │   └── life_span.py
    │   ├── dependencies.py
    │   ├── llm
    │   │   ├── config.py
    │   │   └── llm_engine.py
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
    │   │   │   └── mil.py
    │   │   ├── nosql
    │   │   │   └── mongo.yml
    │   │   ├── sql
    │   │   │   └── mysql.yml
    │   │   ├── storage
    │   │   │   └── minio_repo.py
    │   │   └── util
    │   ├── schema
    │   │   ├── factory.py
    │   │   └── graph
    │   │       ├── graph.py
    │   │       ├── ontology.py
    │   │       └── type.py
    │   └── util
    │       └── file_extractor.py
    ├── knowledge
    │   ├── api
    │   │   ├── health.py
    │   │   └── route.py
    │   ├── engine
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
    ├── subjects.csv
    ├── TA
    │   ├── agent
    │   │   └── base.py
    │   ├── api
    │   │   └── route.py
    │   ├── core
    │   │   └── config.py
    │   ├── tools
    │   │   └── neo
    │   │       ├── base.py
    │   │       └── neo.py
    │   └── workflow.py
    ├── test_script
    │   ├── graph.py
    │   └── neo.py
    └── test.py
