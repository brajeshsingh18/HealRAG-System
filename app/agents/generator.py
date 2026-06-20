from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.documents import Document
load_dotenv()
llm=ChatGroq(model="llama-3.3-70b-versatile")

def generate_answer(question:str,retrieved_docs:list[Document]):
    context="\n\n".join([doc.page_content for doc in retrieved_docs])
    prompt=f"""
    Answer the question using only
    the provided context.
    Context: {context}
    Question: {question} """
    out=llm.invoke(prompt)
    return out.content
