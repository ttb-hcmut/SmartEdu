# SmartEdu
> A Graph-based Intelligent Teaching Assistant for Mastery-oriented Learning Roadmap Guidance and Supervision

## Table of Contents
1. [Introduction](#1-introduction)
2. [Core Features](#2-core-features)
3. [Use Case API](#3-use-case-api)
4. [Infrastructure & How to Run](#4-infrastructure--how-to-run)

## 1. Introduction
**SmartEdu** is a proactive, mastery-oriented educational ecosystem designed to replace traditional linear learning platforms. Instead of static content delivery, it functions as a human-like Teaching Assistant that tracks student progress and dynamically guides them through a highly structured Knowledge Graph.

For detailed mathematical formulations, system design principles, and comprehensive evaluations, please refer to the [Full Project Report](docs/latex/main.pdf).

> [!NOTE]
> Currently, this system targets and adapts specifically to the academic roadmap of Computer Science.

## 2. Core Features
- **Automated Knowledge Ingestion:** Load unstructured documents (lecture slides, textbooks) and get them analyzed autonomously.
- **Knowledge Graph Conversion:** Automatically convert your resources into a structured Educational Knowledge Graph (EKG) that maps prerequisites and related concepts.
- **Dynamic Mastery Tracking:** Continuously tracks your learning performance, identifying knowledge gaps and scoring your proficiency.
- **Virtual Teaching Assistance (TA):** A smart agent that answers questions strictly grounded in the verified knowledge base (no hallucinations), recommends personalized learning paths, and retrieves deep contextual materials suitable for your current progress.
- **Knowledge-based QA:** Teaching Assistant retrieve information, perform continuous loop-up and reasoning loop before giving answers.

### Full System Visualization 

<img src="docs/latex/Images/method/full_pipe.png" width="100%" alt="SmartEdu System">

## 3. Use Case API

The SmartEdu ecosystem exposes three main logical modules, each providing dedicated REST endpoints to handle system ingestion, authentication, state supervision, and the agentic chat workflow.

### Knowledge Module
Manages the ingestion and construction of the Educational Knowledge Graph (EKG).

* **`POST /system/v0/knowledge/ingest-course`**
  * **Use Case:** Validates the presence of raw course documents (PDF slides, textbooks) and triggers the asynchronous dual-phase ingestion pipeline to extract core concepts, filter out hallucinations via DBpedia/NLP steps, and construct the prerequisite graph in Neo4j.
  * **Input Schema (JSON):**
    ```json
    {
      "course_name": "Machine Learning",
      "slide_files": ["slide1.pdf", "slide2.pdf"],
      "textbook_files": ["textbook1.pdf"],
      "reset": true
    }
    ```
  * **Output Schema (JSON):**
    ```json
    {
      "status": "accepted",
      "message": "Course Machine Learning ingestion started in background",
      "details": {
        "slides_count": 2,
        "textbooks_count": 1
      }
    }
    ```

---

### Student Module
Handles student registration, authentication, and chat session state management.

* **`POST /system/v0/student/register`**
  * **Use Case:** Registers a new student, hashes their credentials into the SQLite database, and creates a default state tracking document in MongoDB.
  * **Input Schema (JSON):**
    ```json
    {
      "student_id": "student_01",
      "password": "secure_password"
    }
    ```
  * **Output Schema (JSON):**
    ```json
    {
      "detail": "Registered successfully."
    }
    ```

* **`POST /system/v0/student/login`**
  * **Use Case:** Validates student credentials and generates a secure JWT authentication payload.
  * **Input Schema (Form Data):**
    * `username`: `"student_01"`
    * `password`: `"secure_password"`
  * **Output Schema (JSON):**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1...",
      "token_type": "bearer"
    }
    ```

* **`POST /system/v0/student/session/start`**
  * **Use Case:** Allocates a new in-memory Chat Session ID for the authenticated student to isolate chat history.
  * **Headers:** `Authorization: Bearer <JWT_TOKEN>`
  * **Output Schema (JSON):**
    ```json
    {
      "session_id": "4a7b05eb-6c1b-4b2a..."
    }
    ```

* **`DELETE /system/v0/student/session/end`**
  * **Use Case:** Terminates and drops the active session from the tracker's memory, persisting final progress to MongoDB.
  * **Headers:** `Authorization: Bearer <JWT_TOKEN>`
  * **Query Params:** `session_id=<SESSION_ID>`
  * **Output:** HTTP 204 No Content indicating successful deletion.

---

### Teaching Assistant (TA) Module
Orchestrates the multi-agent LangGraph chat interface.

* **`POST /system/v0/ta/chat`**
  * **Use Case:** Primary tutoring interface. It accepts the student's prompt and schedules the hierarchical LangGraph workflow as a background task.
  * **Headers:** `Authorization: Bearer <JWT_TOKEN>`
  * **Input Schema (JSON):**
    ```json
    {
      "session_id": "4a7b05eb-6c1b-4b2a...",
      "user_input": "Explain backpropagation.",
      "language": "vn"
    }
    ```
  * **Output Schema (JSON):**
    ```json
    {
      "task_id": "7d9b01ae-9a6c-48b2..."
    }
    ```

* **`GET /system/v0/ta/chat/status/{task_id}`**
  * **Use Case:** Status polling endpoint to retrieve the execution state, current active agent/thought, and final markdown tutor response upon completion.
  * **Headers:** `Authorization: Bearer <JWT_TOKEN>`
  * **Output Schema (JSON):**
    ```json
    {
      "status": "done",
      "agent_name": "Generator",
      "intent": "Explain concept",
      "thought": "Using retrieved EKG context...",
      "result": {
        "message": "Backpropagation is...",
        "ui_action": {}
      },
      "error": null
    }
    ```

## 4. Infrastructure & How to Run
### Infrastructure
- **Backend:** FastAPI (Python)
- **Polyglot Persistence Databases:** Neo4j (Graph), Milvus (Vector), MongoDB (Document), MinIO (Object), SQLite (Auth).

### How to run
1. Ensure you have Docker, Python 3.11+, and the `uv` package manager installed.
If you don't, you might want to install it:
   - uv: https://docs.astral.sh/uv/#installation
   - docker: https://www.docker.com/products/docker-desktop/ 
2. Start the database infrastructure via Docker Compose:
   ```bash
   docker compose -f core/repo/docker-compose.yaml --env-file core/.env up -d
   ```
   In order for this to work, either hardcore the environment values in the yaml files or create a .env in capstone/core
3. Install Python dependencies using `uv`:
   ```bash
   uv venv
   # Activate virtual environment (.venv\Scripts\activate on Windows, source .venv/bin/activate on Unix)
   uv pip install -r requirements.txt
   ```
4. Go into the capstone (source code) and start the FastAPI backend server:
   ```bash
   cd capstone

   uv run uvicorn main:app
   # No flag needed, I take care of that
   ```
