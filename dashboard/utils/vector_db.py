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


def list_uploaded_files():
    """
    Get list of uploaded files from MongoDB
    
    Returns:
        List of dictionaries containing file information
    """
    try:
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        
        # Add database path to sys.path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "database"))
        
        from mongo_client import get_mongo_client
        
        db = get_mongo_client()
        files_collection = db["uploaded_files"]
        
        # Get all uploaded files, sorted by upload time (newest first)
        files = list(files_collection.find({}, {"_id": 0}).sort("upload_time", -1))
        
        return files
        
    except Exception as e:
        print(f"DEBUG: Error listing uploaded files: {str(e)}")
        return []


def add_file_to_database(filename, upload_time, file_type="document"):
    """
    Add a file record to MongoDB when it's uploaded
    
    Args:
        filename: Name of the uploaded file
        upload_time: ISO timestamp of upload
        file_type: Type of file (document, image, video)
    """
    try:
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        
        # Add database path to sys.path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "database"))
        
        from mongo_client import get_mongo_client
        
        db = get_mongo_client()
        files_collection = db["uploaded_files"]
        
        # Check if file already exists
        existing_file = files_collection.find_one({"filename": filename})
        if existing_file:
            # Update the existing record
            files_collection.update_one(
                {"filename": filename},
                {"$set": {
                    "upload_time": upload_time,
                    "file_type": file_type,
                    "updated_at": upload_time
                }}
            )
            print(f"DEBUG: Updated existing file record: {filename}")
        else:
            # Insert new record
            file_record = {
                "filename": filename,
                "upload_time": upload_time,
                "file_type": file_type,
                "created_at": upload_time
            }
            files_collection.insert_one(file_record)
            print(f"DEBUG: Added file record to database: {filename}")
        
    except Exception as e:
        print(f"DEBUG: Error adding file to database: {str(e)}")


def delete_file_from_pinecone(filename):
    """
    Delete all vectors for a specific file from Pinecone and remove from MongoDB
    
    Args:
        filename: The source filename to delete
        
    Returns:
        Dictionary with deletion results
    """
    try:
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        
        # Add database path to sys.path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "database"))
        
        from mongo_client import get_mongo_client
        
        # First check if file exists in our database
        db = get_mongo_client()
        files_collection = db["uploaded_files"]
        
        file_record = files_collection.find_one({"filename": filename})
        if not file_record:
            return {"success": False, "message": f"File not found in database: {filename}"}
        
        file_type = file_record.get("file_type", "document")
        
        # Handle different file types differently
        if file_type == "document":
            # For documents, delete from Pinecone
            return delete_document_from_pinecone(filename, files_collection)
        elif file_type == "images_csv":
            # For images CSV, delete from MongoDB images collection
            return delete_csv_data_from_mongodb(filename, files_collection, "images", "Images")
        elif file_type == "videos_csv":
            # For videos CSV, delete from MongoDB videos collection
            return delete_csv_data_from_mongodb(filename, files_collection, "videos", "Videos")
        else:
            return {"success": False, "message": f"Unknown file type: {file_type}"}
        
    except Exception as e:
        print(f"DEBUG: Error deleting file: {str(e)}")
        return {"success": False, "message": f"Error deleting file: {str(e)}"}


def delete_document_from_pinecone(filename, files_collection):
    """Delete document vectors from Pinecone"""
    try:
        # Connect to Pinecone
        pinecone_api_key = os.environ.get("PINECONE_API_KEY")
        pc = Pinecone(api_key=pinecone_api_key)
        index_name = os.getenv("PINECONE_INDEX_NAME", "ask-nour")
        
        if not pc.has_index(index_name):
            return {"success": False, "message": "Pinecone index not found"}
            
        index = pc.Index(index_name)
        
        # Delete vectors by metadata filter
        try:
            delete_response = index.delete(
                filter={"source": {"$eq": filename}},
                namespace=""  # Use default namespace
            )
            print(f"DEBUG: Pinecone delete response: {delete_response}")
        except Exception as pinecone_error:
            print(f"DEBUG: Error deleting from Pinecone: {str(pinecone_error)}")
            # Continue with MongoDB deletion even if Pinecone fails
        
        # Remove from MongoDB
        delete_result = files_collection.delete_one({"filename": filename})
        
        if delete_result.deleted_count > 0:
            return {
                "success": True, 
                "message": f"Successfully deleted document: {filename}",
                "deleted_from_db": True
            }
        else:
            return {"success": False, "message": f"Failed to delete file from database: {filename}"}
            
    except Exception as e:
        print(f"DEBUG: Error deleting document from Pinecone: {str(e)}")
        return {"success": False, "message": f"Error deleting document: {str(e)}"}


