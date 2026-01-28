
from knowledge.repo.graph.test.doc import DOC

# Package import
## LLM based package
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

## Util package
import json
from typing import Tuple, List, Union
from time import time


# Project component import
## 1. Graph
from knowledge.core.schema.graph import EduNode, EduEdge, KG_Instance ### Schema, the blueprint of Graph Design
from knowledge.core.schema.factory import SkeletonStructure, RelationStructure ### Graph Literature holder, a simple holder for LLM to handle
from knowledge.engine.graph.graph_constructor import KG_Handler ### Graph engine


def graph_const(texts: Union[str, List, Tuple[str, str]]):
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
        """
        You Are an Expert Builder of Computer Science Knowledge graph. Your Mission
        Extract Concept Bundles using STRICT VERBATIM content (no summarizing).
        ### RULES:
        - Concept names short be short (4 words max)
        - Concept should be domain special

        ### ROLE CLASSIFICATION (Strictly match these Enums):
        - **Definition**: Core meaning/What is it?
        - **Formula**: Equations, Math, Logic.
        - **Objective**: Goal, Purpose, or Target.
        - **Problem**: Limitation, Risk, Failure, Trade-off.
        - **Solution**: Method/Strategy to fix a problem.
        - **Proof**: Derivation, Logical deduction.
        - **Experiment**: Data, Setup, Empirical results.
        - **Application**: Real life application.
        - **Statement**: General facts, assertions (fallback category).

        ### PRIORITY:
        - Negative consequence -> **Problem**.
        - Goal/Aim -> **Objective**.
        - Derivation -> **Proof**.
        - Experimental details -> **Experiment**.

        TEXT:
        {text}
        
        {format_instructions}"""
    )
    
    chain_p1 = prompt_p1 | llm | parser_p1

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

    
    kg_handler = KG_Handler()
    start = time()
    print("================ Step 1: Graph Literature bulding block ================")
    for i, text in enumerate(texts):
        print(f">>>>>> SubGraph {i} <<<<<<<<")
        start_g = time()
        p1_result : SkeletonStructure = chain_p1.invoke({
            "text": text,
            "format_instructions": parser_p1.get_format_instructions()
        })

        extracted_concepts = [b.name for b in p1_result.tree]

        p2_result : RelationStructure = chain_p2.invoke({
            "text": text,
            "concept_list": ", ".join(extracted_concepts),
            "format_instructions": parser_p2.get_format_instructions()
        })
        

        literature_union = {
            "og": text,
            "meta": {
                "model": MODEL_NAME,
                "concept_count": len(extracted_concepts),
                "relation_count": len(p2_result.edges)
            },
            "skeleton_phase": p1_result.model_dump(),
            "relation_phase": p2_result.model_dump()
        }

        print("Taken time: ", time() - start_g)
        ### Save result
        with open(f"test/graph_lit_{i}.json", "w", encoding="utf-8") as f:
            json.dump(literature_union, f, indent=2, ensure_ascii=False)
        
        # II. Graph Literature (Semantic Info) + Graph Blueprint (Structure Info) ==> Full Graph DataStructure
        
        kg_handler.build(p1_result, p2_result, topic_name="Machine Learning")
    mid = time()
    print(f"Finish Graph takes {mid - start}")
    kg_handler.save_json()
    kg_handler.visualize_kg()

    end = time()
    print(f"Visualize takes {end-mid}")

    return kg_handler.kg


        


