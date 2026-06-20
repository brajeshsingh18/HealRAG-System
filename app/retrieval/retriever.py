from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)

vector_store = FAISS.load_local(
    "data/faiss",
    embeddings,
    allow_dangerous_deserialization=True
)
def retrieval_func(question:str):
    """
    Retrieve top-k relevant documents.
    Returns:
        list: Retrieved documents.
    """
    docs = vector_store.similarity_search(
        question,
        k=3
    )
    return docs
