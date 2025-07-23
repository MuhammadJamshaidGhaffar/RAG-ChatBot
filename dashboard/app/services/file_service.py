"""
File handling service layer
"""

import os
import uuid
import sys
import csv
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from docx import Document
from docx.oxml.shared import qn
import os
# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import database utilities
sys.path.append(str(project_root / "database"))
from mongo_client import get_mongo_client
from utils.constants import IMAGES_COLLECTION, VIDEOS_COLLECTION, EXTRAS_COLLECTION

from utils.vector_db import get_pinecone_vector_store, add_documents_to_vector_store, get_pinecone_stats


def process_uploaded_file(file: UploadFile, upload_type: str = "document") -> JSONResponse:
    """
    Process uploaded file: temporarily save, load content, add to vector store or database, then delete
    
    Args:
        file: UploadFile object from FastAPI
        upload_type: Type of upload - "document", "images_csv", "videos_csv"
        
    Returns:
        JSONResponse with success or error message
    """
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join("uploads", filename)

    try:
        # Save file temporarily
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Handle different upload types
        if upload_type == "document":
            # Handle document files for knowledge base
            if file.filename.endswith(".pdf"):
                return process_document_file(file_path, file.filename, "pdf")
            elif file.filename.endswith(".txt"):
                return process_document_file(file_path, file.filename, "txt")
            elif file.filename.endswith(".docx"):
                return process_document_file(file_path, file.filename, "docx")
            else:
                return JSONResponse(content={"message": "❌ For document upload, please upload a PDF, TXT, or DOCX file."})
        
        elif upload_type == "images_csv":
            # Handle images CSV upload
            if file.filename.endswith(".csv"):
                return upload_images_csv(file_path, file.filename)
            else:
                return JSONResponse(content={"message": "❌ For images upload, please upload a CSV file."})
        
        elif upload_type == "videos_csv":
            # Handle videos CSV upload
            if file.filename.endswith(".csv"):
                return upload_videos_csv(file_path, file.filename)
            else:
                return JSONResponse(content={"message": "❌ For videos upload, please upload a CSV file."})
        
        else:
            return JSONResponse(content={"message": "❌ Invalid upload type specified."})

    except Exception as e:
        return JSONResponse(content={"message": f"❌ Error processing file: {str(e)}"})
    
    finally:
        # Always delete the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


# Convenience functions for specific upload types
def process_document_upload(file: UploadFile) -> JSONResponse:
    """Process document file for knowledge base."""
    return process_uploaded_file(file, "document")


def process_images_csv_upload(file: UploadFile) -> JSONResponse:
    """Process images CSV file for images collection."""
    return process_uploaded_file(file, "images_csv")


def process_videos_csv_upload(file: UploadFile) -> JSONResponse:
    """Process videos CSV file for videos collection."""
    return process_uploaded_file(file, "videos_csv")


def process_document_file(file_path: str, filename: str, file_type: str) -> JSONResponse:
    """Process document files (PDF, TXT, DOCX) for vector store."""
    try:
        if file_type == "pdf":
            loader = PyPDFLoader(file_path)
            docs = loader.load()
        elif file_type == "txt":
            loader = TextLoader(file_path)
            docs = loader.load()
        elif file_type == "docx":
            # Use custom function to preserve layout and hyperlinks
            docx_content = extract_docx_with_layout_preserved(file_path)
            # Create a document-like object to maintain consistency
            docs = [type('Document', (), {
                'page_content': docx_content,
                'metadata': {"source": filename}
            })()]
        else:
            return JSONResponse(content={"message": "❌ Unsupported document type."})

        # Store in Pinecone
        vector_store = get_pinecone_vector_store()
        add_documents_to_vector_store(
            vector_store,
            [doc.page_content for doc in docs],
            metadatas=[{"source": filename, "upload_time": datetime.now().isoformat()} for _ in docs]
        )

        # Update last upload time
        update_last_upload_time()

        return JSONResponse(content={"message": f"✅ Successfully processed {filename} and added {len(docs)} chunks to Ask Nour's knowledge base!"})

    except Exception as e:
        return JSONResponse(content={"message": f"❌ Error processing document: {str(e)}"})


def upload_images_csv(file_path: str, filename: str) -> JSONResponse:
    """Upload images from CSV to MongoDB images collection with hardcoded keys."""
    try:
        db = get_mongo_client()
        collection = db[IMAGES_COLLECTION]
        
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Skip header row (first row contains column headers and is ignored)
            next(reader, None)
            
            images = []
            for row_num, row in enumerate(reader, 1):
                if len(row) >= 1:  # At least image URL required
                    image_doc = {
                        "image_url": row[0].strip(),
                        "image_description": row[1].strip() if len(row) > 1 else "",
                        "uploaded_at": datetime.now().isoformat(),
                        "uploaded_from": filename,
                        "row_number": row_num
                    }
                    images.append(image_doc)
            
            if images:
                collection.insert_many(images)
                # Update last upload time
                update_last_upload_time()
                return JSONResponse(content={
                    "message": f"✅ Successfully uploaded {len(images)} images from {filename} to the images collection!",
                    "count": len(images)
                })
            else:
                return JSONResponse(content={"message": "❌ No valid image data found in CSV file."})
                
    except Exception as e:
        return JSONResponse(content={"message": f"❌ Error uploading images CSV: {str(e)}"})


