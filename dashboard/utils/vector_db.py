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

from utils.constants import CHUNK_OVERLAP, CHUNK_SIZE

if not os.getenv("PINECONE_API_KEY"):
    raise Exception("DEBUG: PINECONE_API_KEY not set in environment variables. Please set it before running the script.")


def get_gemini_api_key_from_mongo():
    """Get Gemini API key from MongoDB config collection with fallback to environment variable"""
    try:
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        
        # Add database path to sys.path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "database"))
        
        from mongo_client import get_mongo_client
        
        # Get from MongoDB config collection
        db = get_mongo_client()
        config_collection = db["config"]
        
        gemini_config = config_collection.find_one({"key": "gemini_api_key"})
        if gemini_config and gemini_config.get("value"):
            api_key = gemini_config["value"]
            print("DEBUG: Using Gemini API key from MongoDB config")
            return api_key
            
    except Exception as e:
        print(f"DEBUG: Error fetching Gemini API key from MongoDB: {e}")
    
    # Fallback to environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("DEBUG: Using Gemini API key from environment variable")
        return api_key
    
    print("DEBUG: No Gemini API key found in MongoDB or environment")
    return None


def get_gemini_embeddings():
    """Get GoogleGenerativeAI embeddings with dynamic API key"""
    try:
        api_key = get_gemini_api_key_from_mongo()
        if not api_key:
            raise ValueError("Gemini API key not found in MongoDB or environment variables")
        
        return GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=api_key
        )
    except Exception as e:
        print(f"ERROR: Failed to create embeddings: {e}")
        raise


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

    print("DEBUG: Creating GoogleGenerativeAIEmbeddings with dynamic API key")
    embed = get_gemini_embeddings()
    
    vector_store = PineconeVectorStore(index=index, embedding=embed)

    print("DEBUG: Initialized PineconeVectorStore")
    print(f"DEBUG: Vector store initialized with index: {index_name}")

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


def get_pinecone_stats():
    """
    Get statistics from Pinecone index
    
    Returns:
        Dictionary with Pinecone index statistics
    """
    try:
        pinecone_api_key = os.environ.get("PINECONE_API_KEY")
        pc = Pinecone(api_key=pinecone_api_key)
        index_name = os.getenv("PINECONE_INDEX_NAME", "ask-nour")
        
        if pc.has_index(index_name):
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            return stats
        else:
            return {'total_vector_count': 0}
    except Exception as e:
        print(f"DEBUG: Error getting Pinecone stats: {str(e)}")
        return {'total_vector_count': 0}
