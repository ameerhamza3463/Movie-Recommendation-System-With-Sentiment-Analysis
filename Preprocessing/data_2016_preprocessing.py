import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import os

load_dotenv()

dir = os.getenv("PROJECT_DIR")

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

    for review in reviews:
        review = review.strip()
        review = re.sub(r'[^\w\s,.!?\'-]', '', review)
        review = review.lower()
        if review:
            cleaned_reviews.append(review)

    return cleaned_reviews

def fetch_and_clean_reviews(row):
    imdb_url = row['movie_imdb_link']
    reviews = get_imdb_reviews(imdb_url)
    cleaned_reviews = clean_reviews(reviews)
    return cleaned_reviews

df = pd.read_csv(f"{dir}/Dataset/movie_metadata.csv")

df = df.loc[:,['director_name','actor_1_name','actor_2_name','actor_3_name','genres','movie_title','movie_imdb_link','title_year']]

df['actor_1_name'] = df['actor_1_name'].replace(np.nan, 'unknown')
df['actor_2_name'] = df['actor_2_name'].replace(np.nan, 'unknown')
df['actor_3_name'] = df['actor_3_name'].replace(np.nan, 'unknown')
df['director_name'] = df['director_name'].replace(np.nan, 'unknown')

df.dropna(how='any',inplace=True)

df_2016 = df.loc[df['title_year'] == 2016]

df_2016['genres'] = df_2016['genres'].str.replace('|', ' ')

df_2016['movie_title'] = df_2016['movie_title'].str.lower()
df_2016['movie_title'] = df_2016['movie_title'].apply(lambda x : x[:-1])

df_2016['imdb_reviews'] = df_2016.apply(fetch_and_clean_reviews, axis=1)

df_2016 = df_2016.rename(columns={'movie_imdb_link':'imdb_url'})
df_2016 = df_2016.drop(columns=['title_year'])

print(df_2016.isna().sum())

df_2016.to_csv(f"{dir}/Dataset/data_2016.csv",index=False)