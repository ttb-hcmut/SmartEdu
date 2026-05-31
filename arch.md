```
└── Capstone
    ├── arch.md # This file
    ├── capstone
    │   ├── core
    │   │   ├── api
    │   │   │   └── life_span.py
    │   │   ├── config.py
    │   │   ├── dependencies.py
    │   │   ├── llm
    │   │   │   ├── config.py
    │   │   │   ├── llm_engine.py
    │   │   │   └── prompt
    │   │   │       ├── agents.py
    │   │   │       └── graph.py
    │   │   ├── model
    │   │   │   └── embedding.py
    │   │   ├── repo
    │   │   │   ├── docker-compose.yaml
    │   │   │   ├── graph
    │   │   │   │   ├── graphdb.py
    │   │   │   │   ├── insert.py
    │   │   │   │   ├── neo4j.yaml
    │   │   │   │   └── utils
    │   │   │   ├── milvus_db
    │   │   │   │   ├── etcd_data
    │   │   │   │   ├── mil.py
    │   │   │   │   └── milvus.yml
    │   │   │   ├── nosql
    │   │   │   │   ├── mongo_db.py
    │   │   │   │   └── mongo.yml
    │   │   │   ├── sql
    │   │   │   │   ├── mysql.yml
    │   │   │   │   └── sql_db.py
    │   │   │   ├── storage
    │   │   │   │   └── minio_repo.py
    │   │   │   └── util
    │   │   │       ├── __init__.py
    │   │   │       └── dbgate.yml
    │   │   ├── schema
    │   │   │   ├── factory.py
    │   │   │   ├── graph
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── graph.py
    │   │   │   │   ├── ontology.py
    │   │   │   │   └── type.py
    │   │   │   └── wf_state.py
    │   │   └── util
    │   │       └── file_extractor.py
    │   ├── knowledge
    │   │   ├── api
    │   │   │   ├── health.py
    │   │   │   └── route.py
    │   │   ├── engine
    │   │   │   ├── __init__.py
    │   │   │   ├── extract.py
    │   │   │   ├── graph
    │   │   │   │   ├── graph_constructor.py
    │   │   │   │   ├── helper
    │   │   │   │   │   ├── analyzer.py
    │   │   │   │   │   ├── normalize.py
    │   │   │   │   │   └── taxonomy.py
    │   │   │   │   ├── prompt.py
    │   │   │   │   ├── template.html
    │   │   │   │   └── visualize_kg.py
    │   │   │   └── subjects.csv
    │   │   ├── knowledge_construction_service.py
    │   │   └── service
    │   │       └── course_ingest.py
    │   ├── main.py
    │   ├── README.md
    │   ├── run_test.py
    │   ├── student
    │   │   ├── api.py
    │   │   ├── auth.py
    │   │   ├── memo.py
    │   │   ├── session_context.py
    │   │   └── Student_Tracker.py
    │   ├── subjects.csv
    │   ├── TA
    │   │   ├── agent
    │   │   │   ├── base.py
    │   │   │   ├── injector.py
    │   │   │   ├── middleware.py
    │   │   │   └── ollama_patch.py
    │   │   ├── api
    │   │   │   └── route.py
    │   │   ├── edu
    │   │   │   ├── helper
    │   │   │   │   ├── context.py
    │   │   │   │   ├── few_shot.py
    │   │   │   │   ├── prompt.py
    │   │   │   │   ├── schema.py
    │   │   │   │   ├── sync_prompts.py
    │   │   │   │   └── utils.py
    │   │   │   ├── smart_edu.py
    │   │   │   └── workflow
    │   │   │       ├── retrieve.py
    │   │   │       ├── roadmap.py
    │   │   │       └── teach.py
    │   │   ├── ta_module.py
    │   │   ├── tools
    │   │   │   ├── context_tools.py
    │   │   │   ├── factory.py
    │   │   │   ├── minio
    │   │   │   │   └── pdf_tools.py
    │   │   │   ├── neo
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── base.py
    │   │   │   │   ├── explore.py
    │   │   │   │   ├── retriever.py
    │   │   │   │   └── schema.py
    │   │   │   └── student
    │   │   │       └── base.py
    │   │   └── tracing
    │   │       ├── __init__.py
    │   │       ├── prompt_sync.py
    │   │       ├── schema.py
    │   │       ├── tracer.py
    │   │       └── writer.py
    │   ├── test_minio.py
    │   └── test_mongo.py
    ├── docs
    │   ├── description
    │   │   ├── implementation_plan.md
    │   │   ├── README.md
    │   │   └── walkthrough.md
    │   ├── draw
    │   │   └── Draw.excalidraw
    │   ├── latex
    │   │   ├── Contents
    │   │   │   ├── 01_Introduction.tex
    │   │   │   ├── 02_Fundamental extra.tex
    │   │   │   ├── 02_Fundamental.tex
    │   │   │   ├── 03_requirements.tex
    │   │   │   ├── 04_Proposal.tex
    │   │   │   ├── 05_System.tex
    │   │   │   ├── 06_Experiments.tex
    │   │   │   └── 07_Eval.tex
    │   │   ├── Images
    │   │   │   ├── ex
    │   │   │   │   ├── ai_mess.png
    │   │   │   │   ├── app_run.png
    │   │   │   │   ├── asynch_ingest.png
    │   │   │   │   ├── dbgate.png
    │   │   │   │   ├── docker.png
    │   │   │   │   ├── full_TA_output_1.png
    │   │   │   │   ├── graph.png
    │   │   │   │   ├── login.png
    │   │   │   │   ├── neo.png
    │   │   │   │   ├── node.png
    │   │   │   │   ├── pedia_err.png
    │   │   │   │   ├── recommend_ml.png
    │   │   │   │   └── tool_mess.png
    │   │   │   ├── fundamental
    │   │   │   │   ├── agent.png
    │   │   │   │   ├── bayes.png
    │   │   │   │   ├── cloud_local_llm.png
    │   │   │   │   ├── embedding.png
    │   │   │   │   ├── lstm.png
    │   │   │   │   ├── micro.png
    │   │   │   │   ├── react.png
    │   │   │   │   └── snn.png
    │   │   │   ├── hcmut.png
    │   │   │   ├── method
    │   │   │   │   ├── adaptive_middleware.png
    │   │   │   │   ├── agent_design.jpg
    │   │   │   │   ├── agent_design.png
    │   │   │   │   ├── full_pipe.png
    │   │   │   │   ├── g_extract.png
    │   │   │   │   ├── lang_mid.png
    │   │   │   │   ├── node_create.png
    │   │   │   │   └── pipeline.png
    │   │   │   ├── relate
    │   │   │   │   ├── dkg.png
    │   │   │   │   ├── edc.png
    │   │   │   │   ├── edukg.png
    │   │   │   │   ├── graphrag hybrid.png
    │   │   │   │   └── kggen.png
    │   │   │   └── system
    │   │   │       ├── AI
    │   │   │       │   └── ollama.png
    │   │   │       ├── backend
    │   │   │       │   ├── fastapi.png
    │   │   │       │   └── uv.png
    │   │   │       ├── database
    │   │   │       │   ├── mil.png
    │   │   │       │   ├── mongodb.png
    │   │   │       │   └── sqlite.png
    │   │   │       ├── filestorage
    │   │   │       │   └── minio.jpg
    │   │   │       ├── frontend
    │   │   │       │   └── react.png
    │   │   │       ├── lang_mid_logo.png
    │   │   │       ├── lang_mid.jpg
    │   │   │       ├── langchain_node.png
    │   │   │       └── S2666920X2500013X.bib
    │   │   ├── Intro
    │   │   │   ├── LoiCamDoan.tex
    │   │   │   ├── LoiCamOn.tex
    │   │   │   └── TomTat.tex
    │   │   ├── main.pdf
    │   │   ├── main.tex
    │   │   ├── Outro
    │   │   │   ├── citation-389497305.bib
    │   │   │   ├── Image.tex
    │   │   │   └── Supplement.tex
    │   │   ├── References.bib
    │   │   ├── script.sh
    │   │   └── table
    │   │       ├── chap2
    │   │       │   ├── edu_sys.tex
    │   │       │   └── frameworks.tex
    │   │       ├── chap3
    │   │       ├── chap4
    │   │       │   ├── wf_1.tex
    │   │       │   ├── wf_2.tex
    │   │       │   ├── wf_3.tex
    │   │       │   └── wf.tex
    │   │       └── chap5
    │   │           ├── config.tex
    │   │           ├── ingestion.tex
    │   │           ├── lifespan.tex
    │   │           ├── llms.tex
    │   │           ├── pipeline.tex
    │   │           └── sys_arch.tex
    │   ├── Ref
    │   │   ├── AEMA_agentic_eval.pdf
    │   │   ├── ai_4_CS50.pdf
    │   │   ├── AI_in_Edu.pdf
    │   │   ├── Course
    │   │   │   ├── 1_Prerequisite Extraction.pdf
    │   │   │   ├── 2_ LDA course extract.pdf
    │   │   │   ├── 3_ LLM based Pre extraction.pdf
    │   │   │   └── pre_summary.pdf
    │   │   ├── KG
    │   │   │   ├── Algo
    │   │   │   │   ├── 1_reasoning_and_graph.pdf
    │   │   │   │   ├── 2_KG_init.pdf
    │   │   │   │   ├── DKG_Comm.pdf
    │   │   │   │   └── Leiden for Comm.pdf
    │   │   │   ├── EduKG
    │   │   │   │   ├── eduKG.pdf
    │   │   │   │   ├── EduKGPipeline.pdf
    │   │   │   │   └── MeduKG.pdf
    │   │   │   ├── KG_Oppo_challenges.pdf
    │   │   │   └── KG_reasoning
    │   │   │       ├── kg_guide4QA.pdf
    │   │   │       └── KGQA.pdf
    │   │   ├── llm_in_edu.pdf
    │   │   ├── open_source_isue.pdf
    │   │   ├── semantic_collapse.pdf
    │   │   └── Technical
    │   │       ├── 2411.18241v1.pdf
    │   │       ├── ICRAAI26_SolyUpadtedv3.pdf.pdf
    │   │       ├── LangGraph V1 Essentials.pdf
    │   │       └── Qwen rep.pdf
    │   └── slides
    │       ├── Adaptive Agent System for Self-Learning and Course Navigation.pdf
    │       └── Roadmap For EduAgent.pdf
    ├── FE
    ├── FE-task.md
    ├── main.py
    ├── pyproject.toml
    ├── README.md
    └── script.sh

```

