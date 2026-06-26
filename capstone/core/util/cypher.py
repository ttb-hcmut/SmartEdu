def concept_pred(var: str = "n") -> str:
    ## one source of truth: a traversable concept entity (not rhetorical; tree nodes excluded by label)
    return f"{var}.rrole IS NULL"
