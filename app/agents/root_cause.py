from pydantic import BaseModel
from typing import List
from agents.generator import llm

class RootCause(BaseModel):
    primary_root_cause: str
    secondary_causes: List[str]
    reason: str
    recommended_action: str

def find_root_cause(retrieval_output,hallucination_output,quality_output):
    prompt = f"""
            You are an Enterprise AI Root Cause Analysis Agent.

            Your task is to analyze auditor outputs and determine:

            1. The PRIMARY root cause.
            2. Any SECONDARY causes.
            3. The reasoning behind the diagnosis.
            4. The best repair action.

            Available Root Causes:

            - RETRIEVAL_FAILURE
            Meaning:
            Retrieved documents are insufficient, irrelevant, incomplete,
            or do not adequately support answering the user query.

            - GENERATION_HALLUCINATION
            Meaning:
            The generated answer contains unsupported claims,
            fabricated information, or facts not grounded in retrieved context.

            - LOW_ANSWER_QUALITY
            Meaning:
            The answer is factually supported but lacks completeness,
            depth, examples, clarity, structure, or usefulness.

            Diagnosis Rules:

            1. If retrieval quality is poor, treat RETRIEVAL_FAILURE as the
            primary root cause because retrieval happens before generation.

            2. If retrieval quality is good but hallucination exists,
            treat GENERATION_HALLUCINATION as the primary root cause.

            3. If retrieval and hallucination are acceptable but the answer
            lacks depth, completeness, examples, or clarity,
            treat LOW_ANSWER_QUALITY as the primary root cause.

            4. Multiple causes may exist.

            Available Repair Actions:

            - QUERY_REWRITE_AND_RETRIEVE
            - REGENERATE_WITH_CONTEXT_CONSTRAINTS
            - EXPAND_AND_REWRITE
            - ACCEPT

            Auditor Outputs:

            Retrieval Auditor:
            {retrieval_output}

            Hallucination Auditor:
            {hallucination_output}

            Quality Auditor:
            {quality_output}

            Return ONLY valid JSON.

            {{
                "primary_root_cause": str,
                "secondary_causes": [str],
                "reason": str,
                "recommended_action": str
            }}
            """
    llm_root_cause=llm.with_structured_output(RootCause)
    out=llm_root_cause.invoke(prompt)
    return {
            'primary_root_cause':out.primary_root_cause,
            'secondary_causes':out.secondary_causes,
            'reason':out.reason,
            'recommended_action':out.recommended_action
            }