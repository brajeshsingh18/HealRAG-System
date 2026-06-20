from langchain_core.documents import Document
from agents.generator import llm
from pydantic import BaseModel
class RetrievalOutput(BaseModel):
    retrieval_score:int
    reason:str
llm_retrieval=llm.with_structured_output(RetrievalOutput)
def retrieval_auditor(ques:str,docs:list[Document]):
    prompt=f"""You are a Retrieval Auditor.
            Question:
            {ques}
            Retrieved Documents:
            {docs}
            Rate relevance from 1 to 10.
            the reason present in the json for the score provided must be concise and brief
            Return JSON:
            {{
            "retrieval_score": int,
            "reason": str
            }}"""
    out=llm_retrieval.invoke(prompt)
    return {'retrieval_score':out.retrieval_score,
            'reason':out.reason}
    