---

## Project Overview

The SmartEdu platform is structured into four primary modules, each serving a distinct architectural role in facilitating course ingestion, tracking student states, and driving interactive, personalized AI tutoring sessions:

1. **`core`**: Contains shared configuration schemas, database connection interfaces (SQL, NoSQL, Graph, Vector, Object Storage), dynamic LLM wrappers, and global utilities used across the entire ecosystem.
2. **`knowledge`**: Implements the pipeline for course material ingestion. It extracts structured semantic concepts and taxonomical relationships from slides and textbooks to build the system's foundational Knowledge Graph.
3. **`student`**: Manages user accounts, authentication (JWT), chat session lifecycles, and maintains an in-memory & persisted learning history including mastery levels, active progress, and recent navigation.
4. **`TA`**: Orchestrates the multi-turn conversational LangGraph workflow. It hosts the Smart Tutor agents, query router, retrieval workflows (RAG), customized learning path generators (Roadmaps), and active tutoring stages.
5. **`FE`**: Landing pages of the system, a Front End that sends request to backend. Technology used 
---

## Detailed Architecture

## 1. Core Module (`core/`)
*Common services, configuration systems, data schemas, and shared database clients.*

### `core/api/life_span.py`
Manages the application lifecycle events, including initializing and tearing down database engines (Neo4j, Milvus, Mongo, MinIO, MySQL) and global LLM configurations at startup and shutdown.
- **Functions**:
  - `lifespan`: Standard FastAPI event handler to initialize and tear down global database engines and LLM clients at application startup and shutdown.

