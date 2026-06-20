from agents.generator import llm
from langchain_core.documents import Document
from pydantic import BaseModel
from typing import Literal

class HallucinationOutput(BaseModel):
    hallucination_verdict: Literal["SUPPORTED" , "HALLUCINATED"]
    confidence: float
    reason: str

llm_hallucination=llm.with_structured_output(HallucinationOutput)

def hallucination_checker(docs:list[Document],answer:str):
    prompt=f"""You are a Hallucination Auditor.
            Context:
            {docs}
            Answer:
            {answer}
            Determine whether the answer is fully
            supported by the context.if there is some doubt then say "HALLUCINATED" in verdict
            reason must be short and concise and confidence must be a value between 0 to 1 based on howmuch the output is supported by documents retrieved
            Return JSON:
            {{
            "hallucination_verdict":"SUPPORTED" | "HALLUCINATED",
            "confidence": float,
            "reason": str
            }}"""
    out=llm_hallucination.invoke(prompt)
    return {
            'hallucination_verdict':out.hallucination_verdict,
            'confidence':out.confidence,
            'reason':out.reason
            }

