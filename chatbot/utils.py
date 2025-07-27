from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted
from langchain_core.messages import AIMessage, HumanMessage, trim_messages
from langchain_core.messages.utils import count_tokens_approximately
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain
)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import chainlit as cl
from chainlit.message import Message
from typing import List, Tuple, Dict
import re
import sys
from pathlib import Path

# Add MongoDB support
try:
    from pymongo import MongoClient
    from dotenv import load_dotenv
    load_dotenv()
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️ MongoDB dependencies not available - falling back to environment variables")


from constants import FAISS_PATH, MAX_HISTORY_TOKENS, END_TOKEN, CHUNK_OVERLAP, CHUNK_SIZE, RETRIEVER_K, MAX_OUTPUT_TOKENS, IMAGES_COLLECTION, VIDEOS_COLLECTION, CONFIG_COLLECTION

# Global cache for LLM instances to avoid recreating them on every request
_cached_api_key = None
_cached_llm_chain = None
_cached_media_llm_chain = None
_cached_vector_store = None

def get_gemini_api_key_from_mongo():
    """
    Get Gemini API key from MongoDB configuration.
    Falls back to environment variable if MongoDB is not available.
    
    Returns:
        str: Gemini API key or None if not found
    """
    if not MONGODB_AVAILABLE:
        print("DEBUG: MongoDB not available, using environment variable")
        return os.getenv("GOOGLE_API_KEY")
    
    try:
        # Get MongoDB connection settings from environment
        mongodb_uri = os.getenv("MONGODB_URI")
        mongo_db_name = os.getenv("MONGO_DB_NAME")
        
        if not mongodb_uri or not mongo_db_name:
            print("DEBUG: MongoDB settings not configured, using environment variable")
            return os.getenv("GOOGLE_API_KEY")
        
        # Connect to MongoDB
        client = MongoClient(mongodb_uri)
        db = client[mongo_db_name]
        config_collection = db[CONFIG_COLLECTION]
        
        # Get Gemini API key from config collection
        api_key_doc = config_collection.find_one({"key": "gemini_api_key"})
        
        if api_key_doc and api_key_doc.get("value"):
            api_key = api_key_doc["value"].strip()
            if api_key:
                print("DEBUG: Successfully retrieved Gemini API key from MongoDB")
                return api_key
        
        print("DEBUG: Gemini API key not found in MongoDB, using environment variable")
        return os.getenv("GOOGLE_API_KEY")
        
    except Exception as e:
        print(f"DEBUG: Error getting Gemini API key from MongoDB: {str(e)}")
        print("DEBUG: Falling back to environment variable")
        return os.getenv("GOOGLE_API_KEY")


def clear_llm_cache():
    """Clear cached LLM instances to force refresh with new API key."""
    global _cached_api_key, _cached_llm_chain, _cached_media_llm_chain, _cached_vector_store
    print("DEBUG: Clearing LLM cache to refresh API key")
    _cached_api_key = None
    _cached_llm_chain = None
    _cached_media_llm_chain = None
    _cached_vector_store = None


def get_cached_llm_chain():
    """Get cached LLM chain or create new one if API key changed."""
    global _cached_api_key, _cached_llm_chain, _cached_vector_store
    
    current_api_key = get_gemini_api_key_from_mongo()
    
    # If API key changed or no cached instance, recreate
    if _cached_api_key != current_api_key or _cached_llm_chain is None:
        print("DEBUG: API key changed or no cached LLM, creating fresh instance")
        _cached_api_key = current_api_key
        
        # Import here to avoid circular imports
        from vectordb_util import get_pinecone_vector_store
        
        try:
            _cached_vector_store = get_pinecone_vector_store()
            _cached_llm_chain = create_llm_chain(_cached_vector_store)
            print("DEBUG: Successfully created cached LLM chain with Pinecone")
        except Exception as e:
            print(f"ERROR: Failed to create LLM chain: {e}")
            _cached_llm_chain = None
    
    return _cached_llm_chain


def get_cached_media_llm_chain():
    """Get cached media LLM chain or create new one if API key changed."""
    global _cached_api_key, _cached_media_llm_chain
    
    current_api_key = get_gemini_api_key_from_mongo()
    
    # If API key changed or no cached instance, recreate
    if _cached_api_key != current_api_key or _cached_media_llm_chain is None:
        print("DEBUG: API key changed or no cached media LLM, creating fresh instance")
        _cached_api_key = current_api_key
        _cached_media_llm_chain = get_media_selector_llm_chain()
    
    return _cached_media_llm_chain