def upload_videos_csv(file_path: str, filename: str) -> JSONResponse:
    """Upload videos from CSV to MongoDB videos collection with hardcoded keys."""
    try:
        db = get_mongo_client()
        collection = db[VIDEOS_COLLECTION]
        
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Skip header row (first row contains column headers and is ignored)
            next(reader, None)
            
            videos = []
            for row_num, row in enumerate(reader, 1):
                if len(row) >= 1:  # At least video URL required
                    video_doc = {
                        "video_url": row[0].strip(),
                        "video_description": row[1].strip() if len(row) > 1 else "",
                        "uploaded_at": datetime.now().isoformat(),
                        "uploaded_from": filename,
                        "row_number": row_num
                    }
                    videos.append(video_doc)
            
            if videos:
                collection.insert_many(videos)
                # Update last upload time
                update_last_upload_time()
                return JSONResponse(content={
                    "message": f"✅ Successfully uploaded {len(videos)} videos from {filename} to the videos collection!",
                    "count": len(videos)
                })
            else:
                return JSONResponse(content={"message": "❌ No valid video data found in CSV file."})
                
    except Exception as e:
        return JSONResponse(content={"message": f"❌ Error uploading videos CSV: {str(e)}"})


def update_last_upload_time():
    """Update the last upload timestamp in MongoDB extras collection"""
    try:
        db = get_mongo_client()
        collection = db[EXTRAS_COLLECTION]
        
        # Upsert the last upload time document
        collection.update_one(
            {"type": "last_upload"},
            {
                "$set": {
                    "type": "last_upload",
                    "timestamp": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            },
            upsert=True
        )
    except Exception as e:
        print(f"DEBUG: Error updating last upload time: {str(e)}")


def get_last_upload_time():
    """Get the last upload timestamp from MongoDB extras collection"""
    try:
        db = get_mongo_client()
        collection = db[EXTRAS_COLLECTION]
        
        # Find the last upload document
        last_upload_doc = collection.find_one({"type": "last_upload"})
        
        if last_upload_doc and "timestamp" in last_upload_doc:
            timestamp = last_upload_doc["timestamp"]
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception as e:
        print(f"DEBUG: Error getting last upload time: {str(e)}")
    
    return "Never"


def get_knowledge_base_stats():
    """Get statistics about the knowledge base from Pinecone and MongoDB collections"""
    try:
        # Get Pinecone stats
        pinecone_stats = get_pinecone_stats()
        
        # Get MongoDB stats
        db = get_mongo_client()
        images_count = db[IMAGES_COLLECTION].count_documents({})
        videos_count = db[VIDEOS_COLLECTION].count_documents({})
        
        return {
            "total_vectors": pinecone_stats.get('total_vector_count', 0),
            "total_images": images_count,
            "total_videos": videos_count,
            "last_upload": get_last_upload_time()
        }
    except Exception as e:
        print(f"DEBUG: Error getting knowledge base stats: {str(e)}")
        return {
            "total_vectors": 0,
            "total_images": 0,
            "total_videos": 0,
            "last_upload": "Never"
        }


# This function is to be used insdie extract_docx_with_layout_preserved ...
def extract_hyperlinks_from_paragraph(paragraph):
    """
    Extract hyperlinks from a paragraph by parsing the XML structure.
    """
    hyperlinks = {}
    
    # Get all hyperlink elements in the paragraph
    for hyperlink in paragraph._element.xpath('.//w:hyperlink'):
        r_id = hyperlink.get(qn('r:id'))
        if r_id:
            # Get the URL from the document relationships
            try:
                url = paragraph.part.rels[r_id].target_ref
                # Get the text content of the hyperlink
                link_text = ''.join([node.text for node in hyperlink.xpath('.//w:t')])
                hyperlinks[link_text] = url
            except KeyError:
                continue
    
    return hyperlinks

# this function is only to be used with docx files to preserve layout and hyperlinks
def extract_docx_with_layout_preserved(file_path):
    """
    Extract text content from DOCX while preserving layout and hyperlinks.
    Hyperlinks appear exactly where they are in the document.
    Tables appear in their original positions.
    """
    doc = Document(file_path)
    content_parts = []
    
    # Keep track of table index
    table_index = 0
    
    # Process document elements in their original order
    for element in doc.element.body:
        # Check if element is a paragraph
        if element.tag.endswith('p'):
            # Find the corresponding paragraph object
            for paragraph in doc.paragraphs:
                if paragraph._element == element:
                    if not paragraph.text.strip():
                        # Preserve empty lines for layout
                        content_parts.append("")
                        continue
                    
                    # Get hyperlinks for this paragraph
                    hyperlinks = extract_hyperlinks_from_paragraph(paragraph)
                    
                    # Build paragraph text with hyperlinks
                    para_text = paragraph.text
                    
                    # Replace hyperlink text with text + URL format
                    for link_text, url in hyperlinks.items():
                        if link_text in para_text:
                            para_text = para_text.replace(link_text, f"{link_text} [{url}]")
                    
                    content_parts.append(para_text)
                    break
        
        # Check if element is a table
        elif element.tag.endswith('tbl'):
            content_parts.append(f"\n [TABLE {table_index + 1}]")
            table = doc.tables[table_index]
            
            for row in table.rows:
                row_content = []
                for cell in row.cells:
                    cell_text = ""
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip():
                            # Get hyperlinks for this cell paragraph
                            hyperlinks = extract_hyperlinks_from_paragraph(paragraph)
                            
                            para_text = paragraph.text
                            # Replace hyperlink text with text + URL format
                            for link_text, url in hyperlinks.items():
                                if link_text in para_text:
                                    para_text = para_text.replace(link_text, f"{link_text} [{url}]")
                            
                            cell_text += para_text + " "
                    
                    row_content.append(cell_text.strip())
                
                # Format table row with proper spacing
                content_parts.append(" | ".join(row_content))
            
            content_parts.append("[END TABLE]\n ")
            table_index += 1
    
    return "\n ".join(content_parts)
