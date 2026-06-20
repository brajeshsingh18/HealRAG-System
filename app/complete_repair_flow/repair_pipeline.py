from app.retrieval.retriever import retrieval_func
from app.agents.generator import generate_answer

from app.auditors.retrieval import retrieval_auditor
from app.auditors.hallucination import hallucination_checker
from app.auditors.quality import quality_auditor

from app.agents.root_cause import find_root_cause
from app.agents.repair import repair_system

from app.verdict_of_issue import get_verdict


def run_self_healing_pipeline(query):

    docs = retrieval_func(query)

    MAX_RETRIES = 3

    last_root_cause = None
    last_answer = None

    for attempt in range(MAX_RETRIES + 1):

        answer = generate_answer(query, docs)

        retrieval_result = retrieval_auditor(query, docs)   

        hallucination_result = hallucination_checker(
            docs,
            answer
        )

        quality_result = quality_auditor(
            query,
            answer
        )

        verdict = get_verdict(
            retrieval_result["retrieval_score"],
            hallucination_result["hallucination_verdict"],
            quality_result["quality_score"],
            hallucination_result["confidence"]
        )

        if verdict == "PASS":

            return {
                "status": "SUCCESS",
                "answer": answer,
                "retries_used": attempt
            }

        last_root_cause = find_root_cause(
            retrieval_result,
            hallucination_result,
            quality_result
        )

        last_answer = answer

        if retrieval_result["retrieval_score"] <= 2:
            return {
                "status": "OUT_OF_SCOPE",
                "answer": last_answer,
                "root_cause": last_root_cause,
                "message": "Knowledge base does not contain information required to answer the query."
                }

        if attempt == MAX_RETRIES:
            break

        repaired_output = repair_system(last_root_cause,query,docs,answer)
        if isinstance(repaired_output, dict):

            answer = repaired_output["answer"]

            if "docs" in repaired_output:
                docs = repaired_output["docs"]

        else:
            answer = repaired_output

    return {
        "status": "FAILED",
        "answer": last_answer,
        "root_cause": last_root_cause,
        "retries_used": MAX_RETRIES,
        "message": "Maximum repair attempts reached."
    }