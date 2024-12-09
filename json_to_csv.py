import pandas as pd
import json
from typing import List, Dict

def load_json(file_path: str) -> List[Dict]:
    """
    Load JSON data from a file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        List[Dict]: Parsed JSON data.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

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

def main():
    # Path to your JSON file
    json_file = "paper_2_X_output.json"  # Replace with your actual JSON file path

    # Load JSON data
    json_data = load_json(json_file)

    # Convert to DataFrame
    df = json_to_dataframe(json_data)

    # Display the DataFrame
    print(df.head(10))

    # Save to CSV for further analysis
    df.to_csv("questions_output.csv", index=False)
    print("DataFrame saved to 'questions_output.csv'")

if __name__ == "__main__":
    main()