def delete_csv_data_from_mongodb(filename, files_collection, collection_name, display_name):
    """Delete CSV data from MongoDB collection"""
    try:
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        
        # Add database path to sys.path
        project_root = Path(__file__).parent.parent.parent
        sys.path.append(str(project_root / "database"))
        
        from mongo_client import get_mongo_client
        from utils.constants import IMAGES_COLLECTION, VIDEOS_COLLECTION
        
        db = get_mongo_client()
        
        # Get the appropriate collection
        if collection_name == "images":
            target_collection = db[IMAGES_COLLECTION]
        elif collection_name == "videos":
            target_collection = db[VIDEOS_COLLECTION]
        else:
            return {"success": False, "message": f"Unknown collection: {collection_name}"}
        
        # Get the file record to check upload batch info
        file_record = files_collection.find_one({"filename": filename})
        if not file_record:
            return {"success": False, "message": f"File record not found: {filename}"}
        
        # First try to delete by uploaded_from field (most precise)
        delete_query = {"uploaded_from": filename}
        doc_count = target_collection.count_documents(delete_query)
        
        if doc_count > 0:
            # Delete documents that match the filename
            delete_result = target_collection.delete_many(delete_query)
            deleted_count = delete_result.deleted_count
            print(f"DEBUG: Deleted {deleted_count} documents using uploaded_from field")
        else:
            # Fallback: try time-based deletion if uploaded_from doesn't work
            upload_time = file_record.get("upload_time")
            
            if upload_time:
                try:
                    from datetime import datetime, timedelta
                    
                    upload_dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                    time_start = (upload_dt - timedelta(minutes=2)).isoformat()
                    time_end = (upload_dt + timedelta(minutes=2)).isoformat()
                    
                    # Use uploaded_at field for time-based deletion
                    time_query = {
                        "uploaded_at": {
                            "$gte": time_start,
                            "$lte": time_end
                        }
                    }
                    
                    doc_count = target_collection.count_documents(time_query)
                    
                    if doc_count > 0:
                        delete_result = target_collection.delete_many(time_query)
                        deleted_count = delete_result.deleted_count
                        print(f"DEBUG: Deleted {deleted_count} documents using time-based query")
                    else:
                        deleted_count = 0
                        print(f"DEBUG: No documents found for time-based deletion")
                        
                except Exception as date_error:
                    print(f"DEBUG: Error with time-based deletion: {str(date_error)}")
                    deleted_count = 0
            else:
                print(f"DEBUG: No upload time available, cannot perform deletion")
                deleted_count = 0
        
        # Only remove file record if we actually deleted some documents
        if deleted_count > 0:
            files_collection.delete_one({"filename": filename})
            
            return {
                "success": True,
                "message": f"Successfully deleted {display_name} CSV data: {filename} ({deleted_count} records removed)",
                "deleted_count": deleted_count,
                "deleted_from_db": True
            }
        else:
            # Even if no documents were found, remove the file record from the list
            # This handles cases where the CSV data was already deleted but the file record remains
            files_collection.delete_one({"filename": filename})
            
            return {
                "success": True,
                "message": f"File removed from list: {filename}. No {display_name} records were found - the data may have been already deleted.",
                "deleted_count": 0,
                "deleted_from_db": True
            }
        
    except Exception as e:
        print(f"DEBUG: Error deleting CSV data: {str(e)}")
        return {"success": False, "message": f"Error deleting {display_name} CSV data: {str(e)}"}
