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


from constants import FAISS_PATH, MAX_HISTORY_TOKENS, END_TOKEN, CHUNK_OVERLAP, CHUNK_SIZE, RETRIEVER_K, MAX_OUTPUT_TOKENS, IMAGES_COLLECTION, VIDEOS_COLLECTION

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

    embed = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
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
        init_doc = text_splitter.create_documents([INIT_TEXT], metadatas=[{"source": "init"}])
        print(f"DEBUG: Created {len(init_doc)} initial documents")
        vectordb = FAISS.from_documents(init_doc, embed)
        vectordb.save_local(FAISS_PATH)
        print(f"DEBUG: ✅ Initialized FAISS with intro doc and saved to {FAISS_PATH}")

    print(f"DEBUG: Returning vectordb with {vectordb.index.ntotal} total vectors")
    return vectordb

def create_llm_chain(vectordb):
    print("DEBUG: Starting create_llm_chain()")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", max_output_tokens=MAX_OUTPUT_TOKENS)
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
        "You are an Ask Nour, a friendly admission assistant at Future University in Egypt for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question concisely in three sentences maximum. "
        "Detect the language of the user’s question (English, Arabic, or Franco-Arabic, which is Arabic text mixed with Latin characters or French words) and respond in the same language. "
        "For Franco-Arabic inputs, respond in standard Arabic. "
        "If you don't know the answer, say that you don't know. "
        "The user's name is {user_name} and their selected faculty is {faculty}; personalize the response if helpful."
        "Output the response in plain text with the following structure:"
        f"- The answer text, followed by the end_token . {END_TOKEN}"
        f"- After {END_TOKEN}, include metadata in the format: include_media=(true/false),keywords=(keyword1,keyword2,...)"
        "- Set include_media=true if the user explicitly requests media, or if you believe that including media would enhance the user's experience or help answer the query more effectively."
        "- Include keywords (e.g., Pharmacy,labs,صيدلة) only if include_media=true."
        "- Do not include keywords if include_media=false."
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
    return chain.stream({
        "input": user_input,
        "user_name": user_name,
        "faculty": faculty,
        "chat_history": chat_history
    })


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

    llm_media = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        max_output_tokens=MAX_OUTPUT_TOKENS,
        response_mime_type="application/json"
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

        "Return your answer in the following strict JSON format:\n"
        "{\n"
        '  "images": ["<image_url_1>", "<image_url_2>", "..."],\n'
        '  "videos": ["Facebook:<url>", "YouTube:<url>", "..."],\n'
        '  "text": "A brief explanation of the selected media."\n'
        "}\n\n"
        "Do not include any extra commentary, markdown, or text outside the JSON object."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("ai", "{previous_response}")
    ])

    chain = prompt | llm_media
    return chain
