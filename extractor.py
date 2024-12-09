import asyncio
import json
import os
import re
from typing import List

import PIL.Image
from absl import logging
from dotenv import load_dotenv
import google.generativeai as genai

from pdfslicer import PDFToImageConverter

# Load environment variables
load_dotenv()

# Configure logging
logging.set_verbosity(logging.ERROR)

# Constants
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
MODEL_NAME: str = "gemini-exp-1206"
SYLLABUS_PATH: str = "syllabus.txt"  # Path to the syllabus text file

# Base prompt
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

PDF_PATH: str = r"pdfs/paper_2_X.pdf"


class QuestionExtractor:
    def __init__(
        self,
        model_name: str = MODEL_NAME,
        api_key: str = GEMINI_API_KEY,
        syllabus_path: str = SYLLABUS_PATH,
        pdf_path: str = PDF_PATH,
    ):
        """Initialize the QuestionExtractor."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name)
        self.pdf_path = pdf_path
        self.syllabus_content = self.load_syllabus(syllabus_path)

    @staticmethod
    def load_syllabus(syllabus_path: str) -> str:
        """Load the syllabus content from a text file."""
        if not os.path.exists(syllabus_path):
            raise FileNotFoundError(f"Syllabus file not found: {syllabus_path}")
        with open(syllabus_path, "r", encoding="utf-8") as file:
            return file.read()

    async def pdf_to_images(self) -> str:
        """Convert the PDF to images and save them."""
        pdf_slicer = PDFToImageConverter(pdf_path=self.pdf_path)
        image_streams = await pdf_slicer.convert_pdf_to_images()
        image_dir = await pdf_slicer.save_images(image_streams)
        return image_dir

    async def process_image(self, image_path: str, response_file: str) -> None:
        """Process a single image and append the response to a file."""
        image = PIL.Image.open(image_path)
        prompt = BASE_PROMPT.replace("<syllabus_content>", self.syllabus_content)
        request_payload = [prompt, image]
        response = self.model.generate_content(request_payload)

        # Extract the text from the response
        if response.candidates and response.candidates[0].finish_reason != 4:  # Not reciting copyrighted material
            extracted_text = response.text
        else:
            extracted_text = '{"questions": []}'  # Default response if no valid content

        # Append the response to the text file
        with open(response_file, "a") as file:
            file.write(f"{extracted_text}\n")

    @staticmethod
    def extract_json_from_responses(response_file: str) -> List[dict]:
        """Extract JSON data from the response file using regex."""
        with open(response_file, "r") as file:
            content = file.read()

        # Regex to match JSON blocks
        pattern = r"```json\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)

        return [json.loads(match) for match in matches]

    @staticmethod
    async def save_json(json_data: List[dict], file_name: str) -> None:
        """Save the extracted JSON data to a file."""
        with open(file_name, "w") as json_file:
            json.dump(json_data, json_file, indent=4)

    async def run(self) -> str:
        """Run the entire question extraction process."""
        # Get the base name of the PDF file (without extension)
        base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]

        image_dir = await self.pdf_to_images()
        response_file = f"{base_name}_responses.txt"  # Use PDF base name for the response file

        # Clear or create the response file
        with open(response_file, "w") as file:
            file.write("")

        # Process images one by one
        for img_path in os.listdir(image_dir):
            full_img_path = os.path.join(image_dir, img_path)
            await self.process_image(full_img_path, response_file)

        # Extract JSON data from responses
        extracted_data = self.extract_json_from_responses(response_file)

        # Save the combined JSON data with the same name as the PDF (output.json)
        await self.save_json(extracted_data, f"{base_name}_output.json")
        return "Question extraction and categorization completed!"


if __name__ == "__main__":
    extractor = QuestionExtractor()
    asyncio.run(extractor.run())
