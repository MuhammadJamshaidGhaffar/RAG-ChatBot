import chainlit as cl
import os
import json
import asyncio
from langchain_core.messages import  HumanMessage
from langchain_core.messages.utils import count_tokens_approximately

from constants import MAX_INPUT_TOKENS,END_TOKEN
from utils import trim_chat_history, run_chain_with_retry, create_llm_chain, send_error_message, extract_variables_from_response, search_media_by_keywords
from utils import get_media_selector_llm_chain, get_cached_llm_chain, get_cached_media_llm_chain, get_gemini_api_key_from_mongo
from kyc_util import handle_kyc, send_welcome_message, save_user_data_to_collection
from vectordb_util import get_pinecone_vector_store
from mongo_util import get_mongo_client
from storage_util import get_storage_config, save_interaction_data

# Check if Gemini API key is available from MongoDB or environment
api_key = get_gemini_api_key_from_mongo()
if not api_key:
    error_msg = "❌ Gemini API key not found in MongoDB or environment variables. Please configure it in the dashboard."
    print(error_msg)
    # Don't raise error here - let it be handled gracefully when chains are used

# Initialize components with error handling
try:
    vectordb = get_pinecone_vector_store()
    print("✅ Vector database initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize vector database: {e}")
    vectordb = None

mongo_db = get_mongo_client()


@cl.on_chat_start
async def on_chat_start():
    print("DEBUG: Chat session started")
    
    # UNCOMMENT THIS LINE TO TEST STREAMING IN PRODUCTION:
    # await test_streaming_debug()
    
    print("DEBUG: Sending welcome message...")
    await send_welcome_message()

    cl.user_session.set("kyc", {})
    cl.user_session.set("is_kyc_complete", False)
    
    # Get storage configuration once at session start
    storage_mode = get_storage_config()
    cl.user_session.set("storage_mode", storage_mode)
    print(f"DEBUG: Initialized user session - KYC: {{}}, is_kyc_complete: False, storage_mode: {storage_mode}")

