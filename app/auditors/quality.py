from agents.generator import llm
from pydantic import BaseModel
from typing import List

class QualityOutput(BaseModel):
    quality_score: int
    completeness: int
    clarity: int
    correctness: int
    relevance: int
    actionability: int
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    reason: str

llm_quality=llm.with_structured_output(QualityOutput)

def quality_auditor(ques:str,ans:str):
    prompt = f"""
            You are a senior AI Answer Quality Auditor.

            Your task is to evaluate the answer to a user question using the criteria below.

            QUESTION:
            {ques}

            ANSWER:
            {ans}

            Evaluation Criteria:

            1. Completeness (0-10)
            - Does the answer fully address all aspects of the question?
            - Are important details missing?
            - Does it provide sufficient depth?

            2. Clarity (0-10)
            - Is the answer easy to understand?
            - Is it logically structured?
            - Is the language concise and unambiguous?

            3. Correctness (0-10)
            - Is the information factually accurate?
            - Are there contradictions or misleading statements?
            - Are technical concepts explained properly?

            4. Relevance (0-10)
            - Does the answer stay focused on the user's question?
            - Does it avoid unnecessary information?

            5. Actionability (0-10)
            - If the user seeks guidance, are clear next steps provided?
            - Is the answer practically useful?

            Scoring Rules:
            - 9-10 = Excellent
            - 7-8 = Good
            - 5-6 = Acceptable but needs improvement
            - 3-4 = Poor
            - 0-2 = Very poor

            Compute:
            quality_score = average of all five criteria rounded to nearest integer.

            Provide:
            - strengths
            - weaknesses
            - improvement_suggestions

            Return ONLY valid JSON.

            Schema:
            {{
                "quality_score": int,
                "completeness": int,
                "clarity": int,
                "correctness": int,
                "relevance": int,
                "actionability": int,
                "strengths": [
                    "string"
                ],
                "weaknesses": [
                    "string"
                ],
                "improvement_suggestions": [
                    "string"
                ],
                "reason": "brief overall justification"
            }}
            """
    out=llm_quality.invoke(prompt)
    return {
            "quality_score": out.quality_score,
            "completeness": out.completeness,
            "clarity": out.clarity,
            "correctness": out.correctness,
            "relevance": out.relevance,
            "actionability": out.actionability,
            "strengths": out.strengths,
            "weaknesses": out.weaknesses,
            "improvement_suggestions": out.improvement_suggestions,
            "reason": out.reason
            }