import chainlit as cl
import os
import json
from langchain_core.messages import  HumanMessage
from langchain_core.messages.utils import count_tokens_approximately

from constants import MAX_INPUT_TOKENS,END_TOKEN
from utils import trim_chat_history, run_chain_with_retry, create_llm_chain, send_error_message, extract_variables_from_response, search_media_by_keywords
from utils import get_media_selector_llm_chain
from kyc_util import handle_kyc, send_welcome_message
from vectordb_util import get_pinecone_vector_store
from mongo_util import get_mongo_client

if not os.getenv("GOOGLE_API_KEY"):
    error_msg = "❌ GOOGLE_API_KEY missing"
    print(error_msg)
    raise ValueError(error_msg)

vectordb = get_pinecone_vector_store()
chain = create_llm_chain(vectordb)
media_selector_chain = get_media_selector_llm_chain()
mongo_db = get_mongo_client()

@cl.on_chat_start
async def on_chat_start():
    print("DEBUG: Chat session started")
    print("DEBUG: Sending welcome message...")
    await send_welcome_message()

    cl.user_session.set("kyc", {})
    cl.user_session.set("is_kyc_complete", False)
    print("DEBUG: Initialized user session - KYC: {}, is_kyc_complete: False")

@cl.on_message
async def handle_message(message: cl.Message):

    print(f"DEBUG: ========== NEW MESSAGE ==========")
    print(f"DEBUG: User message: '{message.content}'")
    print(f"DEBUG: Current session state - is_kyc_complete: {cl.user_session.get('is_kyc_complete', False)}")
    print(f"DEBUG: Current KYC data: {cl.user_session.get('kyc', {})}")
    print(f"DEBUG: Chat history when handle_message started: {cl.chat_context.to_openai()}")

    if not cl.user_session.get("is_kyc_complete", False):
        print("DEBUG: KYC not complete, handling KYC process...")
        is_kyc_complete = await handle_kyc(message)
        print(f"DEBUG: KYC handling result: {is_kyc_complete}")

        if is_kyc_complete:
            cl.user_session.set("is_kyc_complete", True)
            print("DEBUG: KYC marked as complete in session")

            kyc = cl.user_session.get("kyc")
            print(f"DEBUG: Final KYC data: {kyc}")
            await cl.Message(content=f"✅ **Excellent, {kyc['name']}!** 🎉\n\nWelcome to **Ask Nour** - Your FUE Knowledge Companion! \n\nYour profile has been successfully set up for the **{kyc.get('faculty', 'your chosen')}** faculty. I'm now ready to assist you with all your Future University in Egypt questions and guide you through the admissions process.\n\n🚀 **Let's explore FUE together!**").send()

            # clear all context history
            print("DEBUG: Clearing chat context after KYC completion")
            cl.chat_context.clear()
            print("DEBUG: Chat context cleared")
        else:
            print("DEBUG: KYC still incomplete, returning without processing question")
        return    

    kyc = cl.user_session.get("kyc")
    user_input = message.content
    print(f"DEBUG: Processing question from user: {kyc.get('name', 'Unknown')}")
    print(f"DEBUG: User input: '{user_input}'")
    print(f"DEBUG: User faculty: {kyc.get('faculty', 'Unknown')}")

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
        
        print(f"DEBUG: Starting chain execution with params - user: {kyc.get('name', 'Unknown')}, faculty: {kyc.get('faculty', "Unknown")}")
        found_end = False
        response_text = ""
        for token in run_chain_with_retry(answer_chain, user_input, kyc.get('name', "Unknown"), kyc.get("faculty", "Unknown"),  trimmed):
            response_text += token

            print(f"DEBUG: Streaming token: {token}")

            if not found_end:
                # Stream the token to the message
                await msg.stream_token(token.split(END_TOKEN)[0])  # Stream only up to the END_TOKEN if it exists

            # Check if [END_RESPONSE] just appeared in the response
            if END_TOKEN in response_text and not found_end:
                found_end = True  # Stop streaming further tokens
            

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

            if len(images) > 3 and len(videos) > 3:
                
                response = media_selector_chain.invoke({
                    "input": user_input,
                    "previous_response": response_text,
                    "videos" : ", ".join([f"{video['video_url']} ({video.get('description', 'No description')})" for video in videos]),
                    "images" : ", ".join([f"{image['image_url']} ({image.get('description', 'No description')})" for image in images])
                })

                response_text = response.content
                print(f"DEBUG: LLM response: {response_text}")
                
                try:
                    print("DEBUG: Attempting to parse LLM response for media extraction")
                    extracted = json.loads(response_text.content)
                    print(f"DEBUG: Extracted data: {extracted}")

                    extracted_image_urls = extracted["images"]
                    extracted_video_urls = extracted["videos"]

                    if not extracted_image_urls or not extracted_video_urls:
                        raise ValueError("No images or videos extracted from response")
                    
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
                    video_url_lower = video_url.lower()
                    if video_url_lower.startswith("facebook:"):
                        video_url_clean = video_url[len("Facebook:"):]
                        elements.append(cl.CustomElement(name="FacebookVideoEmbed", url=video_url_clean, display="inline"))
                    elif video_url_lower.startswith("youtube:"):
                        video_url_clean = video_url[len("YouTube:"):]
                        elements.append(cl.CustomElement(name="YouTubeVideoEmbed", url=video_url_clean, display="inline"))
                    else:
                        print(f"DEBUG: Unknown video URL format: {video_url}, skipping")

            await cl.Message(content=extracted["text"], elements=elements).send()

        
    except Exception as e:
        print(f"DEBUG: Error during chain execution: {str(e)}")
        print(f"DEBUG: Error type: {type(e).__name__}")
        await send_error_message(f"❌ Gemini quota or other error: {str(e)}", message)

    print("DEBUG: Finalizing message...")
    # Finalize the message
    await msg.update()
    print("DEBUG: Message processing complete")
