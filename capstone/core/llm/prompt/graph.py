from langchain_core.prompts import ChatPromptTemplate

from langchain_core.prompts import ChatPromptTemplate

prompt_p0 = ChatPromptTemplate.from_messages([
    ("system", """Task: Classify text into a single GLOBAL academic topic.
Rules:
- NO sub-topics. Use parent categories only (e.g., "Machine Learning", not "SVM").
- NO numbers, NO "Chapter/Part", NO explanations.
- Format: Title Case Noun Phrase only.

Examples:
- SVM, KNN, CNN -> Machine Learning
- Entropy, Information Gain -> Decision Tree
- What is AI? -> Artificial Intelligence"""),
    
    ("human", "TITLE: {raw_name}\nCONTENT: {text_content}\nTopic:")
])

### RESULT
prompt_p1 = ChatPromptTemplate.from_messages([
    ("system", """You Are an Expert Builder of Computer Science Knowledge Graphs.
    Your Mission: Extract Concept Bundles for the course: "{course}".
     
    ### CRITICAL EXTRACTION RULES:
    1. **Concept Name**: 
    - MUST be a technical/academic Term (e.g., "Backpropagation", not "Good way to learn").
    - Use Singular Form (e.g., "Decision Tree" instead of "Decision Trees").

    2. **Concept Description ('desc' field)**:
    - Identify the definition in the text and place it here. 
    - DO NOT create a separate detail item for Definition. Definition IS the node.

   3. **Rhetorical Details (The 'details' array) - NO CONTEXT LEAKAGE**:
    - **Self-Contained Content**: Each detail MUST be understandable without needing to see the Concept Name.
    - **PRONOUN RESOLUTION**: Replace all ambiguous pronouns ("It", "They", "This", "The method", "The algorithm") with the ACTUAL Concept Name.
    - *Example*: Instead of "It is told when an answer is wrong", extract as "Reinforcement Learning is told when an answer is wrong".
    - **Verbatim Integrity**: Stay as close to the source text as possible while ensuring the content is semantically independent.

    ### ROLE CLASSIFICATION (Assign to 'role' inside 'details'):
        - **Formula**: Equations, Math, Logic.
        - **Objective**: Goal, Purpose, Target (e.g., "The goal is...").
        - **Problem**: Limitation, Risk, Failure, Trade-off (e.g., "Overfitting occurs when...").
        - **Solution**: Method/Strategy to fix a problem.
        - **Statement**: General facts, assertions.    
        - **Exercise**: Question that is related to that concept 
    [Other roles: Proof, Experiment, Application]

    ### EXAMPLE OF WRONG VS RIGHT:
    - WRONG Name: "Overfitting Problem" 
    - RIGHT Name: "Overfitting" (Role: Problem)

    - WRONG Name: "Generalization Objective"
    - RIGHT Name: "Generalization" (Role: Objective)

    {format_instructions}"""),
        ("human", "TEXT:\n{text}")
    ])

prompt_p2 = ChatPromptTemplate.from_messages([
    ("system", """You are a Knowledge Graph Relationship Extractor.
Identify relationships (INCLUDES, PRESIQUITES, CAUSES, RELATED_TO,REFER) between concepts.
     
### RELATIONSHIP GUIDELINES:
    - **PREREQUISITE**: A -> B means concept A must be understood before Concept B.
    - **INCLUDES**: A -> B means Concept A is a category that contains Concept B.
    - **CAUSES**: A -> B means Action in A leads to outcome B (e.g., Complexity -> Overfitting).
    - **RELATED**: A -> B means Concept A relate to Concept B, usually same methods or concept in a big topic.
    - **REFER**: A -> B means Concept A refers to Concept B, but they are not strictly prerequisite or inclusive.
### RELATIONSHIP explanation guildline: Explain why the relationship is 
STRICT RULE: 
    - Only create edges between concepts found in this exact list: [{concept_list}]. Do not invent new nodes.

{format_instructions}"""),
    ("human", "TEXT:\n{text}")
])

TEXTBOOK_EXTRACTION_PROMPT = """
You are a strict academic data extractor. Your task is to link a section of a textbook to a list of existing knowledge graph concepts (anchors).

Textbook Section:
{text}

Candidate Anchors (Extracted from course slides):
{candidates}

Instructions:
1. Read the Textbook Section carefully.
2. Review the Candidate Anchors.
3. Determine if the Textbook Section explicitly elaborates on, provides examples for, or deeply explains any of the Candidate Anchors.
4. DO NOT create new anchors. You can only select from the provided Candidate Anchors.
5. If the text does not strongly relate to an anchor, ignore it. 
6. Return a valid JSON array of objects. Each object must have "anchor_id" (exact ID from candidates) and "justification" (brief reason why it links). If no matches are found, return [].

Output Format (Strict JSON):
[
  {{
    "anchor_id": "Exact_ID_Here",
    "justification": "Short reasoning here"
  }}
]
"""