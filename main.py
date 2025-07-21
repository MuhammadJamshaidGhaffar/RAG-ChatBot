import chainlit as cl
import os

from langchain_core.messages import  HumanMessage
from langchain_core.messages.utils import count_tokens_approximately

from constants import MAX_INPUT_TOKENS
from utils import trim_chat_history, run_chain_with_retry, get_vector_store, create_llm_chain, send_error_message
from kyc_util import handle_kyc, send_welcome_message

if not os.getenv("GOOGLE_API_KEY"):
    error_msg = "❌ GOOGLE_API_KEY missing"
    print(error_msg)
    raise ValueError(error_msg)

vectordb = get_vector_store()
chain = create_llm_chain(vectordb)

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
            await cl.Message(content=f"✅ Great, {kyc['name']}! Weclome. You can now ask questions related to university admissions.").send()

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
        for token in run_chain_with_retry(answer_chain, user_input, kyc.get('name', "Unknown"), kyc.get("faculty", "Unknown"),  trimmed):
            await msg.stream_token(token)
        
    except Exception as e:
        print(f"DEBUG: Error during chain execution: {str(e)}")
        print(f"DEBUG: Error type: {type(e).__name__}")
        await send_error_message(f"❌ Gemini quota or other error: {str(e)}", message)

    print("DEBUG: Finalizing message...")
    # Finalize the message
    await msg.update()
    print("DEBUG: Message processing complete")
