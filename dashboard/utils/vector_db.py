"""
Vector database utilities and operations
"""

import os
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from pinecone import ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from uuid import uuid4

from utils.constants import INIT_TEXT, CHUNK_OVERLAP, CHUNK_SIZE

if not os.getenv("PINECONE_API_KEY"):
    raise Exception("DEBUG: PINECONE_API_KEY not set in environment variables. Please set it before running the script.")


def get_pinecone_vector_store():
    """
    Initialize and return Pinecone vector store
    
    Returns:
        PineconeVectorStore instance
    """
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

    index = pc.Index(index_name)

    print("DEBUG: Created GoogleGenerativeAIEmbeddings with model: gemini-embedding-001")
    embed = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    
    vector_store = PineconeVectorStore(index=index, embedding=embed)

    if not index_already_exists:
        print("DEBUG: Initializing Pinecone with intro document")
        
        add_documents_to_vector_store(
            vector_store,
            [INIT_TEXT],
            metadatas=[{"source": "intro"}]
        )

        print(f"DEBUG: ✅ Initialized Pinecone with intro doc and saved to {index_name}")

    return vector_store


def add_documents_to_vector_store(vector_store, documents, metadatas=None):
    """
    Add documents to the Pinecone vector store.
    
    Args:
        vector_store: PineconeVectorStore instance
        documents: List of document strings to add
        metadatas: Optional list of metadata dictionaries
    """   
    if not isinstance(documents, list):
        raise ValueError("DEBUG: Documents should be a list of strings.")
    
    if metadatas is None:
        metadatas = [{} for _ in documents]
    
    if len(documents) != len(metadatas):
        raise ValueError("DEBUG: Length of documents and metadatas must match.")
    
    print(f"DEBUG: Adding {len(documents)} documents to vector store")
    if not documents:
        print("DEBUG: No documents to add.")
        raise ValueError("DEBUG: No documents to add to the vector store.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    print(f"DEBUG: Splitting {len(documents)} documents into chunks")
    docs = text_splitter.create_documents(documents, metadatas=metadatas)
    
    uuids = [str(uuid4()) for _ in range(len(docs))]
    vector_store.add_documents(documents=docs, ids=uuids)
    
    print(f"DEBUG: Added {len(docs)} documents to the vector store")
