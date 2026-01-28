from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.generation import GraphRAG
 

MODEL_NAME = "gemma3:1b" 
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "graph123")
driver = GraphDatabase.driver(URI, auth=AUTH)

llm = OllamaLLM(model_name=MODEL_NAME, model_params={"temperature": 0})

NEO4J_SCHEMA = """
Nodes:
- Entity {id: STRING, name: STRING, rrole: STRING, content: STRING}
Relationships:
- [:CONTENT], [:CONTENT], [:SEMANTIC], [:PART_OF]

rrole: "Definition", "Objective", "Problem"
"""

CUSTOM_PROMPT = """
Task: Generate a Neo4j Cypher query.
Schema:
{schema}

Rules:
1. ONLY use the label ':Entity'. DO NOT use ':RhetoricalNode' or ':Content'.
2. ONLY use the property 'content'. DO NOT use 'body'.
3. Use 'CONTAINS' for name searching.
4. Output ONLY the query string. No code blocks, no "cypher" keyword.

Example:
Question: What is AI?
Query: MATCH (n:Entity) WHERE n.name CONTAINS 'AI' OR n.rrole = 'Definition' RETURN n.content AS context

Question: {query_text}
Query:"""
# 2. Khởi tạo Retriever
retriever = Text2CypherRetriever(
    driver=driver,
    llm=llm,
    neo4j_schema=NEO4J_SCHEMA,
    custom_prompt=CUSTOM_PROMPT,
    neo4j_database="test"
)

# 3. Setup RAG
rag = GraphRAG(retriever=retriever, llm=llm)

query_text = "What is Machine Learning?"
print(f"--- Querying Graph for: {query_text} ---")

response = rag.search(query_text=query_text, return_context = True)
print("\nFinal Answer:")
print(response.answer)



print("=========================== Debug ===========================")
print(vars(response))