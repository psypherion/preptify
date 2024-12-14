import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class DataVisualizer:
    """
    Class to visualize data from a DataFrame.
    """
    def __init__(self, csv_file_path):
        """
        Initialize the visualizer with the path to the CSV file.

        Args:
            csv_file_path (str): Path to the CSV file.
        """
        self.csv_file_path = csv_file_path
        self.df = self.load_data()

    def load_data(self):
        """
        Load the data from the CSV file.

        Returns:
            pd.DataFrame: Loaded dataset.
        """
        try:
            return pd.read_csv(self.csv_file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.csv_file_path}")

    def plot_topic_frequencies(self, top_n=10):
        """
        Plot the top N topics by frequency.

        Args:
            top_n (int): Number of top topics to display.
        """
        topic_counts = self.df["topic"].value_counts().head(top_n)

        plt.figure(figsize=(10, 6))
        sns.barplot(x=topic_counts.values, y=topic_counts.index, palette="viridis")
        plt.title(f"Top {top_n} Topics by Frequency")
        plt.xlabel("Frequency")
        plt.ylabel("Topic")
        plt.tight_layout()
        plt.show()

    def plot_answer_distribution(self):
        """
        Plot the distribution of answers across the dataset.
        """
        answer_counts = self.df["answer"].value_counts()

        plt.figure(figsize=(8, 6))
        sns.barplot(x=answer_counts.index, y=answer_counts.values, palette="magma")
        plt.title("Answer Distribution")
        plt.xlabel("Answer")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.show()

    def plot_question_lengths(self):
        """
        Plot the distribution of question lengths.
        """
        self.df["question_length"] = self.df["question"].str.len()

        plt.figure(figsize=(10, 6))
        sns.histplot(self.df["question_length"], bins=20, kde=True, color="blue")
        plt.title("Distribution of Question Lengths")
        plt.xlabel("Question Length")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.show()

    def run_visualizations(self):
        """
        Run all visualizations.
        """
        print("Visualizing topic frequencies...")
        self.plot_topic_frequencies()

        print("Visualizing answer distribution...")
        self.plot_answer_distribution()

        print("Visualizing question lengths...")
        self.plot_question_lengths()

if __name__ == "__main__":
    csv_file_path = "db/questions_db.csv"
    visualizer = DataVisualizer(csv_file_path)
    visualizer.run_visualizations()
