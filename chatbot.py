from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.routing import Route
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import os


# Replace with your Gemini API key and model name
GEMINI_API_KEY = "AIzaSyCaCE6OsDkyv5jWP46XvCOvNkvZP7KdgIs"
MODEL_NAME = "learnlm-1.5-pro-experimental"
DATABASE_FILE = "db/questions_db.csv"

# Initialize Gemini API and model
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=MODEL_NAME)

# Load the CSV file into a DataFrame
def load_database(database_file: str) -> pd.DataFrame:
    try:
        return pd.read_csv(database_file)
    except Exception as e:
        print(f"Error loading database: {e}")
        return pd.DataFrame()

database = load_database(DATABASE_FILE)

# Generate a response for a given topic
def generate_response(questions: pd.DataFrame) -> str:
    if questions.empty:
        return "No questions available for the selected unit or topic."

    # Prepare prompt for the Gemini model
    questions_text = "\n".join(
        f"Q{row['question_no']}: {row['question']}" for _, row in questions.iterrows()
    )
    prompt = (
        f"The following are questions related to the topic '{questions['topic'].iloc[0]}':\n\n"
        f"{questions_text}\n\n"
        "Provide detailed answers to each question, including the correct option, explanation, and any additional information."
        "Clarify the answers, and offer additional information to help the user understand the topic better."
    )

    try:
        response = model.generate_content(prompt)
        return response.text if response.candidates else "No valid response from the model."
    except Exception as e:
        return f"Error generating teaching plan: {e}"

# Store context for each topic
topic_context = {}

# Endpoint to handle topic-specific questions and host the chatbot
async def topic_chat(request):
    topic = request.path_params['topic']
    questions = database[database['topic'].str.lower() == topic.lower()]
    
    if questions.empty:
        return JSONResponse({"error": f"No questions found for topic '{topic}'"}, status_code=404)
    
    # Generate context for the topic using the Gemini API
    context = generate_response(questions)
    topic_context[topic] = context  # Save the context for the topic
    
    # Serve the chatbot HTML, passing the topic-specific context
    with open("templates/chatbot.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(html_content)

# Endpoint for chatbot conversation
async def chatbot(request):
    data = await request.json()
    user_message = data.get("message", "")
    topic = data.get("topic", "")  # Include topic in the request
    
    if not user_message or not topic:
        return JSONResponse({"response": "Please provide both a message and a topic."}, status_code=400)
    
    # Retrieve context for the specific topic
    context = topic_context.get(topic, "")
    
    # Prepare the prompt using the topic-specific context and user message
    prompt = (
        f"The user is asking a question related to the topic '{topic}':\n\n"
        f"Context:\n{context}\n\n"
        f"User's question:\n{user_message}\n\n"
        "Provide a detailed, clear, and concise answer to the user's question."
    )
    try:
        response = model.generate_content(prompt)
        bot_response = response.text if response.candidates else "No valid response from the model."
        return JSONResponse({"response": bot_response})
    except Exception as e:
        return JSONResponse({"response": f"Error: {e}"}, status_code=500)

# Endpoint to serve the chatbot HTML
async def serve_chatbot_page(request):
    with open("templates/chatbot.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(html_content)

# Starlette application setup
routes = [
    Route("/", endpoint=serve_chatbot_page),  # Serve the chatbot HTML at the root endpoint
    Route("/topics/{topic}/chat", endpoint=topic_chat, methods=["GET"]),
    Route("/api/chat", endpoint=chatbot, methods=["POST"]),
]

app = Starlette(routes=routes)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware to allow the chatbot frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing; restrict this in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
# Start the Starlette application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)