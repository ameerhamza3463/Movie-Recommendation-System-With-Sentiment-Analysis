import pandas as pd
import ast
import os
from dotenv import load_dotenv

load_dotenv()

dir = os.getenv("PROJECT_DIR")

def combine_csvs():
    data_2016 = pd.read_csv(f"{dir}/Dataset/data_2016.csv")
    data_2018 = pd.read_csv(f"{dir}/Dataset/data_2018.csv")
    data_2019 = pd.read_csv(f"{dir}/Dataset/data_2019.csv")
    data_2020 = pd.read_csv(f"{dir}/Dataset/data_2020.csv")
    combined_df = pd.concat([data_2016, data_2018, data_2019, data_2020], ignore_index=True)    
    return combined_df


def process_reviews(df):
    def parse_reviews(review_str):
        try:
            reviews = ast.literal_eval(review_str)
            if isinstance(reviews, list):
                return [review.strip() for review in reviews]
            else:
                return []
        except (ValueError, SyntaxError):
            return []
    
    df["imdb_reviews"] = df["imdb_reviews"].apply(parse_reviews)
    return df


def main():
    combined_df = combine_csvs()
    processed_df = process_reviews(combined_df)
    return processed_df


if __name__ == "__main__":
    processed_df = main()