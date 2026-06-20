from state import State
from retrieval.retriever import retrieval_func
from agents.generator import generate_answer
from auditors.retrieval import retrieval_auditor
from auditors.hallucination import hallucination_checker
from auditors.quality import quality_auditor
from agents.root_cause import find_root_cause
from agents.repair import repair_system
from verdict_of_issue import get_verdict
from langgraph.graph import StateGraph,START,END


 
def retrieve_node(state:State):                          
    query=state['query']
    docs=retrieval_func(query)
    return {'documents':docs}




def generate_node(state:State):
    query=state['query']
    docs=state['documents']
    ans=generate_answer(query,docs)
    return {'answer':ans}




def auditor_node(state:State):
    query=state['query']
    docs=state['documents']
    answer=state['answer']

    retrieval_result = retrieval_auditor(query, docs)   
    hallucination_result = hallucination_checker(docs,answer)
    quality_result = quality_auditor(query,answer)

    retrieval_score=retrieval_result['retrieval_score']
    hallucination_status=hallucination_result['hallucination_verdict']
    confidence=hallucination_result['confidence']
    quality_score=quality_result['quality_score']

    return {
        "retrieval_score": retrieval_score,
        "hallucination_status": hallucination_status,
        "hallucination_confidence":confidence,
        "quality_score": quality_score
    }



def verdict_node(state:State):
    verdict=get_verdict(state['retrieval_score'],state['hallucination_status'],state['quality_score'],state['hallucination_confidence'])
    return {'verdict':verdict}



def audit_log_node(state: State):

    attempt = {
        "attempt_no":state["retries_count"] + 1,
        "query":state["query"],
        "answer":state["answer"],
        "retrieval_score":state["retrieval_score"],
        "hallucination_status":state["hallucination_status"],
        "hallucination_confidence":state["hallucination_confidence"],
        "quality_score":state["quality_score"],
        "verdict":state["verdict"],
        "primary_root_cause":state.get("primary_root_cause",None),
        "recommended_action":state.get("recommended_action",None)
    }

    audit_record = state["audit_record"]

    audit_record["attempts"].append(
        attempt
    )

    return {
        "audit_record": audit_record
    }




def rootcause_node(state:State):
    retrieval_result = {
        "retrieval_score": state["retrieval_score"]
    }
    hallucination_result = {
        "hallucination_verdict": state["hallucination_status"],
        "confidence": state["hallucination_confidence"]
    }
    quality_result = {
        "quality_score": state["quality_score"]
    }
    root_cause=find_root_cause(retrieval_result,hallucination_result,quality_result)
    return {
            'primary_root_cause':root_cause['primary_root_cause'],
            'recommended_action':root_cause['recommended_action']
            }



def repair_node(state: State):
    root_cause = {
        "recommended_action": state["recommended_action"]
    }
    result = repair_system(
        root_cause=root_cause,
        query=state["query"],
        docs=state["documents"],
        answer=state["answer"]
    )
    updates = {
        "retries_count": state["retries_count"] + 1
    }

    if "query" in result:
        updates["query"] = result["query"]

    if "docs" in result:
        updates["documents"] = result["docs"]

    if "answer" in result:
        updates["answer"] = result["answer"]

    return updates




def finalize_audit_log_node(state: State):

    audit_record = state["audit_record"]

    if len(audit_record["attempts"]) == 0:

        audit_record["attempts"].append(
            {
                "attempt_no":
                    state["retries_count"] + 1,

                "query":
                    state["query"],

                "answer":
                    state.get("answer", ""),

                "retrieval_score":
                    state.get(
                        "retrieval_score",
                        0
                    ),

                "hallucination_status":
                    state.get(
                        "hallucination_status",
                        "NOT_EVALUATED"
                    ),

                "quality_score":
                    state.get(
                        "quality_score",
                        0
                    ),

                "verdict":
                    "INSUFFICIENT_CONTEXT",

                "primary_root_cause":
                    "RETRIEVAL_FAILURE",

                "recommended_action":
                    "TERMINATED"
            }
        )

    audit_record["final_answer"] = \
        state["answer"]

    audit_record["final_verdict"] = \
        state.get("verdict","INSUFFICIENT_CONTEXT")

    audit_record["total_attempts"] = \
        len(
            audit_record["attempts"]
        )

    audit_record["total_repairs"] = \
        state["retries_count"]

    return {
        "audit_record":
            audit_record
    }




