import pandas as pd
import json
from typing import List, Dict
import os

import logging
# Configure logging
logging.basicConfig(
    filename="preptify.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


class JSONToDataFrameConverter:
    """
    A class to convert JSON data containing questions into a pandas DataFrame.
    """

    def __init__(self, json_file_paths: List[str]):
        """
        Initialize the converter with a list of JSON file paths.

        Args:
            json_file_paths (List[str]): List of paths to JSON files containing questions.
        """
        self.json_file_paths = json_file_paths
        self.data_frame = None

    @staticmethod
    def load_json(file_path: str) -> List[Dict]:
        """
        Load JSON data from the specified file.

        Args:
            file_path (str): Path to the JSON file.

        Returns:
            List[Dict]: Parsed JSON data.
        """
        if not file_path:
            raise ValueError("JSON file path cannot be empty.")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

    @staticmethod
    def json_to_dataframe(json_data: List[Dict]) -> pd.DataFrame:
        """
        Convert JSON data into a pandas DataFrame.

        Args:
            json_data (List[Dict]): The JSON data containing questions.

        Returns:
            pd.DataFrame: A DataFrame representing the questions.
        """
        rows = []

        for question_set in json_data:
            for question in question_set.get("questions", []):
                rows.append({
                    "question_no": question.get("question_no"),
                    "question": question.get("question"),
                    "option_a": question.get("options", {}).get("a"),
                    "option_b": question.get("options", {}).get("b"),
                    "option_c": question.get("options", {}).get("c"),
                    "option_d": question.get("options", {}).get("d"),
                    "answer": question.get("answer"),
                    "explanation": question.get("explanation"),
                    "unit": question.get("category", {}).get("unit"),
                    "topic": question.get("category", {}).get("topic"),
                })

        return pd.DataFrame(rows)

    def convert_multiple_and_save(self, output_csv_path: str):
        """
        Load JSON data from multiple files, convert to a DataFrame, and save it to a CSV file.

        Args:
            output_csv_path (str): Path to save the resulting CSV file.
        """
        all_data = []

        for file_path in self.json_file_paths:
            try:
                json_data = self.load_json(file_path)
                all_data.extend(json_data)
            except Exception as e:
                print(f"Error processing file '{file_path}': {e}")

        self.data_frame = self.json_to_dataframe(all_data)

        if self.data_frame.empty:
            print("Warning: No data was converted into the DataFrame.")
        else:
            self.data_frame.to_csv(output_csv_path, index=False)
            print(f"DataFrame successfully saved to '{output_csv_path}'")

    def display_dataframe(self, num_rows: int = 10):
        """
        Display the first few rows of the DataFrame.

        Args:
            num_rows (int): Number of rows to display.
        """
        if self.data_frame is None:
            print("DataFrame is empty. Load and convert data first.")
        else:
            print(self.data_frame.head(num_rows))

if __name__ == "__main__":
    # Example usage
    json_paths = os.listdir("db/json/")
    json_paths = [f"db/json/{path}" for path in json_paths]
    if "db" not in os.listdir():
        os.mkdir("db")

    output_csv_path = "db/questions_db.csv"  # Path to save the combined CSV

    converter = JSONToDataFrameConverter(json_paths)

    try:
        converter.convert_multiple_and_save(output_csv_path)
        converter.display_dataframe()
    except Exception as e:
        print(f"Error: {e}")
