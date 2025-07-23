import os
import dotenv
dotenv.load_dotenv()
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from pinecone import ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from uuid import uuid4

from constants import CHUNK_OVERLAP, CHUNK_SIZE

if not os.getenv("PINECONE_API_KEY"):
    raise Exception("DEBUG: PINECONE_API_KEY not set in environment variables. Please set it before running the script.")



def get_pinecone_vector_store():
    print("DEBUG: Starting get_vector_store()")

    pinecone_api_key = os.environ.get("PINECONE_API_KEY")

    pc = Pinecone(api_key=pinecone_api_key)

    index_name = os.getenv("PINECONE_INDEX_NAME", "ask-nour")

    index_already_exists = pc.has_index(index_name)
    if not index_already_exists:
        pc.create_index(
            name=index_name,
            dimension=3072,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"DEBUG: Created Pinecone index '{index_name}'")


    index = pc.Index(index_name)
    print("DEBUG: Created GoogleGenerativeAIEmbeddings with model: gemini-embedding-001")
    embed = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vector_store = PineconeVectorStore(index=index, embedding=embed)

    return vector_store

def add_documents_to_vector_store(vector_store, documents, metadatas=None):
    """
    Add documents to the Pinecone vector store.
    """
    if not documents:
        print("DEBUG: No documents to add.")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    print(f"DEBUG: Splitting {len(documents)} documents into chunks")
    docs = text_splitter.create_documents(documents, metadatas=metadatas)
    
    uuids = [str(uuid4()) for _ in range(len(docs))]
    vector_store.add_documents(documents=docs, ids=uuids)
    
    print(f"DEBUG: Added {len(docs)} documents to the vector store")