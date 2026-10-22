import operator
from typing import Annotated, Any, Dict, List, TypedDict


class BrandState(TypedDict):
    raw_trends: List[Dict[str, Any]]
    filtered_trend: Dict[str, Any]
    concept_proposals: List[Dict[str, Any]]
    selected_concept: Dict[str, Any]
    generated_assets: Dict[str, Any]
    compliance_passed: bool
    human_approval: str  # "APPROVED", "REJECTED", "PENDING"
    # The reducer (operator.add) means each node returns ONLY its new log
    # lines and LangGraph appends them, instead of overwriting the list.
    execution_log: Annotated[List[str], operator.add]