@cl.on_message
async def handle_message(message: cl.Message):

    print(f"DEBUG: ========== NEW MESSAGE ==========")
    print(f"DEBUG: User message: '{message.content}'")
    print(f"DEBUG: Current session state - is_kyc_complete: {cl.user_session.get('is_kyc_complete', False)}")
    print(f"DEBUG: Current KYC data: {cl.user_session.get('kyc', {})}")
    print(f"DEBUG: Chat history when handle_message started: {cl.chat_context.to_openai()}")

    # Check if user wants to apply or if KYC is in progress
    kyc_result = await handle_kyc(message)
    print(f"DEBUG: KYC handling result: {kyc_result}")
    
    # If kyc_result is None, it means no application intent and no active KYC - proceed with normal chat
    # If kyc_result is False, it means KYC is in progress but not complete - return
    # If kyc_result is True, it means KYC is complete - continue with normal chat
    
    if kyc_result is None:
        print("DEBUG: No KYC interaction, proceeding with normal chat")
        # Normal chat flow - no KYC interaction
    elif kyc_result is False:
        print("DEBUG: KYC in progress but not complete, returning")
        return  # KYC is in progress but not complete
    elif kyc_result is True:
        print("DEBUG: KYC completed, proceeding with normal chat after completion")
        cl.user_session.set("is_kyc_complete", True)
        
        kyc = cl.user_session.get("kyc")
        print(f"DEBUG: Final KYC data: {kyc}")
        
        # Save user data to USERS_COLLECTION
        print("DEBUG: Saving user data to USERS_COLLECTION...")
        save_success = save_user_data_to_collection(kyc)
        if save_success:
            print("DEBUG: User data saved successfully")
        else:
            print("DEBUG: Failed to save user data")

        return  # Don't process the message that completed KYC as a regular question

    # Normal chat processing for all users (KYC complete or no KYC needed)
    kyc = cl.user_session.get("kyc", {})
    user_input = message.content
    user_name = kyc.get('name', 'Unknown') if kyc else 'Unknown'
    user_faculty = kyc.get('faculty', 'Unknown') if kyc else 'Unknown'
    
    print(f"DEBUG: Processing question from user: {user_name}")
    print(f"DEBUG: User input: '{user_input}'")
    print(f"DEBUG: User faculty: {user_faculty}")

    # Check if input exceeds token limit
    token_count = count_tokens_approximately([HumanMessage(user_input)])
    print(f"DEBUG: Input token count: {token_count}, Max allowed: {MAX_INPUT_TOKENS}")
    if token_count > MAX_INPUT_TOKENS:
        error = f"❌ Input too long! Please limit to {MAX_INPUT_TOKENS} tokens."
        print(f"DEBUG: Input too long, sending error message")
        await send_error_message(error, message)
        return

    print("DEBUG: Creating spinner message...")
    # Create a spinner
    msg = cl.Message(content="")
    await msg.send()

    
    # Get the cached LLM chain
    chain = get_cached_llm_chain()
    if not chain:
        await send_error_message("❌ Unable to initialize LLM chain. Please check API key configuration.", message)
        return
        
    answer_chain = chain.pick("answer")
    try:
        history = cl.chat_context.to_openai()
        print(f"DEBUG: Full chat history length: {len(history)} messages")
        history = history[:-2]  # Exclude the last two message (the current user input and emoty AI response which was sent just above)
        print(f"DEBUG: Chat history before trimming: {len(history)} messages")
        print(f"DEBUG: Chat history content: {history}")
        
        trimmed = trim_chat_history(history)
        print(f"DEBUG: Trimmed chat history: {len(trimmed)} messages")
        print(f"DEBUG: Trimmed history content: {trimmed}")
        
        print(f"DEBUG: Starting chain execution with params - user: {user_name}, faculty: {user_faculty}")
        found_end = False
        response_text = ""
        for token in run_chain_with_retry(answer_chain, user_input, user_name, user_faculty, trimmed):
            response_text += token

            print(f"DEBUG: Streaming token: {token}")

            if not found_end:
                # Check if END_TOKEN appears in the accumulated response_text
                if END_TOKEN in response_text:
                    # Find where END_TOKEN starts in the accumulated text
                    end_token_index = response_text.find(END_TOKEN)
                    
                    # Calculate how much text we should have streamed up to END_TOKEN
                    text_before_end = response_text[:end_token_index]
                    
                    # Calculate how much we've already streamed (length before this token)
                    already_streamed_length = len(response_text) - len(token)
                    
                    # Calculate how much of the current token to stream
                    remaining_to_stream = len(text_before_end) - already_streamed_length
                    
                    if remaining_to_stream > 0:
                        # Stream only the part before END_TOKEN
                        token_to_stream = token[:remaining_to_stream]
                        await msg.stream_token(token_to_stream)
                        # Force flush with visible delay for streaming effect
                        import asyncio
                        await asyncio.sleep(0.1)  # Increased from 0.01 to 0.05
                    
                    found_end = True  # Stop streaming further tokens
                else:
                    # No END_TOKEN found yet, stream the entire token
                    await msg.stream_token(token)
                    # Force flush with visible delay for streaming effect
                    import asyncio
                    await asyncio.sleep(0.1)  # Increased from 0.01 to 0.05
            

        # extract two variables
        include_media, keywords = extract_variables_from_response(response_text)

        print(f"DEBUG: include_media={include_media}, keywords={keywords}")

        if include_media:
            print(f"DEBUG: Searching media with keywords: {keywords}")
            images, videos = search_media_by_keywords(keywords, mongo_db, )
            print(f"DEBUG: Found {len(images)} images and {len(videos)} videos")

            # a default response of LLM
            extracted = {
                    "images": [],
                    "videos": [],
                    "text": "Here are some relevant media"
                }
            extracted_image_urls = []
            extracted_video_urls = []
        

            if len(images) > 3 or len(videos) > 3:
                
                media_selector_chain = get_cached_media_llm_chain()
                if not media_selector_chain:
                    await send_error_message("❌ Unable to initialize media selector chain. Please check API key configuration.", message)
                    return
                    
                response = media_selector_chain.invoke({
                    "input": user_input,
                    "previous_response": response_text,
                    "videos" : ", ".join([f"{video['video_url']} ({video.get('description', 'No description')})" for video in videos]),
                    "images" : ", ".join([f"{image['image_url']} ({image.get('description', 'No description')})" for image in images])
                })

                response_text_2 = response.content
                print(f"DEBUG: LLM response: {response_text_2}")
                
                try:
                    print("DEBUG: Attempting to parse LLM response for media extraction")
                    extracted = json.loads(response_text_2)
                    print(f"DEBUG: Extracted data: {extracted}")

                    extracted_image_urls = extracted["images"]
                    extracted_video_urls = extracted["videos"]
                    
                except Exception as error:
                    print(f"DEBUG: Error parsing LLM response: {error}")
            else:
                extracted_image_urls = [image["image_url"] for image in images]
                extracted_video_urls = [video["video_url"] for video in videos]


            elements = []
            if extracted_image_urls:
                print(f"DEBUG: Showing {len(extracted_image_urls)} images")
                # elements = [cl.Image(url=image_url, name=f"image_{i}", display="inline") for i, image_url in enumerate(extracted_image_urls)]
                for i, image_url in enumerate(extracted_image_urls):
                    print(f"DEBUG: Processing image URL {i} : {image_url}")
                    elements.append(cl.Image(url=image_url, name=f"image_{i}", display="inline"))

            if extracted_video_urls:
                print(f"DEBUG: Showing {len(videos)} videos")

                # extracted urls are in form of ["Facebook:<url>", "YouTube:<url>", ...]
                for i, video_url in enumerate(extracted_video_urls):
                    print(f"DEBUG: Processing video URL {i}: {video_url}")
                    video_url_lower = video_url.lower().strip()
                    if video_url_lower.startswith("facebook:"):
                        print(f"DEBUG: Detected Facebook video URL: {video_url}")
                        video_url_clean = video_url[len("Facebook:"):]
                        elements.append(cl.CustomElement(name="FacebookVideoEmbed", props={"url": video_url_clean}, display="inline"))
                    elif video_url_lower.startswith("youtube:"):
                        print(f"DEBUG: Detected YouTube video URL: {video_url}")
                        video_url_clean = video_url[len("YouTube:"):]
                        elements.append(cl.CustomElement(name="YouTubeVideoEmbed", props={"url": video_url_clean}, display="inline"))
                    else:
                        print(f"DEBUG: Unknown video URL format: {video_url}, skipping")

            
            if len(extracted_image_urls) > 0 or len(extracted_video_urls) > 0:
                print(f"DEBUG: Sending message with media elements")
                await cl.Message(content=extracted["text"], elements=elements).send()

        # Save interaction data based on config (retrieved once at session start)
        storage_mode = cl.user_session.get("storage_mode")
        save_interaction_data(user_input, response_text.split(END_TOKEN)[0], storage_mode)

        
    except Exception as e:
        print(f"DEBUG: Error during chain execution: {str(e)}")
        print(f"DEBUG: Error type: {type(e).__name__}")
        await send_error_message(f"❌ Gemini quota or other error: {str(e)}", message)

    print("DEBUG: Finalizing message...")
    # Finalize the message
    await msg.update()
    print("DEBUG: Message processing complete")
