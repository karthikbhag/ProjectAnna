import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# --- 1. File Path Management & Data Loading ---

def load_json_data_from_data_folder(filename):
    """
    Constructs the path from the Chatbot directory (where this script is)
    to the Data directory and loads the specified JSON file.
    """
    # Path(__file__).resolve().parent gives the directory of the executing file (e.g., /Chatbot)
    current_script_dir = Path(__file__).resolve().parent
    
    # Go UP one directory (..) and then DOWN into 'Data'
    data_path = current_script_dir.parent / 'Data' / filename
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            print(f"Successfully loaded data from: {data_path.name}")
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Could not find file. Check path: {data_path}")
        return None
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {data_path.name}")
        return None

# --- 2. API Client and Data Setup ---

# Load environment variables from the .env file in the current directory (Chatbot/.env)
load_dotenv() 

try:
    # Client automatically uses the GEMINI_API_KEY environment variable.
    client = genai.Client()
    print("Gemini Client Initialized Successfully!")
except Exception as e:
    print(f"FATAL ERROR: Could not initialize Gemini client. Check GEMINI_API_KEY. Error: {e}")
    exit()

# Load both JSON data sources
posts_data = load_json_data_from_data_folder('tmobile_posts.json')
reviews_data = load_json_data_from_data_folder('tmobile_reviews.json')

if not posts_data or not reviews_data:
    print("FATAL ERROR: Missing or invalid data files. Exiting.")
    exit()

# Consolidate Data into a single, readable context string
context_posts = json.dumps(posts_data, indent=2, ensure_ascii=False)
context_reviews = json.dumps(reviews_data, indent=2, ensure_ascii=False)

FULL_DATA_CONTEXT = (
    "You are a T-Mobile Data Analyst Bot. You must answer questions ONLY using the JSON data provided below. "
    "If the answer is not in the data, state that you cannot find the information.\n\n"
    "--- T-Mobile Posts Data (Announcements/Marketing) ---\n"
    f"{context_posts}\n\n"
    "--- T-Mobile Customer Reviews Data (Feedback/Sentiment) ---\n"
    f"{context_reviews}"
)

# --- 3. Chatbot Logic ---

def run_chatbot():
    """Initializes the chat session and runs the conversation loop."""
    
    # Start a chat session and inject the context as system instructions.
    chat_session = client.chats.create(
        model='gemini-2.5-flash',
        config={"system_instruction": FULL_DATA_CONTEXT}
    )
    
    print("-" * 50)
    print("Chatbot Ready! Ask a question about the T-Mobile posts or reviews.")
    print("Type 'quit' or 'exit' to end the session.")
    print("-" * 50)

    # Main conversation loop
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['quit', 'exit']:
            print("Session ended. Goodbye!")
            break
        
        if not user_input.strip():
            continue
            
        try:
            # Send the user's message. The chat session handles history and context automatically.
            response = chat_session.send_message(user_input)
            
            # Display the streamed response (simulated streaming for brevity)
            print(f"\nGemini: {response.text}\n")
            
        except Exception as e:
            print(f"An error occurred during the API call: {e}")
            break

if __name__ == "__main__":
    run_chatbot()