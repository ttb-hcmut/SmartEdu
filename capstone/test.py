from knowledge.engine.extract import graph_const
from knowledge.repo.graph.test.doc import DOC
from knowledge.repo.graph.graphdb import GraphDB
texts = "\n".join([doc for doc in DOC])

kg = graph_const(DOC)

from time import time
start = time()
graphDB = GraphDB(uri="bolt://localhost:7687", auth=("neo4j", "graph123"))
print("================================ Start Inserting ================================ ")
graphDB.reset("test")
graphDB.import_graph("test", kg)

print("insertion takes: ", time()-start)
