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
                                      
If the user mentions an partial or slightly incorrect faculty name, infer the most likely valid one.
If faculty is too ambiguous or not present, return faculty as null.                                      
                                      
Return only a JSON object. If a field is missing, use null. Do not guess.

Example format:
{{"name": "...", "email": "...", "mobile": "...", "faculty": "..."}}

User message:
{message}
""")

kyc_chain = prompt | llm

async def send_welcome_message():
    cl.user_session.set("kyc", {})
    faculty_list = "\n- " + "\n- ".join(FACULTIES)
    welcome = f"""
🎓 **Welcome to Ask Nour - Your FUE Knowledge Companion!**

I'm here to assist you with all your **Future University in Egypt (FUE)** inquiries. Before we begin exploring the exciting opportunities at FUE, please provide the following details:

**📝 Required Information:**
- ✅ **Full Name**
- ✉️ **Email Address** 
- 📱 **Mobile Number**
- 🏛️ **Faculty of Interest**

**� Available FUE Faculties:**{faculty_list}

You can enter all details at once or provide them one by one. Let's get started on your FUE journey! 🚀
"""
    await cl.Message(content=welcome).send()



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

    # Track issues
    guidance_msgs = []

    if "email" in kyc and not is_valid_email(kyc["email"]):
        print(f"DEBUG: Invalid email detected: '{kyc['email']}'")
        guidance_msgs.append(f"📧 The email '{kyc['email']}' is invalid. Please enter a valid email (e.g., example@domain.com).")
        kyc.pop("email")

    if "mobile" in kyc and not is_valid_mobile(kyc["mobile"]):
        print(f"DEBUG: Invalid mobile detected: '{kyc['mobile']}'")
        guidance_msgs.append(f"📱 The mobile number '{kyc['mobile']}' seems invalid. Please include country code and use 10–15 digits.")
        kyc.pop("mobile")

    if "faculty" in kyc and not is_valid_faculty(kyc["faculty"]):
        print(f"DEBUG: Invalid faculty detected: '{kyc['faculty']}'")
        faculty_list = ", ".join(FACULTIES)
        guidance_msgs.append(f"🏫 The faculty '{kyc['faculty']}' is not recognized. Valid options are: {faculty_list}.")
        kyc.pop("faculty")

    print(f"DEBUG: Validation errors found: {len(guidance_msgs)}")
    print(f"DEBUG: Guidance messages: {guidance_msgs}")
    cl.user_session.set("kyc", kyc)

    # Check if KYC is complete
    required_fields = ["name", "email", "mobile", "faculty"]
    missing = [f for f in required_fields if f not in kyc]
    
    print(f"DEBUG: Required fields: {required_fields}")
    print(f"DEBUG: Missing fields: {missing}")
    print(f"DEBUG: Final KYC state: {kyc}")
    print(f"DEBUG: Has guidance messages: {len(guidance_msgs) > 0}")

    if not missing and not guidance_msgs:
        print(f"DEBUG: KYC is complete! User: {kyc['name']}")
        # await cl.Message(
        #     content=f"✅ Great, {kyc['name']}! Your KYC is complete. You can now ask questions related to university admissions."
        # ).send()

        return True
    else:
        msg_parts = []
        if missing:
            msg_parts.append("🔍 You're still missing the following info: " + ", ".join(missing))
        if guidance_msgs:
            msg_parts.extend(guidance_msgs)

        final_message = "\n\n".join(msg_parts)
        print(f"DEBUG: Sending incomplete KYC message: {final_message}")
        await cl.Message(content=final_message).send()

    return False