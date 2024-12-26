import os
import uuid
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.routing import Route
import sys

UPLOAD_DIR = "uploads"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Middleware for handling sessions (to set cookies)
middleware = [
    Middleware(SessionMiddleware, secret_key="your_secret_key_here")
]

# Create the app
app = Starlette(debug=True, routes=[], middleware=middleware)


# Generate a unique user ID
def get_user_id(request: Request):
    print("Session Data:", request.session)  # Debugging line
    user_id = request.session.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        request.session["user_id"] = user_id
    return user_id

# Route to retrieve user_id
async def get_user_id_api(request: Request):
    user_id = get_user_id(request)
    return JSONResponse({"user_id": user_id})


# Route to save API key to .env file
async def save_api_key(request: Request):
    data = await request.json()

    # Extract API key and user ID from the request body
    api_key = data.get("apiKey")
    user_id = data.get("userId")

    if not api_key or not user_id:
        return JSONResponse({"error": "Invalid data provided"}, status_code=400)

    # Save the API key to a .env file in the server's current directory
    env_file_path = ".env"
    env_line = f"\nGEMINI_API_KEY_FOR_{user_id}={api_key}\n"

    try:
        with open(env_file_path, "a") as env_file:  # Open the file in append mode
            env_file.write(env_line)

        return JSONResponse({"message": "API key saved successfully."})
    except Exception as e:
        return JSONResponse({"error": f"Failed to save API key: {str(e)}"}, status_code=500)

# Home route
async def homepage(request: Request):
    user_id = get_user_id(request)
    html_content = open("templates/home.html").read()
    html_with_user_id = html_content.replace("{{user_id}}", user_id)
    return HTMLResponse(html_with_user_id)


# Route for uploading the syllabus file
async def upload_syllabus(request: Request):
    user_id = get_user_id(request)
    user_dir = os.path.join(UPLOAD_DIR, user_id, "syllabus")
    os.makedirs(user_dir, exist_ok=True)

    form = await request.form()
    syllabus_file = form.get("singleFile")

    if syllabus_file:
        file_path = os.path.join(user_dir, syllabus_file.filename)
        with open(file_path, "wb") as f:
            f.write(await syllabus_file.read())
        return JSONResponse({"message": f"Syllabus file uploaded to {file_path}"})
    else:
        return JSONResponse({"error": "No file provided"}, status_code=400)


# Route for uploading question files
async def upload_questions(request: Request):
    user_id = get_user_id(request)
    user_dir = os.path.join(UPLOAD_DIR, user_id, "questions")
    os.makedirs(user_dir, exist_ok=True)

    form = await request.form()
    question_files = form.getlist("multipleFiles")
    uploaded_files = []

    for question_file in question_files:
        file_path = os.path.join(user_dir, question_file.filename)
        with open(file_path, "wb") as f:
            f.write(await question_file.read())
        uploaded_files.append(file_path)

    return JSONResponse({"message": "Files uploaded successfully", "files": uploaded_files})


# Route to process uploaded files
async def process_files(request: Request, methods=["POST", "GET"]):
    user_id = get_user_id(request)
    syllabus_dir = os.path.join(UPLOAD_DIR, user_id, "syllabus")
    questions_dir = os.path.join(UPLOAD_DIR, user_id, "questions")

    syllabus_files = os.listdir(syllabus_dir) if os.path.exists(syllabus_dir) else []
    question_files = os.listdir(questions_dir) if os.path.exists(questions_dir) else []

    # Call main.py with user ID
    # os.system(f"python main.py {syllabus_dir}/{syllabus_files[0]} {questions_dir} {user_id}")   
    print(f"Running \npython main.py {syllabus_dir}/{syllabus_files[0]} {questions_dir} {user_id}")

    return JSONResponse({
        "user_id": user_id,
        "syllabus_files": syllabus_files,
        "question_files": question_files,
    })

# Define routes
routes = [
    Route("/", homepage),
    Route("/upload/syllabus", upload_syllabus, methods=["POST"]),
    Route("/upload/questions", upload_questions, methods=["POST"]),
    Route("/process", process_files, methods=["POST", "GET"]),
    Route("/save-api-key", save_api_key, methods=["POST"]),
    Route("/get-user-id", get_user_id_api, methods=["GET"]),
]

# Create the app
app = Starlette(debug=True, routes=routes, middleware=middleware)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)