### `core/config.py`
Defines the global environment configurations, database connection parameters (hosts, ports, credentials), and standard settings for Milvus, MongoDB, Neo4j, MinIO, MySQL, and Bloom's Taxonomy values.
- **Classes**:
  - `App_settings`: App metadata and route endpoints.
  - `K_conf`: Ingestion profiles.
  - `Ingest_param`: PDF ingestion paging metrics.
  - `Mil_conf` / `Emb_conf` / `Neo` / `Minio_conf` / `Mongo_conf`: Repository credentials.
  - `TA_conf` / `TA_serv`: TA agent configuration profiles.

### `core/dependencies.py`
Exposes dependency injection helper methods for FastAPI controllers, enabling dynamic retrieval and scoped management of KnowledgeModule, TAModule, and IngestionService instances.
- **Functions**:
  - `get_knowledge_module`: Retrieves the initialized KnowledgeModule instance from the FastAPI app state.
  - `get_ingestion_service`: Resolves the active CourseIngestionService instance.
  - `get_TA_module`: Resolves the initialized TAModule instance.

### `core/llm/config.py`
Defines hyperparameter profiles and active settings (model name, temperature, context length, keep-alive windows) for the different LLM agents (RAG, TA, Evaluator, Worker, Graph).
- **Classes**:
  - `LLMProfile`: Structured dataclass capturing individual model params.
  - `LLMConfig`: Pool mapping agent nicknames to their respective target profiles.

