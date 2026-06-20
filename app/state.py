from typing import TypedDict,List,Literal
from langchain_core.documents import Document
from pydantic import Field

class State(TypedDict):
    query:str
    documents:List[Document]
    answer:str
    citations:List[str]
    retrieval_score:int # =Field(le=10,ge=0)
    hallucination_status:Literal["SUPPORTED","HALLUCINATED"]
    hallucination_confidence: float
    quality_score:int # Field(le=10,ge=0)
    verdict:Literal["PASS","FAIL"]  # Field(description='Represents whether the current answer is acceptable or some changes needed')
    primary_root_cause:Literal["RETRIEVAL_FAILURE","GENERATION_HALLUCINATION","LOW_ANSWER_QUALITY"] # =Field(description="According to priority which is affecting the answer first and also the most")
    recommended_action:Literal["QUERY_REWRITE_AND_RETRIEVE","REGENERATE_WITH_CONTEXT_CONSTRAINTS","EXPAND_AND_REWRITE","ACCEPT"]
    retries_count:int # =Field(description="No. of attempts of finding an acceptable answer")
    max_retries:int
    audit_record:dict

