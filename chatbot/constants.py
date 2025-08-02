# constants.py

# Text splitting - Optimized for admission assistance content
CHUNK_SIZE = 1500  # Increased for better context retention in educational content
CHUNK_OVERLAP = 200  # Increased overlap to maintain context across chunks

# Retriever - Increased for comprehensive admission information
RETRIEVER_K = 5  # Retrieve more chunks for thorough admission answers

MAX_HISTORY_TOKENS = 2000  # Increased to maintain longer conversation context
MAX_INPUT_TOKENS = 750  # Increased to allow longer questions
MAX_OUTPUT_TOKENS = 1500  # Increased for comprehensive responses


END_TOKEN = "[END_RESPONSE]"


USERS_COLLECTION = "user_details"
ADMIN_USERS_COLLECTION_NAME = "admin_users"
IMAGES_COLLECTION = "images"
VIDEOS_COLLECTION = "videos"
CONFIG_COLLECTION = "config"

CHAT_HISTORY_COLLECTION = "chat_history"
QUESTIONS_COLLECTION = "questions"

# REGISTER_BUTTON_URL = "https://services.fue.edu.eg/applyonline2025/"
REGISTER_BUTTON_URL = "https://bit.ly/fue_asknour"


