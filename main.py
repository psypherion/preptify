import os
import argparse
import asyncio
import time
from syllabus import SyllabusExtractor
from extractor import QuestionExtractor
from dotenv import dotenv_values

import logging

# Configure logging
logging.basicConfig(
    filename="preptify.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

class PDFProcessor:
    """
    Class to manage syllabus and question extraction from multiple PDF files.
    """

    def __init__(self, syllabus_pdf_path: str, question_pdfs: list, user_id: str, request_limit: int = 5, cooldown: int = 60):
        """
        Initialize the PDFProcessor with paths for syllabus and question PDFs.

        Args:
            syllabus_pdf_path (str): Path to the syllabus PDF.
            question_pdfs (list): List of paths to question PDFs.
            user_id (str): Unique user ID to fetch the corresponding API key.
            request_limit (int): Maximum number of requests allowed per minute.
            cooldown (int): Cooldown time in seconds after hitting the request limit.
        """
        self.syllabus_pdf_path = syllabus_pdf_path
        self.question_pdfs = question_pdfs
        self.user_id = user_id
        self.syllabus_json_path = "syllabus/syllabus.json"
        self.request_limit = request_limit
        self.cooldown = cooldown
        self.api_key = self.get_user_api_key()

    def get_user_api_key(self) -> str:
        """
        Fetch the API key for the specific user from the .env file.

        Returns:
            str: The API key for the user.
        Raises:
            ValueError: If the API key for the user is not found.
        """
        env_config = dotenv_values(".env")  # Load all variables from the .env file
        key_name = f"GEMINI_API_KEY_FOR_{self.user_id}"  # Key format in .env

        if key_name not in env_config:
            raise ValueError(f"API key for user ID {self.user_id} not found in .env file.")
        
        return env_config[key_name]

    def process_syllabus(self):
        """
        Extract and convert syllabus PDF to JSON.
        """
        syllabus_extractor = SyllabusExtractor(pdf_path=self.syllabus_pdf_path)
        syllabus_extractor.process(output_json_path=self.syllabus_json_path)

    async def process_questions(self):
        """
        Process multiple question PDFs using the extracted syllabus.
        Handle request limits by adding cooldowns as necessary.
        """
        request_count = 0

        for question_pdf in self.question_pdfs:
            if request_count >= self.request_limit:
                print(f"Reached request limit ({self.request_limit}). Cooling down for {self.cooldown} seconds...")
                time.sleep(self.cooldown)
                request_count = 0

            print(f"Processing questions from: {question_pdf}")
            extractor = QuestionExtractor(pdf_path=question_pdf, syllabus_path=self.syllabus_json_path, api_key=self.api_key)
            await extractor.run()
            request_count += 1

    def run(self):
        """
        Run the entire PDF processing pipeline.
        """
        self.process_syllabus()
        asyncio.run(self.process_questions())


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process syllabus and question PDFs.")
    parser.add_argument("syllabus_path", type=str, help="Path to the syllabus PDF")
    parser.add_argument("questions_path", type=str, help="Path to the directory containing question PDFs")
    parser.add_argument("user_id", type=str, help="Unique user ID to fetch API key")

    args = parser.parse_args()

    # Get the syllabus and question paths from arguments
    syllabus_path = args.syllabus_path
    questions_path = args.questions_path
    user_id = args.user_id

    # List all question PDFs in the provided directory
    question_pdfs = [os.path.join(questions_path, pdf) for pdf in os.listdir(questions_path) if pdf.endswith(".pdf")]

    try:
        processor = PDFProcessor(syllabus_path, question_pdfs, user_id)
        processor.run()
    except Exception as e:
        print(f"Error: {e}")
