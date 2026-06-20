from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


loader=PyPDFLoader("data/docs/Machine_Deep_Learning_Concepts.pdf")
text=loader.load()

splitter=RecursiveCharacterTextSplitter(chunk_size=500,
    chunk_overlap=100)
chunks=splitter.split_documents( text)
# print(chunks)

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)
vector_store=FAISS.from_documents(chunks,embeddings)
vector_store.save_local(
    "data/faiss"
)

