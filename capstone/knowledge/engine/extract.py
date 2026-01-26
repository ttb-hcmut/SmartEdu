
from knowledge.repo.graph.test.doc import DOC

# Package import
## LLM based package
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

## Util package
import json

# Project component import
## Schema, the blueprint of Graph Design
from knowledge.core.schema.graph import EduNode, EduEdge, GlobalKG
## Graph Literature holder, a simple holder for LLM to handle
from knowledge.core.schema.factory import SkeletonStructure, RelationStructure


def graph_const(text: str, output_file: str = "test/graph_debug.json"):
    # Set up model
    MODEL_NAME = "gpt-oss:120b-cloud"  
    llm = OllamaLLM(
        model=MODEL_NAME, 
        temperature=0.0,
        num_ctx=8192
    )
    # I. Output Graph Literature
    ## Step 1: Output the tree of Concept --> Rheto as the Skeleton 
    parser_p1 = PydanticOutputParser(pydantic_object=SkeletonStructure)
    
    
    prompt_p1 = ChatPromptTemplate.from_template(
        """Analyze the text and extract knowledge structures into Concept Bundles.
        
        ### EXTRACTION RULES (STRICT):
        1. **Content Fidelity**: Extract content **VERBATIM** (word-for-word) or as close to the original text as possible. Do NOT summarize, simplified, or rewrite technical details. Keep original keywords.
        2. **Completeness**: If a definition or example spans multiple sentences, include the full context.
        
        ### CLASSIFICATION DEFINITIONS:
        - **Definition**: The formal explanation of WHAT the concept is.
        - **Formula**: Mathematical equations, logic expressions, or algorithmic steps.
        - **Problem**: Limitations, trade-offs, risks, failures, or challenges associated with the concept. (e.g., "Overfitting leads to poor generalization").
        - **Illustration**: **REAL-LIFE EXAMPLES**, specific scenarios, analogies, or practical applications mentioned in the text. (e.g., "Like a student memorizing answers instead of understanding").

        ### PRIORITY LOGIC:
        - If a sentence describes a **negative consequence** or **limitation**, classify as **Problem** (even if it looks like an example).
        - If a sentence describes a **concrete scenario** to explain the concept, classify as **Illustration**.

        TEXT:
        {text}
        
        {format_instructions}"""
    )

    chain_p1 = prompt_p1 | llm | parser_p1
    

    p1_result : SkeletonStructure = chain_p1.invoke({
        "text": text,
        "format_instructions": parser_p1.get_format_instructions()
    })

    ## Step 2: From tree, strengthen into graph via Concept <--> Concept 
    parser_p2 = PydanticOutputParser(pydantic_object=RelationStructure)
    prompt_p2 = ChatPromptTemplate.from_template(
        """Identify relationships (IS_A, PART_OF, RELATED_TO, CAUSES) between concepts.
        STRICT CONSTRAINT: Only create edges between concepts found in this list: {concept_list}
        Do not invent new nodes.
        
        TEXT:
        {text}
        
        {format_instructions}"""
    )
    chain_p2 = prompt_p2 | llm | parser_p2

    extracted_concepts = [b.name for b in p1_result.tree]

    p2_result : RelationStructure = chain_p2.invoke({
        "text": text,
        "concept_list": ", ".join(extracted_concepts),
        "format_instructions": parser_p2.get_format_instructions()
    })

    final_output = {
        "og": text,
        "meta": {
            "model": MODEL_NAME,
            "concept_count": len(extracted_concepts),
            "relation_count": len(p2_result.edges)
        },
        "skeleton_phase": p1_result.model_dump(),
        "relation_phase": p2_result.model_dump()
    }

    print(json.dumps(final_output, indent=2, ensure_ascii=False))
    ### Save result
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    
    # II. Graph Literature (Semantic Info) + Graph Blueprint (Structure Info) ==> Full Graph DataStructure



    


