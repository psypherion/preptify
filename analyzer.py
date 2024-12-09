import json
from collections import Counter
from typing import List, Dict

def load_json(file_path: str) -> List[Dict]:
    """Load JSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def get_frequent_topics(questions: List[Dict]) -> Dict[str, int]:
    """Count the frequency of topics in the questions."""
    topic_counter = Counter()
    for question_set in questions:
        for question in question_set.get("questions", []):
            topic = question.get("category", {}).get("topic", "Unknown Topic")
            topic_counter[topic] += 1
    return topic_counter

def get_frequent_subtopics(questions: List[Dict], syllabus: List[Dict]) -> Dict[str, int]:
    """Count the frequency of subtopics in the questions based on the syllabus."""
    subtopic_counter = Counter()
    topic_to_subtopics = {
        topic["topic_name"]: topic.get("sub_topics", [])
        for unit in syllabus for unit_data in unit.get("units", [])
        for topic in unit_data.get("topics", [])
    }
    for question_set in questions:
        for question in question_set.get("questions", []):
            topic = question.get("category", {}).get("topic", "")
            subtopics = topic_to_subtopics.get(topic, [])
            for subtopic in subtopics:
                subtopic_counter[subtopic] += 1
    return subtopic_counter

def generate_leaderboard(counter: Counter, top_n: int = 10, output_file: str = None) -> None:
    """Print and optionally save a leaderboard of the most frequent topics or subtopics."""
    result = []
    print("\nLeaderboard:")
    print("Rank | Name                                    | Frequency")
    print("--------------------------------------------------------")
    for rank, (name, freq) in enumerate(counter.most_common(top_n), start=1):
        line = f"{rank:4} | {name:40} | {freq}"
        print(line)
        result.append(line)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(result))
        print(f"Leaderboard saved to {output_file}")

def main():
    """Main function to load data, analyze topics and subtopics, and display leaderboards."""
    questions_file = "paper_2_X_output.json"
    syllabus_file = "syllabus.json"

    questions = load_json(questions_file)
    syllabus = load_json(syllabus_file)

    topic_frequencies = get_frequent_topics(questions)
    generate_leaderboard(topic_frequencies, top_n=10, output_file="topic_leaderboard.txt")

    subtopic_frequencies = get_frequent_subtopics(questions, syllabus)
    generate_leaderboard(subtopic_frequencies, top_n=10, output_file="subtopic_leaderboard.txt")

if __name__ == "__main__":
    main()
