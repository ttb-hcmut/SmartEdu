from core.schema.graph.type import *

ACTION_DOWNGRADE = "DOWNGRADE"
ACTION_KEEP      = "KEEP"     
ACTION_HIERARCHY = "HIERARCHY"


SEMANTIC_MAP = {
    "objective":    RhetoricalRole.OBJECTIVE,
    "goal":         RhetoricalRole.OBJECTIVE,
    "aim":          RhetoricalRole.OBJECTIVE,
    "purpose":      RhetoricalRole.OBJECTIVE,
    "target":       RhetoricalRole.OBJECTIVE,

    "problem":      RhetoricalRole.PROBLEM,
    "issue":        RhetoricalRole.PROBLEM,
    "challenge":    RhetoricalRole.PROBLEM,
    "drawback":     RhetoricalRole.PROBLEM,
    "limitation":   RhetoricalRole.PROBLEM,
    "bottleneck":   RhetoricalRole.PROBLEM,

    "solution":     RhetoricalRole.SOLUTION,
    "application":  RhetoricalRole.APPLICATION,

    "statement":    RhetoricalRole.STATEMENT,
    "conclusion":   RhetoricalRole.STATEMENT,
    "finding":      RhetoricalRole.STATEMENT,
    "benefit":      RhetoricalRole.STATEMENT,
}