### `core/llm/llm_engine.py`
Acts as the central factory engine to initialize, instantiate, and cache LangChain ChatOllama connections based on LLMConfig profiles.
- **Classes & Methods**:
  - `CoreLLMEngine`: Holds instances of various models, dynamically spawning Ollama connectors with retry safety.

### `core/model/embedding.py`
Provides a unified embedding wrapper utilizing HuggingFace transformers (e.g., SciBERT) to generate numerical vectors for course topics and text chunks.
- **Classes & Methods**:
  - `Embedder`: Formulates embedding extraction loops and manages vector dims.

### `core/repo/graph/graphdb.py`
Interacts with the Neo4j instance to handle Cypher query execution, student mastery progress, and graph structure retrieval.
- **Classes & Methods**:
  - `GraphDB`: Establishes connections to Neo4j, retrieves learning path topologies, updates mastery ratings, and resets database nodes.

### `core/repo/graph/insert.py`
Contains serialization utilities to convert Knowledge Graph objects and dependencies into formatted dict collections suitable for Neo4j transactional loading.
- **Functions**:
  - `serialize_kg_to_dict`: Maps KG_Instance structures into clean list collections of nodes, edges, and clusters.

### `core/repo/milvus_db/mil.py`
Manages the vector database storage client (Milvus), supporting collection construction, vector embedding inserts, and semantic similarity search queries.
- **Classes & Methods**:
  - `MilvusDB`: Connects to Milvus, constructs collection schemas, inserts concept vectors, and queries top-K matching nodes.

### `core/repo/nosql/mongo_db.py`
Implements the MongoDB client wrapper to store unstructured learning histories, chat context memos, and student session states.
- **Classes & Methods**:
  - `Mongo_DB`: Coordinates connections, retrieves session documents, appends logs to chat history, and updates active learning positions.

### `core/repo/sql/sql_db.py`
Manages the relational SQL database connection (MySQL/SQLite) using SQLAlchemy to handle structured account authentication and student profiles.
- **Classes & Methods**:
  - `SQL_DB`: Establishes DB pools, handles user password verification, and executes registration queries.

### `core/repo/storage/minio_repo.py`
Interfaces with MinIO object storage to organize, store, and stream course material PDFs, lecture slides, and parsed textbook chunks.
- **Classes & Methods**:
  - `MinioDB`: Establishes bucket connections, uploads whole PDF documents, and saves chunk text structures.

### `core/schema/factory.py`
Declares the standardized Pydantic data schemas representing text extractions, slide concept bundles, and textbook-to-anchor links.
- **Classes**:
  - `RhetoricalItem`: Standard structure capturing statement roles and exact texts.
  - `ConceptBundle`: Maps slide concept names to their rhetorical contexts.
  - `SkeletonStructure`: Phase 1 slide parsing skeleton containing extracted concepts.
  - `RelationStructure`: Phase 2 slide parsing model identifying concept-to-concept relations.
  - `AnchorLinkStructure`: Matches textbook segments to related slide anchors.

### `core/schema/graph/graph.py`
Defines the base schemas representing clusters and graph instances of the Knowledge Graph system.
- **Classes**:
  - `Cluster`: Leiden or semantic cluster container holding node ID members.
  - `KG_Instance`: Consolidated container representing the mapped nodes, edges, and clusters.

### `core/schema/graph/ontology.py`
Represents the structural ontology of the educational Knowledge Graph, enforcing typed nodes (Topic, Community, Concept, Rhetorical) and edges.
- **Classes**:
  - `TopicNode` / `CommunityNode` / `ConceptNode` / `RhetoricalNode`: Node schemas inheriting from BaseNode.
  - `EduEdge`: Ontology structure mapping source-to-target nodes.

