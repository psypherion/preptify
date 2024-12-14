import os
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re
import logging

# Configure logging
logging.basicConfig(
    filename="preptify.log",
    level=logging.INFO,  # Set logging level to INFO (or DEBUG for more detailed logs)
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# Constants
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
MODEL_NAME: str = "gemini-1.5-flash"
SYLLABUS_PATH: str = "syllabus.txt"  # Path to the syllabus text file
PDF_PATH: str = r"syllabus/syllabus.pdf"

class SyllabusExtractor:
    """
    Class to extract text from a syllabus PDF file and convert it into structured JSON using the Gemini API.
    """

    def __init__(self, pdf_path: str = PDF_PATH, api_key_env: str = GEMINI_API_KEY, model_name: str = MODEL_NAME):
        """
        Initialize the SyllabusExtractor.

        Args:
            pdf_path (str): Path to the PDF file.
            api_key_env (str): Environment variable for the API key.
            model_name (str): Gemini API model name.
        """
        self.pdf_path = pdf_path
        self.api_key = api_key_env
        self.model_name = model_name

        if not self.api_key:
            logger.error("API key not found. Ensure the GEMINI_API_KEY is set in the environment.")
            raise ValueError("API key not found. Ensure the GEMINI_API_KEY is set in the environment.")

        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name=self.model_name)

    @staticmethod
    def extract_text_from_pdf(pdf_path: str, output_txt_path: str = None) -> str:
        """
        Extracts text from a PDF file.

        Args:
            pdf_path (str): Path to the PDF file.
            output_txt_path (str): Optional path to save the extracted text as a .txt file.

        Returns:
            str: Extracted text from the PDF.
        """
        if not os.path.exists(pdf_path):
            logger.error(f"The file '{pdf_path}' does not exist.")
            raise FileNotFoundError(f"The file '{pdf_path}' does not exist.")

        reader = PdfReader(pdf_path)
        extracted_text = ""
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            extracted_text += f"\n--- Page {page_number} ---\n{text}"

        if output_txt_path:
            with open(output_txt_path, "w", encoding="utf-8") as output_file:
                output_file.write(extracted_text)

        logger.info(f"Text extracted successfully from {pdf_path}")
        return extracted_text

    def jsonify_syllabus(self, syllabus_text: str) -> dict:
        """
        Converts the syllabus text into a structured JSON object using the Gemini API.

        Args:
            syllabus_text (str): The text content of the syllabus.

        Returns:
            dict: A dictionary representing the JSON object.
        """
        prompt = f"""
        The following text contains a syllabus for a subject. Please analyze and structure the content into a clean and hierarchical JSON format for better usability.

        The JSON structure should adhere to the following format:
        {{
          "units": [
            {{
              "unit_no": <int>,
              "unit_name": "<str>",
              "topics": [
                {{
                  "topic_name": "<str>",
                  "sub_topics": ["<str>", "<str>", ...]
                }},
                ...
              ]
            }},
            ...
          ]
        }}

        Key Requirements:
        1. Extract all units, topics, and sub-topics.
        2. Remove unnecessary formatting artifacts like page numbers or headers.
        3. Ensure valid JSON output.

        Here is the syllabus content:
        {syllabus_text}
        Provide the output in valid JSON format without additional comments.
        """

        response = self.model.generate_content([prompt])
        pattern = r"\s*```json\n(.*?)\n```"
        matches = re.findall(pattern, response.text, re.DOTALL)

        if response.candidates:
            try:
                logger.info("JSON response generated successfully.")
                return [json.loads(match) for match in matches]
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from the API response.")
                raise ValueError("Failed to parse JSON from the API response.")
        else:
            logger.error("No valid response from Gemini API.")
            raise ValueError("No valid response from Gemini API.")


    def process(self, output_txt_path: str = "syllabus/syllabus.txt", output_json_path: str = "syllabus/syllabus.json") -> None:
        """
        Extract syllabus text from a PDF, convert it to JSON, and save the output.

        Args:
            output_txt_path (str): Path to save the extracted text as a .txt file.
            output_json_path (str): Path to save the structured JSON.
        """
        try:
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_txt_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"Created directory: {output_dir}")

            logger.info(f"Starting processing for {self.pdf_path}")
            syllabus_text = self.extract_text_from_pdf(self.pdf_path, output_txt_path)
            logger.info(f"Text extracted to {output_txt_path}")

            syllabus_json = self.jsonify_syllabus(syllabus_text)

            # Ensure the JSON output directory exists
            json_output_dir = os.path.dirname(output_json_path)
            if json_output_dir and not os.path.exists(json_output_dir):
                os.makedirs(json_output_dir)
                logger.info(f"Created directory: {json_output_dir}")

            with open(output_json_path, "w", encoding="utf-8") as json_file:
                json.dump(syllabus_json, json_file, indent=4)

            logger.info(f"Syllabus JSON saved to {output_json_path}")
        except Exception as e:
            logger.error(f"Error in processing: {e}")
            raise


if __name__ == "__main__":
    syllabus_path = input("Enter the path to the syllabus PDF file: ").strip()

    try:
        extractor = SyllabusExtractor(pdf_path=syllabus_path)
        print("Processing syllabus...")
        extractor.process()
        print("Syllabus processing complete.")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        print(f"Error: {e}")
