import os
import asyncio
import time
from syllabus import SyllabusExtractor
from extractor import QuestionExtractor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")


class PDFProcessor:
    """
    Class to manage syllabus and question extraction from multiple PDF files.
    """

    def __init__(self, syllabus_pdf_path: str, question_pdfs: list, request_limit: int = 5, cooldown: int = 60):
        """
        Initialize the PDFProcessor with paths for syllabus and question PDFs.

        Args:
            syllabus_pdf_path (str): Path to the syllabus PDF.
            question_pdfs (list): List of paths to question PDFs.
            request_limit (int): Maximum number of requests allowed per minute.
            cooldown (int): Cooldown time in seconds after hitting the request limit.
        """
        self.syllabus_pdf_path = syllabus_pdf_path
        self.question_pdfs = question_pdfs
        self.syllabus_json_path = "syllabus.json"
        self.request_limit = request_limit
        self.cooldown = cooldown

    def process_syllabus(self):
        """
        Extract and convert syllabus PDF to JSON.
        """
        print("Processing syllabus...")
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
            extractor = QuestionExtractor(pdf_path=question_pdf, syllabus_path=self.syllabus_json_path, api_key=GEMINI_API_KEY)
            await extractor.run()
            request_count += 1

    def run(self):
        """
        Run the entire PDF processing pipeline.
        """
        self.process_syllabus()
        asyncio.run(self.process_questions())

if __name__ == "__main__":
    # Paths to the syllabus and question PDFs
    syllabus_pdf_path = "syllabus/syllabus.pdf"
    question_pdfs = [f"pdfs/{pdf}" for pdf in os.listdir("pdfs")]

    try:
        processor = PDFProcessor(syllabus_pdf_path, question_pdfs)
        processor.run()
    except Exception as e:
        print(f"Error: {e}")
