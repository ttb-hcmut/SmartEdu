from test.test_script.knowledge.ingestion import run_ingestion_test
from test.test_script.TA.tools import full
from test.test_script.TA.question import test_ta_logic
from core.repo.graph.graphdb import GraphDB

import asyncio
import json
from time import time

import os
import re
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

    parser.add_argument(
        "--name", type=str, default="ML"
    )
    parser.add_argument(
        "--loop", type=int, default=0
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    test: str = args.test
    n: int = args.n
    loop = args.loop if args.loop > 0 else 1 
    

    if test == "graph":
        books = []

        path = "./data/"
        name = args.name
        if os.path.exists(path + name):
            slides = [f"{name}/{f}" for f in os.listdir(path + name)]
        else:
            slides = []
        asyncio.run(run_ingestion_test(course_name=name,slide_files=slides[:n],textbook_files=books)) 
    elif test == "TA":
        import datetime
        count = 0 
        now = datetime.datetime.now()
        session_filename = f"TA_v0_{now.strftime('%H%M%S')}_{now.strftime('%d%m')}.json"
        while(True):
            query = input("\nWhat shall we do today ?\n")
            if len(query) < 1 or query == "exit":
                break
            start = time()
            asyncio.run(test_ta_logic(query=query, filename=session_filename))
            print(f"Time taken for question {count+1} [{query}]:\n" , time() - start)
            count+=1
            if count == loop:
                break
        
    

if __name__ == "__main__":
    main()