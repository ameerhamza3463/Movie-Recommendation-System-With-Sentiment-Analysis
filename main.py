from flask import Flask, render_template, request
import sys
import os
import pandas as pd
from dotenv import load_dotenv
import re
import joblib
from collections import Counter
import json
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

current_directory = os.getcwd()
env_path = os.path.join(current_directory, ".env")
# setting up the env_path variable in the .env file
if os.path.exists(env_path):
    with open(env_path, "r") as env_file:
        lines = env_file.readlines()
        if any(line.startswith(f"PROJECT_DIR={current_directory}") for line in lines):
            print("PROJECT_DIR is already set to the current directory.")
        elif any(line.startswith("PROJECT_DIR=") for line in lines):
            print("PROJECT_DIR exists but points to a different directory.")
        else:
            with open(env_path, "a") as env_file:
                env_file.write(f"\nPROJECT_DIR='{current_directory}'\n")
                print("PROJECT_DIR added to .env")
else:
    with open(env_path, "w") as env_file:
        env_file.write(f"PROJECT_DIR='{current_directory}'\n")
        print(".env file created and PROJECT_DIR added")

load_dotenv()

dir = os.getenv("PROJECT_DIR")

features_dir = os.path.join(dir, "Features")
if features_dir not in sys.path:
    sys.path.append(features_dir)

import Data
import Collaborative

dataset = Data.main()

model_gb = joblib.load(f"{dir}/NLP/models/model_gb.pkl")
model_lr = joblib.load(f"{dir}/NLP/models/model_lr.pkl")
model_nb = joblib.load(f"{dir}/NLP/models/model_nb.pkl")
model_rf = joblib.load(f"{dir}/NLP/models/model_rf.pkl")
model_svm = joblib.load(f"{dir}/NLP/models/model_svm.pkl")
vectorizer = joblib.load(f"{dir}/NLP/models/vectorizer.pkl")

models = {
    "Gradient Boosting": model_gb,
    "Logistic Regression": model_lr,
    "Naive Bayes": model_nb,
    "Random Forest": model_rf,
    "SVM": model_svm,
}

label_mapping_reverse = {0: "positive", 1: "nuetral", 2: "negative"}


def get_movie_row(movie_name):
    filtered_data = dataset[
        dataset["movie_title"].str.strip().str.match(movie_name, case=False, na=False)
    ]
    return filtered_data


def create_detail_object(movie_row, sentiments , recommended):
    data = {}
    data["name"] = movie_row.iloc[0]["movie_title"].title()
    data["director"] = movie_row["director_name"].tolist()[:3]
    data["actors"] = [
        actor
        for actor in [
            movie_row.iloc[0]["actor_1_name"],
            movie_row.iloc[0]["actor_2_name"],
            movie_row.iloc[0]["actor_3_name"],
        ]
        if actor.lower() != "unknown"
    ]
    data["genres"] = movie_row.iloc[0]["genres"].split(" ")
    data["reviews"] = sentiments
    data['recommended_movies'] = json.loads(recommended)
    data["poster"] = movie_row.iloc[0]["poster_url"]
    data["description"] = movie_row.iloc[0]["description"].capitalize()
    return data


def get_sentiment(movie_reviews):
    results = {}

    if movie_reviews and len(movie_reviews) > 0:
        for review in movie_reviews:
            vectorized_review = vectorizer.transform([review])

            predictions = []
            for model_name, model in models.items():
                prediction = model.predict(vectorized_review)[0]
                predicted_label = label_mapping_reverse[
                    int(prediction)
                ]
                predictions.append(predicted_label)

            prediction_counts = Counter(predictions)
            most_common = prediction_counts.most_common()

            final_sentiment = "nuetral"
            if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
                if ((most_common[0] == "positive" and most_common[1] == "negative") or (most_common[0] == "negative" and most_common[1] == "positive")):
                    final_sentiment = "nuetral"
                elif ((most_common[0] == "positive" and most_common[1] == "nuetral") or (most_common[0] == "nuetral" and most_common[1] == "positive")):
                    final_sentiment = "positive"
                elif ((most_common[0] == "nuetral" and most_common[1] == "negative") or (most_common[0] == "negative" and most_common[1] == "nuetral")):
                    final_sentiment = "negative"
                else:
                    final_sentiment = "nuetral"
            else:
                final_sentiment = most_common[0][0]

            results[review] = final_sentiment

    return results


def get_recommended(movie_url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}
    cleaned_url = movie_url.split('/?')[0]

    response = requests.get(cleaned_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'lxml')

        recommended_movies = {}

        movie_cards = soup.find_all('div', class_='ipc-media')

        for card in movie_cards:
            title_span = card.find_next('span', attrs={"data-testid": "title"})
            movie_name = title_span.text if title_span else None
            img_tag = card.find('img', class_='ipc-image')
            poster_url = img_tag['src'] if img_tag else None
            if movie_name and poster_url:
                recommended_movies[movie_name] = poster_url
                
            if len(recommended_movies) >= 10:
                break
        
        return recommended_movies
    else:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")
        return {}


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/recommend", methods=["GET"])
def recommend():
    movie = request.args.get("search")
    if movie:
        filtered_data = get_movie_row(movie)
        if filtered_data.empty:
            return render_template("error.html")
        else:
            sentiments = get_sentiment(filtered_data.iloc[0]["imdb_reviews"])
            recommended = Collaborative.Collaborative(filtered_data)
            data = create_detail_object(filtered_data, sentiments, recommended)
            return render_template("recommend.html", data=data)
    else:
        return render_template("error.html")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port="5000")