def trim_chat_history(raw_history: list[dict]):
    print(f"DEBUG: Starting trim_chat_history with {len(raw_history)} messages")
    print(f"DEBUG: Raw history: {raw_history}")
    
    # Convert to LangChain Message objects
    msgs = []
    for i, m in enumerate(raw_history):
        print(f"DEBUG: Processing message {i}: role={m.get('role')}, content_length={len(m.get('content', ''))}")
        RoleCls = None
        if m["role"] == "user":
            RoleCls = HumanMessage
        elif m["role"] == "assistant":
            RoleCls = AIMessage
        # RoleCls = HumanMessage if m["role"] == "user" elif  AIMessage

        if RoleCls is not None:
            msgs.append(RoleCls(m["content"]))
            print(f"DEBUG: Added {RoleCls.__name__} message")
        else:
            print(f"DEBUG: Skipped message with unknown role: {m.get('role')}")

    print(f"DEBUG: Converted {len(msgs)} messages to LangChain format")
    print(f"DEBUG: Starting trim_messages with max_tokens={MAX_HISTORY_TOKENS}")
    
    trimmed = trim_messages(
        msgs,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=MAX_HISTORY_TOKENS,
        start_on="human",
        end_on=("ai"),
        include_system=False,
        allow_partial=False
    )
    
    print(f"DEBUG: Trimmed to {len(trimmed)} messages")
    print(f"DEBUG: Trimmed messages: {[f'{type(msg).__name__}: {msg.content[:100]}...' for msg in trimmed]}")
    return trimmed


def get_faiss_vector_store():
    print("DEBUG: Starting get_vector_store()")
    vectordb = None

    # Get API key from MongoDB or environment
    api_key = get_gemini_api_key_from_mongo()
    if not api_key:
        raise ValueError("❌ Gemini API key not found in MongoDB or environment variables. Please configure it in the dashboard.")
    
    embed = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=api_key)
    print("DEBUG: Created GoogleGenerativeAIEmbeddings with model: gemini-embedding-001")

    if os.path.exists(FAISS_PATH):
        print(f"DEBUG: FAISS index exists at {FAISS_PATH}, loading...")
        # 🔄 Load existing index
        vectordb = FAISS.load_local(FAISS_PATH, embed, allow_dangerous_deserialization=True)
        print(f"DEBUG: Successfully loaded FAISS index with {vectordb.index.ntotal} vectors")
    else:
        print(f"DEBUG: FAISS index not found at {FAISS_PATH}, creating new one...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,   # characters
            chunk_overlap=CHUNK_OVERLAP
        )
        print(f"DEBUG: Created text splitter - chunk_size: {CHUNK_SIZE}, overlap: {CHUNK_OVERLAP}")
        
        # Create with one dummy doc (INIT_TEXT)
        init_doc = text_splitter.create_documents(["INIT_TEXT"], metadatas=[{"source": "init"}])
        print(f"DEBUG: Created {len(init_doc)} initial documents")
        vectordb = FAISS.from_documents(init_doc, embed)
        vectordb.save_local(FAISS_PATH)
        print(f"DEBUG: ✅ Initialized FAISS with intro doc and saved to {FAISS_PATH}")

    print(f"DEBUG: Returning vectordb with {vectordb.index.ntotal} total vectors")
    return vectordb

