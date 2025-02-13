import pandas as pd
import numpy as np
from tmdbv3api import TMDb
from tmdbv3api import Movie
import json
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
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
    result = tmdb_movie.search(x)
    movie_id = result[0].id
    response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}'.format(movie_id,tmdb.api_key))
    data_json = response.json()
    if data_json['genres']:
        genre_str = " "
        for i in range(0,len(data_json['genres'])):
            genres.append(data_json['genres'][i]['name'])
        return genre_str.join(genres)
    else:
        np.NaN


def get_imdb(x):
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


link = "https://en.wikipedia.org/wiki/List_of_American_films_of_2018"
df1 = pd.read_html(link, header=0)[2]
df2 = pd.read_html(link, header=0)[3]
df3 = pd.read_html(link, header=0)[4]
df4 = pd.read_html(link, header=0)[5]

df = pd.concat([df1, df2, df3, df4], ignore_index=True)

df_2018 = df[["Title", "Cast and crew"]]

df['genres'] = df['Title'].map(lambda x: get_genre(str(x)))
df_2018['imdb_url'] = df_2018['Title'].apply(get_imdb)
df_2018.dropna(how='any' , inplace=True)
df_2018['imdb_reviews'] = df_2018.apply(fetch_and_clean_reviews, axis=1)

df_2018['director_name'] = df_2018['Cast and crew'].apply(get_director)
df_2018['actor_1_name'] = df_2018['Cast and crew'].apply(get_actor1)
df_2018['actor_2_name'] = df_2018['Cast and crew'].apply(get_actor2)
df_2018['actor_3_name'] = df_2018['Cast and crew'].apply(get_actor3)

df_2018 = df_2018.rename(columns={'Title':'movie_title'})
new_df18 = df_2018.drop(columns=['Cast and crew'])

new_df18['actor_2_name'] = new_df18['actor_2_name'].replace(np.nan, 'unknown')
new_df18['actor_3_name'] = new_df18['actor_3_name'].replace(np.nan, 'unknown')
new_df18['movie_title'] = new_df18['movie_title'].str.lower()

print(new_df18.isna().sum())

new_df18.to_csv(f"{dir}/Dataset/data_2018.csv", index=False)