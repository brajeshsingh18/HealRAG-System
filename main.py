from app.retrieval.retriever import retrieval_func
from app.agents.generator import generate_answer
from app.auditors.hallucination import hallucination_checker
from app.auditors.quality import quality_auditor
from app.auditors.retrieval import retrieval_auditor
from app.complete_repair_flow.repair_pipeline import run_self_healing_pipeline


query = input("Enter Query: ")

result = run_self_healing_pipeline(query)

print("\n" + "=" * 60)

if result["status"] == "SUCCESS":

    print("ANSWER:")
    print(result["answer"])

    print(f"\nRetries Used: {result['retries_used']}")

elif result["status"]=="OUT_OF_SCOPE":
    print("FINAL ANSWER:")
    print(result["answer"])
    print("\nROOT CAUSE:")
    print(result["root_cause"])
    print("STATUS:")
    print(result['message'])


else:

    print("FINAL ANSWER:")
    print(result["answer"])

    print("\nROOT CAUSE:")
    print(result["root_cause"])

    print(f"\nRetries Used: {result['retries_used']}")

    print("\nSTATUS:")
    print(result["message"])
