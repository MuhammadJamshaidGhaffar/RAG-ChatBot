"""
File handling service layer
"""

import os
import uuid
import sys
from pathlib import Path
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from utils.vector_db import get_pinecone_vector_store, add_documents_to_vector_store


def process_uploaded_file(file: UploadFile) -> JSONResponse:
    """
    Process uploaded file: save it, load content, and add to vector store
    
    Args:
        file: UploadFile object from FastAPI
        
    Returns:
        JSONResponse with success or error message
    """
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join("uploads", filename)

    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())
    except Exception as e:
        return JSONResponse(content={"message": f"❌ Error saving file: {str(e)}"})

    # Load file content using appropriate loader
    try:
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file.filename.endswith(".txt"):
            loader = TextLoader(file_path)
        elif file.filename.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            # Clean up file if unsupported type
            if os.path.exists(file_path):
                os.remove(file_path)
            return JSONResponse(content={"message": "❌ Unsupported file type. Please upload a PDF, TXT, or DOCX file."})

        docs = loader.load()

        # Store in Pinecone
        try:
            vector_store = get_pinecone_vector_store()
            add_documents_to_vector_store(
                vector_store,
                [doc.page_content for doc in docs],
                metadatas=[{"source": file.filename} for _ in docs]
            )
        except Exception as e:
            return JSONResponse(content={"message": f"❌ Error adding documents to vector store: {str(e)}"})

        return JSONResponse(content={"message": "✅ File uploaded and indexed successfully!"})

    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        return JSONResponse(content={"message": f"❌ Error processing file: {str(e)}"})


async def handle_file_upload(file: UploadFile) -> JSONResponse:
    """
    Async wrapper for file upload handling
    
    Args:
        file: UploadFile object from FastAPI
        
    Returns:
        JSONResponse with success or error message
    """
    return process_uploaded_file(file)
