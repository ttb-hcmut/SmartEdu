from knowledge.engine.extract import graph_const
from knowledge.repo.graph.test.doc import DOC

texts = "\n".join([doc for doc in DOC])

graph_const(DOC[0])
