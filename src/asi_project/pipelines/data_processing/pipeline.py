

from kedro.pipeline import Pipeline
from .data import join_statements_node, return_greeting_node

def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([return_greeting_node, join_statements_node])