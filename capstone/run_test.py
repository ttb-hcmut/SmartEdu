from test.test_script.knowledge.ingestion import run_ingestion_test
from test.test_script.TA.tools import full
from test.test_script.TA.question import test_ta_logic
from core.repo.graph.graphdb import GraphDB

import asyncio
import json
from time import time

from keybert import KeyBERT
import os
import re
kw_model = KeyBERT()
import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test mode."
    )
    parser.add_argument(
        "--test", type=str, default="TA"
    )
    parser.add_argument(
        "--n", type=int, default=2
    )
    return parser.parse_args()

def main():
    args = parse_args()
    test: str = args.test
    n: int = args.n
    slides = [
        "Chapter 1 - Introduction.pdf",
        "Chapter 2 - Decision Tree.pdf",
        "Chapter 3 - Bayesian Learning.pdf",
        "Chapter 4 - Genetic Algorithms.pdf",
        "Chapter 5 - Graphical Models.pdf",
        "Chapter 6 - SVM.pdf",
        "Dimensionality Reduction.pdf"
    ]


    books = []

    name = "ML"
    start = time()

    if test == "graph":
        asyncio.run(main=run_ingestion_test(course_name=name,slide_files=slides[:n],textbook_files=books)) 
    elif test == "TA":
        query = "What is the relationship between Reinforcement Learning and Supervised Learning"
        asyncio.run(test_ta_logic(query=query) )

        full()

    print("Time taken: ", time() - start)



if __name__ == "__main__":
    main()