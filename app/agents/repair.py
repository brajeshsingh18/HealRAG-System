from agents.generator import llm
from retrieval.retriever import retrieval_func
from agents.generator import generate_answer

def repair_system(root_cause,query,docs,answer):
    action=root_cause['recommended_action']
    context = "\n\n".join(
        doc.page_content for doc in docs
    )

    if action == "QUERY_REWRITE_AND_RETRIEVE":
        prompt = f"""
            You are an expert Retrieval Optimization Agent.

            The original user query failed to retrieve sufficiently relevant information.

            Your task:
            1. Analyze the user query.
            2. Identify missing context, ambiguity, or poor wording.
            3. Rewrite the query to maximize retrieval quality.
            4. Preserve the original intent.
            5. Add relevant keywords, synonyms, and domain-specific terminology.
            6. Do not answer the question.
            7. Do not explain.
            8. Do not add bullet points.
            9. Do not include quotation marks.

            Original Query:
            {query}

            Return ONLY the rewritten query.
            """
        revised_query=llm.invoke(prompt).content
        new_docs=retrieval_func(revised_query)
        ans=generate_answer(revised_query,new_docs)
        return {
                "action": action,
                "query": revised_query,
                "docs": new_docs,
                "answer": ans
                }

    
    elif action == "REGENERATE_WITH_CONTEXT_CONSTRAINTS":
        prompt = f"""
            You are a factual answer generation agent.

            Your previous answer contained unsupported claims.

            Rules:
            1. Use ONLY information present in the provided context.
            2. Do NOT use prior knowledge.
            3. Do NOT infer facts not explicitly supported.
            4. If the context is insufficient, clearly state:
            "The provided context does not contain enough information."
            5. Every major statement must be grounded in the context.

            Question:
            {query}

            Context:
            {context}

            Previous Answer:
            {answer}

            Generate a corrected answer grounded entirely in the context.
            """
        ans=llm.invoke(prompt).content
        return {
                'action':action,
                'answer':ans
                }
        
    elif action == "EXPAND_AND_REWRITE":
        prompt = f"""
            You are an expert technical writer.

            The answer is factually correct but lacks quality.

            Improve the answer by:

            1. Increasing completeness.
            2. Improving clarity.
            3. Adding examples where appropriate.
            4. Improving structure.
            5. Explaining concepts more deeply.
            6. Removing ambiguity.
            7. Preserving factual correctness.

            Question:
            {query}

            Context:
            {context}

            Current Answer:
            {answer}

            Generate a substantially improved version of the answer.
            """
        ans=llm.invoke(prompt).content
        return {
                'action':action,
                'answer':ans
                }
        

    elif action == "ACCEPT":
        return {
                'action':action,
                'answer':answer
                }
        