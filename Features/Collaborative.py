import json
import Data

def Collaborative(movie_row):
    dataset = Data.main()
    
    movie_name = movie_row.iloc[0]["movie_title"]
    director = movie_row['director_name'].tolist()
    actors = [movie_row.iloc[0]['actor_1_name'], movie_row.iloc[0]['actor_2_name'], movie_row.iloc[0]['actor_3_name']]
    genres =  movie_row.iloc[0]["genres"].split(" ")

    weights = {'director': 0.15, 'actors': 0.25, 'genres': 0.6}

    similarity_scores = {}

    for index, row in dataset.iterrows():

        if row['movie_title'] == movie_name:
            continue

        iterated_director = row["director_name"]
        iterated_actors = [row['actor_1_name'], row['actor_2_name'], row['actor_3_name']]
        iterated_genres =  row["genres"].split(" ")

        director_similarity = len(set(director).intersection(set(iterated_director))) / len(set(director).union(set(iterated_director))) * weights['director']
        actor_similarity = len(set(actors).intersection(set(iterated_actors))) / len(set(actors).union(set(iterated_actors))) * weights['actors']
        genre_similarity = len(set(genres).intersection(set(iterated_genres))) / len(set(genres).union(set(iterated_genres))) * weights['genres']

        total_similarity = director_similarity + actor_similarity + genre_similarity

        similarity_scores[row['movie_title']] = total_similarity

    top_10_movies = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)[:10]

    top_10_movies_scores_json = json.dumps({movie : score for movie, score in top_10_movies})
    print(top_10_movies_scores_json)
    
    top_10_movies_poster_json = json.dumps(
        {movie.title(): dataset.loc[dataset['movie_title'] == movie, 'poster_url'].iloc[0] for movie, score in top_10_movies},
        indent=4
    )
    
    return top_10_movies_poster_json

if __name__ == "__main__":
    Collaborative()