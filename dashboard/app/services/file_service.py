"""
File handling service layer
"""

import os
import uuid
import sys
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from utils.vector_db import get_pinecone_vector_store, add_documents_to_vector_store, get_pinecone_stats


def process_uploaded_file(file: UploadFile) -> JSONResponse:
    """
    Process uploaded file: temporarily save, load content, add to vector store, then delete
    
    Args:
        file: UploadFile object from FastAPI
        
    Returns:
        JSONResponse with success or error message
    """
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join("uploads", filename)

    try:
        # Save file temporarily
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Load file content using appropriate loader
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file.filename.endswith(".txt"):
            loader = TextLoader(file_path)
        elif file.filename.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            return JSONResponse(content={"message": "❌ Unsupported file type. Please upload a PDF, TXT, or DOCX file."})

        docs = loader.load()

        # Store in Pinecone
        vector_store = get_pinecone_vector_store()
        add_documents_to_vector_store(
            vector_store,
            [doc.page_content for doc in docs],
            metadatas=[{"source": file.filename, "upload_time": datetime.now().isoformat()} for _ in docs]
        )

        # Update last upload time
        update_last_upload_time()

        return JSONResponse(content={"message": f"✅ Successfully processed {file.filename} and added {len(docs)} chunks to Ask Nour's knowledge base!"})

    except Exception as e:
        return JSONResponse(content={"message": f"❌ Error processing file: {str(e)}"})
    
    finally:
        # Always delete the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


def update_last_upload_time():
    """Update the last upload timestamp in a simple file"""
    try:
        with open("last_upload.txt", "w") as f:
            f.write(datetime.now().isoformat())
    except Exception:
        pass  # Ignore errors for timestamp tracking


def get_last_upload_time():
    """Get the last upload timestamp"""
    try:
        if os.path.exists("last_upload.txt"):
            with open("last_upload.txt", "r") as f:
                timestamp = f.read().strip()
                dt = datetime.fromisoformat(timestamp)
                return dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        pass
    return "Never"


def get_knowledge_base_stats():
    """Get statistics about the knowledge base from Pinecone"""
    try:
        stats = get_pinecone_stats()
        return {
            "total_vectors": stats.get('total_vector_count', 0),
            "last_upload": get_last_upload_time()
        }
    except Exception as e:
        print(f"DEBUG: Error getting knowledge base stats: {str(e)}")
        return {
            "total_vectors": 0,
            "last_upload": "Never"
        }