### `core/schema/graph/type.py`
Stores standard base models, reference structures, and type enumerations utilized throughout the graph schema.
- **Classes & Enums**:
  - `Ref`: Direct reference pointers identifying external storage blocks.
  - `BaseNode`: Structural base class for graph objects.
  - `RhetoricalRole`: Enumerates logical roles (Formula, Proof, Statement, quiz).
  - `NodeType` / `EdgeType`: Ontology classifications.

### `core/schema/wf_state.py`
Defines the state objects, payload dictionaries, and message collections tracked inside the LangGraph workflows.
- **Classes**:
  - `ConceptNode`: Simplified concept representations with Bloom's mastery tracking.
  - `LearningProposal`: Structured recommendation details.
  - `StudentState`: Typed dictionary mapping current sessions, history lists, and masteries.
  - `AgentState`: Unified state wrapper representing active chats, intents, and worker outputs.

### `core/util/file_extractor.py`
Implements the core document parsing pipeline using Docling, converting PDF pages into clean markdown sections and window-overlapping text blocks.
- **Functions**:
  - `extract_pdf`: Processes target documents, strips headers, and batches pages.
  - `create_refs`: Maps batch chunks into verifiable storage references.

---

## 2. Knowledge Ingestion Module (`knowledge/`)
*Automated parsing of educational documents and generation of semantic graphs.*

### `knowledge/api/route.py`
Exposes REST endpoints to trigger and monitor course ingestion tasks in the background.
- **Endpoints**:
  - `POST /ingest-course`: Enqueues an ingestion request, validates the presence of uploaded PDFs, and triggers background processing.

### `knowledge/engine/extract.py`
Uses the LLM engine to clean slide headers, extract concept skeletons, link concepts, and trace textbook-to-KG semantic relationships.
- **Classes & Methods**:
  - `GraphExtractionService`: Controls extraction phases, using prompting layers to synthesize concepts and relationships.

### `knowledge/engine/graph/graph_constructor.py`
Parses extraction phase structures, builds graph instances, resolves reference models, and exports the final Knowledge Graph.
- **Classes & Methods**:
  - `KG_Handler`: Accumulates extracted concepts and edges into serialized Knowledge Graph lists.

### `knowledge/service/course_ingest.py`
Coordinates the complete course loading pipeline by verifying PDFs, triggering file extractors, launching LLM mappings, and writing results to databases.
- **Classes & Methods**:
  - `CourseIngestionService`: The pipeline orchestrator driving course imports.

### `knowledge/knowledge_construction_service.py`
Exposes the entrypoint facade wrapper representing the ingestion module, managing core resource cleanup.
- **Classes & Methods**:
  - `KnowledgeModule`: Handles component initialization and provides access to CourseIngestionService.

---

## 3. Student Management Module (`student/`)
*Identity verification, chat session registration, and persistent tracking of learner progress.*

### `student/api.py`
Exposes user-facing endpoints to register student accounts, process credentials, and start or end chat sessions.
- **Endpoints**:
  - `POST /register`: Registers new student profiles, hashes credentials, and allocates a default state document.
  - `POST /login`: Validates credentials and generates a secure authentication payload.
  - `POST /session/start` & `DELETE /session/end`: Generates and discards session-specific UUID tokens to cleanly isolate chat sessions.

### `student/auth.py`
Handles token creation, claim processing, and user validation using secure JWT encryption.
- **Functions**:
  - `create_access_token`: Generates secure JWT access tokens.
  - `get_current_student`: FastAPI dependency that decodes JWT claims and validates caller identity.

### `student/Student_Tracker.py`
Orchestrates active learning states, mastery levels, visited resources, and synchronization between database providers.
- **Classes & Methods**:
  - `Student_Tracker`: Coordinates high-level state operations, tracks in-memory sessions, maps active lesson steps, advances learned concepts, updates Neo4j progress graphs, and synchronizes persistent student history with MongoDB.

### `student/memo.py`
Provides helper classes to cache, summarize, and format chat history turns as an injection context for LLM agents.
- **Classes & Methods**:
  - `Memo`: Caches and formats the sliding conversation window history (skim vs. full mode) to supply context to the LLMs.

---

## 4. Teaching Assistant Module (`TA/`)
*The LangGraph-powered AI tutor orchestrating multi-agent reasoning and step-by-step education.*

### `TA/ta_module.py`
Coordinates the top-level orchestration of tutor dialogue iterations, trace buffers, and callback telemetry.
- **Classes & Methods**:
  - `TAModule`: High-level entrypoint that handles chat inputs, initializes state logs, launches the `SmartEdu` engine execution, and serializes trace histories.

