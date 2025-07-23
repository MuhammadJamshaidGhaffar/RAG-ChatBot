import chainlit as cl
import re
import json
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

FACULTIES = [
    "oral and dental",
    "pharmacy",
    "commerce and business administration",
    "engineering",
    "computer science",
    "economics and political science"
]

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_valid_mobile(mobile):
    return re.match(r"^\+?\d{10,15}$", mobile) is not None

def is_valid_faculty(faculty):
    return faculty.lower() in [f.lower() for f in FACULTIES]


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", response_mime_type="application/json"
)

prompt = PromptTemplate.from_template("""
You are an admission assistant for a university. From the user message below, extract these fields:
- name
- email
- mobile
- faculty of interest

Valid faculties are:
{faculties}

If the user mentions a partial or slightly incorrect faculty name, infer the most likely valid one.
If faculty is too ambiguous or not present, return faculty as null.

Return only a JSON object with the extracted data. If a field is missing, use null. Do not guess.

Example format:
{{
  "name": "...", 
  "email": "...", 
  "mobile": "...", 
  "faculty": "..."
}}

User message:
{message}
""")

kyc_chain = prompt | llm

# LLM chain for generating dynamic validation and completion messages
message_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", response_mime_type="application/json"
)

message_prompt = PromptTemplate.from_template("""
You are an admission assistant for Future University in Egypt (FUE). Generate appropriate response messages based on the KYC validation results.

Detect the language of the user's previous message (English, Arabic, or Franco-Arabic, which is Arabic text mixed with Latin characters or French words) and respond in the same language.
For Franco-Arabic inputs, respond in standard Arabic.

Current KYC state: {kyc_state}
Missing fields: {missing_fields}
Validation errors: {validation_errors}
User's previous message: {user_message}

Available faculties: {faculties}

Generate a JSON response with appropriate message text:

If KYC is complete (no missing fields, no errors):
{{
  "message_type": "completion",
  "text": "Welcome message confirming completion and readiness to help with university questions"
}}

If there are missing fields or validation errors:
{{
  "message_type": "guidance", 
  "text": "Helpful message guiding user to provide missing/correct information"
}}

Make the messages friendly, professional, and specific to the issues found. Use emojis appropriately.
""")

message_chain = message_prompt | message_llm

async def send_welcome_message():
    cl.user_session.set("kyc", {})
    faculty_list = "\n- " + "\n- ".join(FACULTIES)
    
    # Create welcome message with logo
    welcome = f"""
🎓 **Welcome to Ask Nour - Your FUE Knowledge Companion!**

I'm here to assist you with all your **Future University in Egypt (FUE)** inquiries. Before we begin exploring the exciting opportunities at FUE, please provide the following details:

**📝 Required Information:**
- ✅ **Full Name**
- ✉️ **Email Address** 
- 📱 **Mobile Number**
- 🏛️ **Faculty of Interest**

**🎯 Available FUE Faculties:**{faculty_list}

You can enter all details at once or provide them one by one. Let's get started on your FUE journey! 🚀
"""
    
    # Create image element for the logo
    logo_image = cl.Image(path="./public/fue-red-logo.jpg", name="FUE Logo", display="inline")
    
    # Send logo
    # await cl.Message(content="",elements=[logo_image]).send()

    # send Message
    await cl.Message(
        content=welcome,
        elements=[logo_image]
    ).send()



async def handle_kyc(message: cl.Message):
    kyc = cl.user_session.get("kyc") or {}
    print(f"DEBUG: Current KYC state: {kyc}")
    print(f"DEBUG: User message: {message.content}")

    # Extract fields using Gemini
    response = kyc_chain.invoke({"message": message.content, "faculties": FACULTIES})
    print(f"DEBUG: LLM response: {response.content}")
    
    try:
        extracted = json.loads(response.content)
        print(f"DEBUG: Extracted data: {extracted}")
            
    except Exception as error:
        print(f"DEBUG: Error parsing LLM response: {error}")
        await cl.Message(content="⚠️ Sorry, I couldn't understand your message. Please try again.").send()
        return

    # Update non-null values
    for key in ["name", "email", "mobile", "faculty"]:
        if extracted.get(key):
            old_value = kyc.get(key)
            kyc[key] = extracted[key].strip()
            print(f"DEBUG: Updated {key}: '{old_value}' -> '{kyc[key]}'")

    print(f"DEBUG: KYC after update: {kyc}")

    # Track validation issues
    validation_errors = []

    if "email" in kyc and not is_valid_email(kyc["email"]):
        print(f"DEBUG: Invalid email detected: '{kyc['email']}'")
        validation_errors.append(f"Invalid email: {kyc['email']}")
        kyc.pop("email")

    if "mobile" in kyc and not is_valid_mobile(kyc["mobile"]):
        print(f"DEBUG: Invalid mobile detected: '{kyc['mobile']}'")
        validation_errors.append(f"Invalid mobile: {kyc['mobile']}")
        kyc.pop("mobile")

    if "faculty" in kyc and not is_valid_faculty(kyc["faculty"]):
        print(f"DEBUG: Invalid faculty detected: '{kyc['faculty']}'")
        validation_errors.append(f"Invalid faculty: {kyc['faculty']}")
        kyc.pop("faculty")

    print(f"DEBUG: Validation errors found: {len(validation_errors)}")
    cl.user_session.set("kyc", kyc)

    # Check if KYC is complete
    required_fields = ["name", "email", "mobile", "faculty"]
    missing = [f for f in required_fields if f not in kyc]
    
    print(f"DEBUG: Required fields: {required_fields}")
    print(f"DEBUG: Missing fields: {missing}")
    print(f"DEBUG: Final KYC state: {kyc}")

    # Generate dynamic response message
    try:
        message_response = message_chain.invoke({
            "kyc_state": str(kyc),
            "missing_fields": missing,
            "validation_errors": validation_errors,
            "user_message": message.content,
            "faculties": FACULTIES
        })
        
        message_data = json.loads(message_response.content)
        print(f"DEBUG: Generated message: {message_data}")
        
        # Send the dynamic message
        if message_data.get("text"):
            await cl.Message(content=message_data["text"]).send()
            
        # Return completion status
        return message_data.get("message_type") == "completion"
        
    except Exception as error:
        print(f"DEBUG: Error generating dynamic message: {error}")
        # Fallback to simple status message
        if not missing and not validation_errors:
            await cl.Message(
                content=f"✅ Great, {kyc.get('name', 'there')}! Your information is complete. You can now ask questions about university admissions."
            ).send()
            return True
        else:
            fallback_msg = "Please provide any missing information to continue."
            if missing:
                fallback_msg = f"Missing: {', '.join(missing)}. " + fallback_msg
            await cl.Message(content=fallback_msg).send()
            return False