def create_llm_chain(vectordb):
    print("DEBUG: Starting create_llm_chain()")
    
    # Check if vectordb is available
    if vectordb is None:
        raise ValueError("❌ Vector database not available. Please check Pinecone and API key configuration.")
    
    # Get API key from MongoDB or environment
    api_key = get_gemini_api_key_from_mongo()
    if not api_key:
        raise ValueError("❌ Gemini API key not found in MongoDB or environment variables. Please configure it in the dashboard.")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", max_output_tokens=MAX_OUTPUT_TOKENS, google_api_key=api_key)
    print(f"DEBUG: Created LLM - model: gemini-2.5-flash, temp: 0, max_tokens: {MAX_OUTPUT_TOKENS}")

    # 1️⃣ setup history-aware retriever
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question, "
        "which might reference context in the chat history, "
        "formulate a standalone question that can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is. "
        "Detect the language of the user’s question (English, Arabic, or Franco-Arabic, which is Arabic text mixed with Latin characters or French words). "
        "Preserve the detected language in the reformulated question. "
        "For Franco-Arabic, treat it as Arabic and reformulate in standard Arabic. "
        # "The name of the user is {user_name}, and their selected faculty is {faculty}. "
        "The user's selected faculty is {faculty};"
        "Use this information to personalize and clarify the question if relevant."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    print(f"DEBUG: Created contextualize_q_prompt with retriever_k={RETRIEVER_K}")
    history_retriever = create_history_aware_retriever(llm, vectordb.as_retriever(k=RETRIEVER_K), contextualize_q_prompt)
    print("DEBUG: Created history-aware retriever")

    # 2️⃣ setup document combiner
    system_prompt = (
        "You are Ask Nour, a friendly admission assistant at Future University in Egypt for question-answering tasks. "
        "Use the following pieces of retrieved context to answer questions comprehensively and professionally. "
        "Detect the language of the user’s question (English, Arabic, or Franco-Arabic, which is Arabic text mixed with Latin characters or French words) and respond in the same language. "
        "For Franco-Arabic inputs, respond in standard Arabic. "
        "If you don't know the answer, say that you don't know. "
        "The user's name is {user_name} and their selected faculty is {faculty}; personalize the response if helpful. "

        "**FORMATTING REQUIREMENTS:**\n"
        "- Provide comprehensive, detailed answers with proper structure\n"
        "- Use paragraphs to organize different aspects of your response\n"
        "- Use bullet points (•) for listing items, requirements, or key points\n"
        "- Use **bold text** for important information and headings\n"
        "- Include specific details, numbers, and examples when available\n"
        "- Maintain a professional yet friendly tone\n"
        "- For Arabic responses, ensure proper formatting and readability\n"

        "**RESPONSE STRUCTURE:**\n"
        "1. Start with a welcoming acknowledgment\n"
        "2. Provide the main information in well-organized paragraphs\n"
        "3. Use bullet points for detailed lists or requirements\n"
        "4. End with helpful next steps or additional assistance offer\n"

        "Output the response in plain text with the following structure:\n"
        "- The answer text, followed by the end_token [END_RESPONSE].\n"
        "- After [END_RESPONSE], include metadata in the format:\n"
        "  include_media=(true/false),keywords=(keyword1,keyword2,...)\n"

        "- Set include_media=true **only if**:\n"
        "  • the user explicitly requests media (e.g., asks for videos, photos, pictures, etc.), OR\n"
        "  • you believe media would enhance the response (e.g., when the user asks about a department, facilities, labs, faculty members, etc.).\n"

        "- Include keywords (e.g., Pharmacy,labs,صيدلة) **only if include_media=true**.\n"
        "- Do **not** include keywords if include_media=false.\n"

        "- **IMPORTANT**: When include_media=true, respond as if you will show the media. Use phrases like 'Let me show you...', 'Here are some...', 'I'll display...', etc. Do NOT say you cannot show media.\n"
        "- When include_media=false, provide a complete answer without mentioning media capabilities.\n"

        "- Do **not** mention flags, internal variables, or implementation details in your response.\n"
        "- Remain conversational and helpful without revealing how you work behind the scenes.\n"

        "{context}\n"
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    combine_chain = create_stuff_documents_chain(llm, qa_prompt)
    print("DEBUG: Created document combine chain")

    # 3️⃣ final retriever chain
    chain = create_retrieval_chain(history_retriever, combine_chain)
    print("DEBUG: Created final retrieval chain")

    return chain


@retry(
    retry=retry_if_exception_type(ResourceExhausted),
    wait=wait_random_exponential(multiplier=2, max=70),
    stop=stop_after_attempt(5),
    reraise=True,
    before_sleep=lambda retry_state: print(f"⚠️ Quota hit in chat. Retrying... attempt #{retry_state.attempt_number}")
)
def run_chain_with_retry(chain, user_input, user_name, faculty, chat_history):
    print("Running chain with retry...")
    print("User Input:", user_input)
    print("Chat History:", chat_history)
    
    try:
        result = chain.stream({
            "input": user_input,
            "user_name": user_name,
            "faculty": faculty,
            "chat_history": chat_history
        })
        print("DEBUG: Chain stream started successfully")
        return result
    except Exception as e:
        print(f"ERROR: Failed to start chain stream: {e}")
        # Return empty generator if chain fails completely
        def empty_generator():
            yield "I apologize, but I'm experiencing technical difficulties. Please try again."
        return empty_generator()


async def send_error_message(error_msg: str, user_message : "Message", ):
    """Send an error message to the user and clean up the chat context."""
    print(f"DEBUG: Sending error message: '{error_msg}'")
    print(f"DEBUG: User message to remove: '{user_message.content if user_message else 'None'}'")

    # Show error message to user
    msg =  cl.Message(content=error_msg)
    await msg.send()

    if cl.chat_context.remove(user_message):
        print("Removed user input from chat context")
    if cl.chat_context.remove(msg):
        print("Removed error message from chat context")


def extract_variables_from_response(response_text:str) -> Tuple[bool, List[str]]:
    meta_match = re.search(r"\[END_RESPONSE\]\s*include_media=(true|false),keywords=\((.*?)\)", response_text, re.DOTALL)
    
    if meta_match:
        include_media = meta_match.group(1) == "true"
        keywords_raw = meta_match.group(2).strip()
        keywords = [kw.strip() for kw in keywords_raw.split(",") if kw.strip()]
    else:
        include_media = False
        keywords = []

    return include_media, keywords

def search_media_by_keywords(keywords: List[str], db) -> Tuple[List[Dict], List[Dict]]:
    """
    Search MongoDB images and videos collections for documents matching the given keywords in their description.
    
    Args:
        keywords (List[str]): List of keywords to search for (e.g., ["Pharmacy", "labs", "صيدلة"]).
        db : MongoDB database.
        images_collection (str): Name of the images collection.
        videos_collection (str): Name of the videos collection.
    
    Returns:
        Tuple[List[Dict], List[Dict]]: Two lists containing matching documents from images and videos collections.
        Each document has 'image_url'/'video_url' and 'description' fields.
    """

    images_coll = db[IMAGES_COLLECTION]
    videos_coll = db[VIDEOS_COLLECTION]
    
    # Build regex query for keywords (case-insensitive)
    regex_pattern = "|".join(keywords)
    query = {"description": {"$regex": regex_pattern, "$options": "i"}}
    
    # Search images collection
    image_matches = list(images_coll.find(query))
    
    # Search videos collection
    video_matches = list(videos_coll.find(query))
    
    return image_matches, video_matches


def get_media_selector_llm_chain():
    print("DEBUG: Starting get_media_selector_llm_chain()")

    # Get API key from MongoDB or environment
    api_key = get_gemini_api_key_from_mongo()
    if not api_key:
        raise ValueError("❌ Gemini API key not found in MongoDB or environment variables. Please configure it in the dashboard.")

    llm_media = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        max_output_tokens=MAX_OUTPUT_TOKENS,
        response_mime_type="application/json",
        google_api_key=api_key
    )

    print(f"DEBUG: Created media selector LLM - model: gemini-2.5-flash, max_tokens: {MAX_OUTPUT_TOKENS}")

    system_prompt = (
        "You are a media selection assistant. "
        "Your task is to choose the most relevant media (images and videos) based on the user's question "
        "and the previous Gemini response. You are provided with candidate media below. "
        "Select up to 3 images and 3 videos unless the user explicitly asks for more. "
        "Preserve the original video format exactly as provided (e.g., 'Facebook:<url>' or 'YouTube:<url>').\n\n"

        "Available videos (format: Facebook:<url> or YouTube:<url>):\n"
        "{videos}\n\n"

        "Available images:\n"
        "{images}\n\n"

        "For the 'text' field, write a natural, user-friendly description of the media content. "
        "Do NOT mention selection process, keywords, relevance, or internal details. "
        "Write as if you're naturally describing what the user will see. "
        "Examples: 'Here's our modern computer lab where students work on programming projects.' "
        "or 'Take a virtual tour of our engineering facilities and laboratories.'\n\n"

        "Return your answer in the following strict JSON format:\n"
        "{{\n"
        '  "images": ["<image_url_1>", "<image_url_2>", "..."],\n'
        '  "videos": ["Facebook:<url>", "YouTube:<url>", "..."],\n'
        '  "text": "A natural description of what the user will see in the media."\n'
        "}}\n\n"
        "Do not include any extra commentary, markdown, or text outside the JSON object."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("ai", "{previous_response}")
    ])

    chain = prompt | llm_media
    return chain


def detect_arabic_text(text: str) -> bool:
    """
    Detect if text contains Arabic characters.
    Returns True if Arabic characters are found.
    """
    import re
    # Arabic Unicode range: U+0600-U+06FF (basic Arabic), U+0750-U+077F (Arabic Supplement)
    # U+FB50-U+FDFF (Arabic Presentation Forms-A), U+FE70-U+FEFF (Arabic Presentation Forms-B)
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]')
    return bool(arabic_pattern.search(text))


def format_message_with_rtl(content: str) -> str:
    """
    Format message content with RTL support for Arabic text.
    Wraps Arabic content in RTL div tags.
    """
    if not content:
        return content
    
    # Check if the message contains Arabic text
    if detect_arabic_text(content):
        # Split content by lines to handle mixed content
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if detect_arabic_text(line):
                # Wrap Arabic lines with RTL direction
                formatted_lines.append(f'<div dir="rtl" class="ar-text">{line}</div>')
            else:
                # Keep non-Arabic lines as LTR
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    return content
