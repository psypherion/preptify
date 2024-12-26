import os
import pandas as pd

class TopicCategorizer:
    """
    Class to categorize topics based on their frequency in a dataset and organize them into directories.
    """

    def __init__(self, csv_file_path, study_dir="study"):
        """
        Initialize the TopicCategorizer with the dataset path and output directory.

        Args:
            csv_file_path (str): Path to the CSV file containing the dataset.
            study_dir (str): Base directory for saving categorized data.
        """
        self.csv_file_path = csv_file_path
        self.study_dir = study_dir
        self.df = self.load_data()

    def load_data(self):
        """
        Load the data from the CSV file.

        Returns:
            pd.DataFrame: Loaded dataset.
        """
        if not os.path.exists(self.csv_file_path):
            raise FileNotFoundError(f"File not found: {self.csv_file_path}")
        return pd.read_csv(self.csv_file_path)

    def save_topics_to_file(self):
        """
        Save the unique topics to a text file.
        """
        topics = self.df["topic"].unique()
        topics_file = os.path.join(self.study_dir, "topics.txt")
        os.makedirs(self.study_dir, exist_ok=True)

        with open(topics_file, "w") as file:
            file.write(str(list(topics)))

    def calculate_topic_frequencies(self):
        """
        Calculate frequencies of each topic in the dataset.

        Returns:
            list: List of tuples containing topic and its frequency.
        """
        topics = self.df["topic"].unique()
        return [(topic, len(self.df[self.df["topic"] == topic])) for topic in topics]

    def categorize_topics(self, topic_frequencies):
        """
        Categorize topics based on their frequencies.

        Args:
            topic_frequencies (list): List of tuples with topic and frequency.

        Returns:
            dict: Categorized topics into most, moderate, and least important.
        """
        topic_frequencies.sort(key=lambda x: x[1], reverse=True)
        max_freq = topic_frequencies[0][1]
        min_freq = topic_frequencies[-1][1]
        range_diff = max_freq - min_freq

        range_1 = max_freq - range_diff // 3
        range_2 = range_1 - range_diff // 3

        return {
            "most_important": [(topic, freq) for topic, freq in topic_frequencies if freq >= range_1],
            "moderately_important": [(topic, freq) for topic, freq in topic_frequencies if range_2 <= freq < range_1],
            "least_important": [(topic, freq) for topic, freq in topic_frequencies if freq < range_2]
        }, (range_1, range_2)

    def create_directories(self):
        """
        Create directories for categorized data.

        Returns:
            dict: Directory paths for categories.
        """
        output_dirs = {
            "most_important": os.path.join(self.study_dir, "most_important"),
            "moderately_important": os.path.join(self.study_dir, "moderately_important"),
            "least_important": os.path.join(self.study_dir, "least_important")
        }

        for dir_path in output_dirs.values():
            os.makedirs(dir_path, exist_ok=True)

        return output_dirs

    def save_category_data(self, categories, output_dirs):
        """
        Save categorized data to directories as CSV files.

        Args:
            categories (dict): Categorized topics.
            output_dirs (dict): Directories for saving each category.
        """
        for category, topics in categories.items():
            category_dir = output_dirs[category]
            category_df = pd.DataFrame(topics, columns=["Topic", "Frequency"])
            category_df.to_csv(os.path.join(category_dir, f"{category}_topics.csv"), index=False)

            for topic, _ in topics:
                topic_data = self.df.loc[self.df["topic"] == topic, ["question","option_a","option_b","option_c","option_d", "answer", "explanation"]]
                topic_csv = os.path.join(category_dir, f"{str(topic).replace('/', '_')}.csv")
                topic_data.to_csv(topic_csv, index=False)

    def run(self):
        """
        Execute the categorization process.
        """
        self.save_topics_to_file()
        topic_frequencies = self.calculate_topic_frequencies()
        categorized_topics, ranges = self.categorize_topics(topic_frequencies)
        range_1, range_2 = ranges

        print(f"Ranges: Most Important: >= {range_1}, Moderately Important: >= {range_2}, Less Important: < {range_2}")

        output_dirs = self.create_directories()
        self.save_category_data(categorized_topics, output_dirs)

        print("Categorization and directory creation complete.")

if __name__ == "__main__":
    csv_file_path = "db/questions_db.csv"
    categorizer = TopicCategorizer(csv_file_path)
    categorizer.run()
