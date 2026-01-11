import streamlit as st
import pickle
import requests
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_KEY = 8265bd1679663a7ea12ac168da84d2e8

@st.cache_resource
def get_session():
    """Create a requests session with retry logic"""
    session = requests.Session()
    retry = Retry(
        connect=2, 
        backoff_factor=0.3, 
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

@lru_cache(maxsize=100)
def fetch_poster(movie_id):
    """Fetch poster from TMDB API with fallback"""
    try:
        session = get_session()
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        
        # Short timeout - if API is slow, skip and use placeholder
        response = session.get(url, timeout=8)
        response.raise_for_status()
        
        data = response.json()
        
        if "poster_path" in data and data["poster_path"]:
            return "https://image.tmdb.org/t/p/original" + data["poster_path"]
        
    except requests.exceptions.Timeout:
        pass  # Use fallback
    except:
        pass  # Use fallback
    
    # Fallback: placeholder image
    return "https://via.placeholder.com/500x750?text=No+Poster+Available"


st.title("Movie Recommender System")
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

movies_df = pickle.load(open("movies_df.pkl", "rb")) # movies_list has that df -> new_df
similarity_df = pickle.load(open("similarity_mat.pkl", "rb"))

def recommend(movie): # very similar to what we'have build
    '''return 5 similar movies'''
    movie_index = movies_df[movies_df["title"] == movie].index[0] # .[0] think like .index is
    # a box and we take first element -> [0][0] -> 0
    distances = similarity_df[movie_index]
    movies_list = sorted(
        list(enumerate(distances)),  # (index, similarity_score)
        reverse=True, # descending order
        key=lambda x: x[1]) # sorting on similarity wale pr not on index pr
    top_5 = movies_list[1:6]  

    recommended_movies = []
    recommend_movies_posters = []
    for i in top_5:
        # fetch the movie poster
        movie_id = movies_df.iloc[i[0]].movie_id
        recommend_movies_posters.append(fetch_poster(movie_id))
        recommended_movies.append(movies_df.iloc[i[0]].title)

    return recommended_movies, recommend_movies_posters 

movies_titles = movies_df["title"].values

# Custom CSS
page_element="""
<style>
[data-testid="stAppViewContainer"]{
  background-image: url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
  background-size: cover;
}
[data-testid="stHeader"]{
  background-color: rgba(0,0,0,0);
}
.stButton > button {
    background-color: #4D2FB2;         
    color: white;
}
</style>
"""

st.markdown(page_element, unsafe_allow_html=True)

user_selected_movie = st.selectbox(
    "Select a movie",
    (movies_titles),
)

if st.button("Recommend"):
    names, posters = recommend(user_selected_movie)

    cols = st.columns(5)

    for i in range(len(names)):
        with cols[i]:
            st.text(names[i])
            st.image(posters[i])
    