def save_audit_log_node(state:State):

    import json
    from pathlib import Path

    log_file = Path(
        "logs/audit_logs.json"
    )

    log_file.parent.mkdir(
        exist_ok=True
    )

    if (
    log_file.exists()
    and log_file.stat().st_size > 0
    ):
        logs = json.loads(
            log_file.read_text(
            encoding="utf-8")
        )
    else:
        logs = []


    logs.append(
        state["audit_record"]
    )

    log_file.write_text(
        json.dumps(
            logs,
            indent=4
        )
    )

    return {}



def route_after_auditor_node(state:State):
    if state['retrieval_score'] <=2:
        return "QUERY NOT ANSWERABLE"
    else:
        return "CHECK THE VERDICT"



def route_after_verdict_node(state:State):
    verdict=state['verdict']
    if verdict=='PASS':
        return "ACCEPTED"
    
    else:
        return "FINDING THE ISSUE"



def route_after_repair_node(state:State):
    if state["retries_count"] >= state["max_retries"]:
        return "MAX RETRIES REACHED"
    else:
        return "AUDIT AGAIN"
    
def route_after_audit_log_node(state:State):
    if state['verdict']=='PASS':
        return "FINALIZE THE AUDIT LOG"
    else:
        return "REPAIR IS NEEDED"
    



graph=StateGraph(State)

graph.add_node("retrieve_node",retrieve_node)
graph.add_node("generate_node",generate_node)
graph.add_node("auditor_node",auditor_node)
graph.add_node("verdict_node",verdict_node)
graph.add_node("audit_log_node",audit_log_node)
graph.add_node("rootcause_node",rootcause_node)
graph.add_node("repair_node",repair_node)
graph.add_node("finalize_audit_log_node",finalize_audit_log_node)
graph.add_node("save_audit_log_node",save_audit_log_node)

graph.add_edge(START,"retrieve_node")
graph.add_edge("retrieve_node","generate_node")
graph.add_edge("generate_node","auditor_node")
graph.add_conditional_edges("auditor_node",route_after_auditor_node,{'QUERY NOT ANSWERABLE':'finalize_audit_log_node','CHECK THE VERDICT':"verdict_node"})
graph.add_conditional_edges("verdict_node",route_after_verdict_node,{'ACCEPTED':'audit_log_node','FINDING THE ISSUE':"rootcause_node"})
graph.add_edge("rootcause_node","audit_log_node")
graph.add_conditional_edges("audit_log_node",route_after_audit_log_node,{'FINALIZE THE AUDIT LOG':'finalize_audit_log_node','REPAIR IS NEEDED':'repair_node'})
graph.add_edge("finalize_audit_log_node","save_audit_log_node")
graph.add_edge("save_audit_log_node",END)
graph.add_conditional_edges("repair_node",route_after_repair_node,{'MAX RETRIES REACHED':'finalize_audit_log_node','AUDIT AGAIN':'auditor_node'})

workflow=graph.compile()

from IPython.display import Image, display

png_data= workflow.get_graph().draw_mermaid_png()
  
with open("data/graph.png", "wb") as f:
    f.write(png_data)
print("Graph saved as graph.png")

initial_state={
        "query": "What is astronomy?",
        "retries_count": 0,
        "max_retries": 3,
        "audit_record": {
            'query':"What is astronomy?",
            'attempts':[]
        }
    }

final_state=workflow.invoke(initial_state)
print(final_state['audit_record'])




    