### `TA/agent/injector.py`
Spawns and configures LangChain agent executor pipelines with structural middlewares and tool schemas.
- **Classes & Methods**:
  - `AgentInjector`: Spawns Ollama connectors and configures `NodeSchemaMiddleware` schema-mapping tools.

### `TA/agent/middleware.py`
Interceptors to dynamically validate and map different validation schemas inside active multi-intent agent runs.
- **Classes & Methods**:
  - `NodeSchemaMiddleware`: A custom interceptor that switches the target structured response validation schema (e.g., `RAGCore`, `RAGDeep`, `RoadmapExplore`) based on the active LangGraph node.

### `TA/agent/ollama_patch.py`
Applies structural fixes and formatting updates to Ollama JSON schema parser classes.
- **Functions**:
  - Patches LangChain Ollama client schemas to ensure native structured JSON output formatting.

### `TA/api/route.py`
Exposes the main tutoring endpoint allowing clients to post queries and receive contextual agent responses.
- **Endpoints**:
  - `POST /chat`: Receives user queries and session IDs, executing active tutor pipelines.

### `TA/edu/smart_edu.py`
Compiles and manages the primary StateGraph compiled with LangGraph to orchestrate router, retrieve, roadmap, and teach sub-workflows.
- **Classes & Methods**:
  - `SmartEdu`: Compiles and executes the primary LangGraph StateGraph, consisting of:
    - `TA_Router`: Evaluates queries and redirects flow to specialized sub-workflows.
    - `TA_Retrieve_Finish`, `TA_Roadmap_Finish`, `TA_Teach_Finish`: Synthesis nodes that format custom tutor dialogue outputs.
    - `Apply_Proposal`: Commits recommended pathway adjustments when approved by the student.
    - `TA_Unknown_Finish`: Standard fallback node that guides students on how to interact with the system.

### `TA/edu/workflow/retrieve.py`
Assembles the search retrieval workflow (`build_retrieve_wf`) to evaluate queries, trigger vector databases, and check knowledge gaps.
- **Functions**:
  - `build_retrieve_wf`: Compiles the retrieve sub-graph containing `RAG_Core`, `Deep_Decision`, and `rag_deep`.
  - `rag_core` / `rag_deep`: RAG queries retrieving content and proposing bridge nodes.
  - `deep_decision`: Evaluates if a query requires deep, multivariable context routing.

### `TA/edu/workflow/roadmap.py`
Assembles the roadmap workflow (`build_roadmap_wf`) to construct sequences, review current progress, and suggest pedagogical pathways.
- **Functions**:
  - `build_roadmap_wf`: Compiles the roadmap sub-graph containing `Roadmap_Explore`, `Roadmap_Evaluator`, and `TA_Advice`.
  - `roadmap_explore_logic` / `roadmap_evaluator_logic`: Generate candidate sequences and evaluate them against student history.
  - `ta_advice_logic`: Formulates advice reports and roadmap updates.

### `TA/edu/workflow/teach.py`
Assembles the core lesson workflow (`build_teach_wf`) to deliver slides, reviews, quizzes, and next concept candidates.
- **Functions**:
  - `build_teach_wf`: Compiles the teach sub-graph containing `Teach_Understand`, `Teach_Lookup`, `Teach_RAG`, `Teach_Lecture`, `Teach_Evaluate`, and `Next_Topic`.
  - `teach_understand`: Decides whether to lecture, review, or quiz.
  - `teach_lookup`: Deterministically extracts relevant slide contents without using LLM calls.
  - `teach_rag`: Fallback retrieval node if deterministic lookups return empty content.
  - `teach_lecture`: Formulates structured lecture texts with dynamic challenge questions.
  - `teach_evaluate` / `next_topic`: Evaluates student answers and selects candidate steps.

### `TA/tools/factory.py`
Binds the appropriate database exploration and document extraction tools to specific agents.
- **Classes & Methods**:
  - `ToolFactory`: Instantiates explorer and reader tools (e.g., `EntityFinder`, `RhetoricalRetriever`, `GetPages`) for RAG and TA models.

### `TA/tracing/tracer.py`
Tracks step-by-step reasoning outputs, records metrics, formats payload models, and exports traces to Langfuse.
- **Classes & Methods**:
  - `AgentTracer`: Monitors active workflows, tracks step-by-step model outputs, handles optional Langfuse callback telemetry, and writes async execution logs to JSON files.