import pandas as pd
import numpy as np
from tmdbv3api import TMDb
from tmdbv3api import Movie
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re
import math

load_dotenv()

tmdb = TMDb()
tmdb_movie = Movie()
tmdb.api_key = os.getenv("TMDB_API_KEY")
dir = os.getenv("PROJECT_DIR")

def get_genre(x):
    genres = []
    try:
        result = tmdb_movie.search(x)
        if result:
            movie_id = result[0].id
            response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={tmdb.api_key}')
            data_json = response.json()

            if 'genres' in data_json and data_json['genres']:
                for genre in data_json['genres']:
                    genres.append(genre['name'])
                return " ".join(genres)
            else:
                return np.NaN
        else:
            return np.NaN
    except Exception as e:
        print(f"Error in get_genre for {x}: {e}")
        return np.NaN


def get_imdb(x):
  try:
      result = tmdb_movie.search(x)
      if not result:
          return np.NaN
      movie_id = result[0].id
      response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}'.format(movie_id, tmdb.api_key))
      data_json = response.json()
      imdb_id = data_json.get('imdb_id', None)
      if imdb_id:
          return f"https://www.imdb.com/title/{imdb_id}/"
      else:
          return np.NaN
  except Exception as e:
      print(f"Error in get_imdb for {x}: {e}")
      return np.NaN


def get_imdb_reviews(imdb_url):
    imdb_id = imdb_url.split("/title/")[1].split("/")[0]

    url = f'https://www.imdb.com/title/{imdb_id}/reviews/?ref_=tt_ql_urv'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            reviews_div = soup.find_all("div", {"class": "ipc-html-content-inner-div"})
            reviews_list = [review.string.strip() for review in reviews_div if review.string]
            return reviews_list
        else:
            return []
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return []


def clean_reviews(reviews):
    cleaned_reviews = []

    if len(reviews) == 0:
        return []

    for review in reviews:
        review = review.strip()
        review = re.sub(r'[^\w\s,.!?\'-]', '', review)
        review = review.lower()
        if review:
            cleaned_reviews.append(review)

    return cleaned_reviews


def fetch_and_clean_reviews(row):
    reviews = get_imdb_reviews(row['imdb_url'])
    cleaned_reviews = clean_reviews(reviews)
    return cleaned_reviews


def get_director(x):
    if " (director)" in x:
        return x.split(" (director)")[0]
    elif " (directors)" in x:
        return x.split(" (directors)")[0]
    else:
        return x.split(" (director/screenplay)")[0]

def get_actor1(x):
    return ((x.split("screenplay); ")[-1]).split(", ")[0])

def get_actor2(x):
    if len((x.split("screenplay); ")[-1]).split(", ")) < 2:
        return np.NaN
    else:
        return ((x.split("screenplay); ")[-1]).split(", ")[1])

def get_actor3(x):
    if len((x.split("screenplay); ")[-1]).split(", ")) < 3:
        return np.NaN
    else:
        return ((x.split("screenplay); ")[-1]).split(", ")[2])


link = "https://en.wikipedia.org/wiki/List_of_American_films_of_2020"
df1 = pd.read_html(link, header=0)[2]
df2 = pd.read_html(link, header=0)[3]
df3 = pd.read_html(link, header=0)[4]
df4 = pd.read_html(link, header=0)[5]

df_2020 = pd.concat([df1, df2, df3, df4], ignore_index=True)

df_2020 = df_2020[['Title','Cast and crew']]

df_2020['genres'] = df_2020['Title'].map(lambda x: get_genre(str(x)))
df_2020.dropna(how='any' , inplace=True)
df_2020['imdb_url'] = df_2020['Title'].apply(get_imdb)
df_2020['imdb_reviews'] = df_2020.apply(fetch_and_clean_reviews, axis=1)

df_2020['director_name'] = df_2020['Cast and crew'].map(lambda x: get_director(str(x)))
df_2020['actor_1_name'] = df_2020['Cast and crew'].map(lambda x: get_actor1(x))
df_2020['actor_2_name'] = df_2020['Cast and crew'].map(lambda x: get_actor2(x))
df_2020['actor_3_name'] = df_2020['Cast and crew'].map(lambda x: get_actor3(x))

df_2020 = df_2020.rename(columns={'Title':'movie_title'})
new_df20 = df_2020.drop(columns=['Cast and crew'])

new_df20['actor_2_name'] = new_df20['actor_2_name'].replace(np.nan, 'unknown')
new_df20['actor_3_name'] = new_df20['actor_3_name'].replace(np.nan, 'unknown')
new_df20['movie_title'] = new_df20['movie_title'].str.lower()

print(new_df20.isna().sum())

new_df20.to_csv(f"{dir}/Dataset/data_2020.csv", index=False)