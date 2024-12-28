import asyncio
import json
import os
import re
import logging
from typing import List

import PIL.Image
from dotenv import load_dotenv
import google.generativeai as genai

from pdfslicer import PDFToImageConverter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="preptify.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# Constants
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
OCR_MODELS: List[str] = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-exp-1114",
    "gemini-1.5-pro-exp-0827",
    "gemini-1.5-pro-exp-0801",
    "gemini-1.5-flash-8b-exp-0924",
    "gemini-1.5-flash-8b-exp-0827",
    "gemini-exp-1206",
    "gemini-exp-1121",
]
SYLLABUS_PATH: str = "syllabus/syllabus.txt"
BASE_PROMPT: str = """
Please extract all MCQ questions and their options from the image provided. 
Ensure you include answers and explanations for each question where possible.

Also, categorize each question under the appropriate topic and sub-topic based on the provided syllabus.

The syllabus is as follows:
<syllabus_content>

The expected JSON output format is:
{
  "questions": [
    {
      "question_no": <int>,
      "question": "<str>",
      "options": {
        "a": "<str>",
        "b": "<str>",
        "c": "<str>",
        "d": "<str>"
      },
      "answer": "<str>",
      "explanation": "<str>",
      "category": {
        "unit": "<unit_name>",
        "topic": "<topic_name>"
      }
    }
  ]
}

Key Points:
- Include all questions present in the image.
- Ensure each question has four options (a, b, c, d).
- Provide the answer and explanation for each question.
- Categorize each question into its corresponding unit and topic based on the syllabus.
- If no questions are present in the image, return {"questions": []}.
- Deliver the output in valid JSON format.
"""

class QuestionExtractor:
    def __init__(
        self,
        pdf_path: str,
        user_id: str,
        syllabus_path: str = SYLLABUS_PATH,
        ocr_models: List[str] = OCR_MODELS,
        api_key: str = GEMINI_API_KEY
    ):
        self.pdf_path = pdf_path
        self.user_id = user_id
        self.ocr_models = ocr_models
        self.syllabus_content = self.load_syllabus(syllabus_path)
        self.current_model_index = 0

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the environment.")

        genai.configure(api_key=GEMINI_API_KEY)
        self.model = self._initialize_model()

        # Set up user-specific directories
        self.base_dir = os.path.join("db", self.user_id)
        self.image_dir = os.path.join(self.base_dir, "images")
        self.json_dir = os.path.join(self.base_dir, "json")
        self.response_dir = os.path.join(self.base_dir, "response")
        self.question_db_path = os.path.join(self.base_dir, "question_db.csv")

        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.response_dir, exist_ok=True)

    def _initialize_model(self):
        model_name = self.ocr_models[self.current_model_index]
        logger.info(f"Using model: {model_name}")
        return genai.GenerativeModel(model_name=model_name)

    def switch_model(self):
        self.current_model_index += 1
        if self.current_model_index >= len(self.ocr_models):
            raise RuntimeError("All OCR models have been exhausted.")
        self.model = self._initialize_model()

    @staticmethod
    def load_syllabus(syllabus_path: str) -> str:
        if not os.path.exists(syllabus_path):
            raise FileNotFoundError(f"Syllabus file not found: {syllabus_path}")
        with open(syllabus_path, "r", encoding="utf-8") as file:
            return file.read()

    async def pdf_to_images(self) -> str:
        pdf_slicer = PDFToImageConverter(pdf_path=self.pdf_path)
        image_streams = await pdf_slicer.convert_pdf_to_images()
        image_dir = await pdf_slicer.save_images(image_streams, output_dir=self.image_dir)
        return image_dir

    async def process_image(self, image_path: str, response_file: str) -> None:
        print(f"Processing image: {image_path}")
        image = PIL.Image.open(image_path)
        prompt = BASE_PROMPT.replace("<syllabus_content>", self.syllabus_content)
        request_payload = [prompt, image]

        print(f"Using model: {self.model.model_name}")

        try:
            response = self.model.generate_content(request_payload)

            print(f"Generating response for image: {image_path}")
            if response.candidates and response.candidates[0].finish_reason != 4:
                extracted_text = response.text
                print(f"Response generated for image: {image_path}")
            else:
                extracted_text = '{"questions": []}'
                print(f"No response generated for image: {image_path}")

            with open(response_file, "a") as file:
                file.write(f"{extracted_text}\n")
            print(f"Response saved to file: {response_file}")
            logger.info(f"Response saved to file: {response_file}")
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            self.switch_model()
            await self.process_image(image_path, response_file)

    @staticmethod
    def extract_json_from_responses(response_file: str) -> List[dict]:
        with open(response_file, "r") as file:
            content = file.read()
        pattern = r"```json\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)
        return [json.loads(match) for match in matches]

    @staticmethod
    async def save_json(json_data: List[dict], file_name: str) -> None:
        with open(file_name, "w") as json_file:
            json.dump(json_data, json_file, indent=4)

    async def run(self) -> str:
        base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        image_dir = await self.pdf_to_images()

        response_file = os.path.join(self.response_dir, f"{base_name}_responses.txt")

        with open(response_file, "w") as file:
            file.write("")

        for img_path in os.listdir(image_dir):
            full_img_path = os.path.join(image_dir, img_path)
            await self.process_image(full_img_path, response_file)

        extracted_data = self.extract_json_from_responses(response_file)

        output_json_path = os.path.join(self.json_dir, f"{base_name}_output.json")
        await self.save_json(extracted_data, output_json_path)

        return f"Question extraction and categorization completed! Output saved to {output_json_path}"

if __name__ == "__main__":
    try:
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        pdf_path = input("Enter the path to the PDF file: ").strip()
        user_id = input("Enter the user ID: ").strip()

        extractor = QuestionExtractor(pdf_path=pdf_path, user_id=user_id)
        asyncio.run(extractor.run())
    except Exception as e:
        logger.error(f"Critical error: {e}")
