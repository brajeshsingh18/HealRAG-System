def get_verdict(
    retrieval_score: int,
    hallucination_status: str,
    quality_score: int,
    hallucination_confidence: float
) -> str:

    if hallucination_status != "SUPPORTED":
        return "FAIL"

    if retrieval_score < 7:
        return "FAIL"

    if quality_score < 7:
        return "FAIL"

    final_score = (
        0.5 * retrieval_score +
        0.3 * quality_score +
        0.2 * hallucination_confidence * 10
    )

    return "PASS" if final_score >= 8 else "FAIL"