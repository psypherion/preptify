import httpx
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
from starlette.responses import FileResponse, HTMLResponse
from starlette.routing import Route
from starlette.requests import Request
import os
from starlette.staticfiles import StaticFiles
import shutil

UPLOAD_DIR = "uploads"
ALLOWED_CSV_FILES = ["questions_db.csv"]

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


async def serve_csv(request: Request):
    user_id = request.path_params.get("user_id")
    csv_file_path = os.path.join("db", user_id, ALLOWED_CSV_FILES[0])
    
    # Check if the CSV file exists
    if not os.path.exists(csv_file_path):
        return JSONResponse({"error": f"CSV file not found for user {user_id}"}, status_code=404)
    
    return FileResponse(csv_file_path, filename="questions_db.csv", media_type="text/csv")


# # Route to serve the CSV file for a given user_id
# async def serve_csv(request: Request):
#     user_id = request.path_params.get("user_id")
#     csv_file_path = os.path.abspath(f"db/{user_id}/questions_db.csv")
    
#     # Check if the CSV file exists
#     if not os.path.exists(csv_file_path):
#         return JSONResponse({"error": f"CSV file not found for user {user_id}"}, status_code=404)
    
#     return JSONResponse({"Fetched CSV file": csv_file_path})

async def serve_chart(request: Request):
    user_id = request.path_params.get("user_id")
    try:
        async with httpx.AsyncClient() as client:
            base_url: str = str(request.base_url)
            print(f"Base URL: {base_url}")
            csv_url = f"{base_url}users/{user_id}/data/" # URL of the hosted CSV
            print(f"CSV URL: {csv_url}")
            response = await client.get(csv_url)
            print(f"Response: {response}")
            response.raise_for_status()  # Raise an exception for bad status codes
            print(f"Response: {response.text}")
            # Process CSV data
            csv_data: List[Dict[str, str]] = []
            reader = csv.DictReader(response.text.splitlines())
            for row in reader:
                csv_data.append(row)
            
            return JSONResponse({"data": csv_data})
    except httpx.HTTPError as e:
        return JSONResponse({"error": f"Error fetching CSV: {e}"}, status_code=500)
    except csv.Error as e:
        return JSONResponse({"error": f"Error parsing CSV: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": f"An unexpected error occurred: {e}"}, status_code=500)

# # Route to serve the charts.html and inject the CSV path from the /{user_id}/data/ endpoint
# async def serve_chart(request: Request):
#     user_id = request.path_params.get("user_id")
#     csv_file_path = f"db/{user_id}/questions_db.csv"
#     # Define the path for the chart template
#     chart_template_path = os.path.join("templates", "charts.html")
    
#     # Check if the charts.html template exists
#     if not os.path.exists(chart_template_path):
#         return JSONResponse({"error": "Chart template not found"}, status_code=404)
    
#     try:
#         # Read the charts.html template
#         with open(chart_template_path, "r") as file:
#             html_content = file.read()
        
#         # Inject the endpoint for CSV file dynamically into the HTML
#         # Using the new /{user_id}/data/ endpoint to serve CSV data
#         csv_data_endpoint = f"/{user_id}/data/"
#         html_content = html_content.replace("{{csv_file_path}}", csv_data_endpoint)
        
#         return templates.TemplateResponse('charts.html', {"request": request, "csv_file_path": csv_file_path})
    
#     except Exception as e:
#         return JSONResponse({"error": f"An error occurred while loading the chart: {str(e)}"}, status_code=500)



# Define routes
routes = [
    Route("/", homepage),
    Route("/upload/syllabus", upload_syllabus, methods=["POST"]),
    Route("/upload/questions", upload_questions, methods=["POST"]),
    Route("/process", process_files, methods=["POST", "GET"]),
    Route("/save-api-key", save_api_key, methods=["POST"]),
    Route("/get-user-id", get_user_id_api, methods=["GET"]),
    Route("/users/{user_id}/chart", endpoint=serve_chart),
    Route("/users/{user_id}/data", serve_csv), 
]

# Create the app
app = Starlette(debug=True, routes=routes, middleware=middleware)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
