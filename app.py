import streamlit as st
import pickle
import pandas as pd
import requests
from urllib.parse import quote

# Configuration
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide"
)


# Load the movie data and similarity matrix
@st.cache_data
def load_data():
    try:
        movies = pickle.load(open('/Users/Dell/Desktop/movie recommender system/movie_list.pkl', 'rb'))
        similarity = pickle.load(open('/Users/Dell/Desktop/movie recommender system/similarity.pkl', 'rb'))
        return movies, similarity
    except FileNotFoundError:
        st.error("Data files not found! Make sure movie_list.pkl and similarity.pkl are in the same directory.")
        return None, None


# Function to fetch movie poster using OMDb API
@st.cache_data
def fetch_poster_omdb(movie_title, omdb_api_key):
    """
    Fetch movie poster using OMDb API
    """
    try:
        clean_title = movie_title.replace(":", "").replace("'", "'").strip()
        url = f"http://www.omdbapi.com/?t={quote(clean_title)}&apikey={omdb_api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('Response') == 'True':
                poster_url = data.get('Poster')
                if poster_url and poster_url != 'N/A':
                    return poster_url, data.get('Year', 'Unknown'), data.get('imdbRating', 'N/A'), data.get('Plot',
                                                                                                            'No description available')
        return create_placeholder_poster(movie_title), 'Unknown', 'N/A', 'No description available'
    except Exception as e:
        return create_placeholder_poster(movie_title), 'Unknown', 'N/A', 'No description available'


def create_placeholder_poster(movie_title):
    title_short = movie_title[:30] + "..." if len(movie_title) > 30 else movie_title
    encoded_title = quote(title_short)
    return f"https://via.placeholder.com/300x450/1a1a1a/ffffff?text={encoded_title}"


# Function to recommend movies
def recommend(movie, movies, similarity):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[movie_index])), reverse=True, key=lambda x: x[1])
        recommended_movies = []
        for i in range(1, 6):  # Skip the first one (itself) and get next 5
            idx = distances[i][0]
            movie_data = movies.iloc[idx]
            recommended_movies.append({
                'title': movie_data.title,
                'movie_id': movie_data.movie_id,
                'description': movie_data.tags[:300] + "..." if len(movie_data.tags) > 300 else movie_data.tags
            })
        return recommended_movies
    except Exception as e:
        st.error(f"Error getting recommendations: {e}")
        return []


# Main application
def main():
    st.markdown("""
    <style>
    .main-header {text-align: center; color: #ff6b6b; font-size: 3rem; margin-bottom: 1rem;}
    .subtitle {text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 2rem;}
    .movie-description {font-style: italic; color: #666; margin: 10px 0;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">🎬 Movie Recommender System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Discover movies you\'ll love based on your preferences</p>',
                unsafe_allow_html=True)

    # API Key input
    omdb_api_key = st.sidebar.text_input("Enter your OMDb API Key:", type="password")
    if not omdb_api_key:
        st.warning("⚠️ Please enter your OMDb API key in the sidebar.")
        st.info("Get one for free at: http://www.omdbapi.com/apikey.aspx")

    # Load data
    movies, similarity = load_data()
    if movies is None:
        st.stop()

    #st.success(f"✅ Loaded {len(movies)} movies successfully!")

    # Movie selection
    st.sidebar.header("🎯 Movie Selection")
    search_term = st.sidebar.text_input("🔍 Search for a movie:")
    movie_list = movies['title'].values

    if search_term:
        filtered_movies = [movie for movie in movie_list if search_term.lower() in movie.lower()]
        selected_movie = st.sidebar.selectbox("Search Results:",
                                              filtered_movies) if filtered_movies else st.sidebar.selectbox(
            "All Movies:", movie_list, index=0)
    else:
        selected_movie = st.sidebar.selectbox("Choose a movie:", movie_list, index=0)

    # Display selected movie
    if selected_movie:
        st.markdown("---")
        st.subheader("🎬 Selected Movie")
        col1, col2 = st.columns([1, 2])

        with col1:
            if omdb_api_key:
                poster_url, year, rating, plot = fetch_poster_omdb(selected_movie, omdb_api_key)
                st.image(poster_url, width=250, caption=f"{selected_movie}")
            else:
                st.image(create_placeholder_poster(selected_movie), width=250, caption=selected_movie)
                year, rating, plot = "Unknown", "N/A", "Enter your API key to see description"

        with col2:
            st.markdown(f"**{selected_movie}**")
            st.markdown(f"**Year:** {year}")
            st.markdown(f"**IMDb Rating:** ⭐ {rating}/10")
            st.markdown(f"**Movie ID:** {movies[movies['title'] == selected_movie].iloc[0].movie_id}")
            st.markdown(f'<div class="movie-description">{plot}</div>', unsafe_allow_html=True)

    # Recommendation section
    st.markdown("---")
    if st.button("🔍 Get Movie Recommendations", type="primary"):
        if selected_movie:
            with st.spinner("🎯 Finding movies similar to your selection..."):
                recommendations = recommend(selected_movie, movies, similarity)

                if recommendations:
                    st.subheader(f"🎭 Movies Similar to '{selected_movie}'")

                    for i, movie in enumerate(recommendations):
                        col1, col2 = st.columns([1, 3])

                        with col1:
                            if omdb_api_key:
                                poster_url, year, rating, plot = fetch_poster_omdb(movie['title'], omdb_api_key)
                                st.image(poster_url, width=200)
                            else:
                                st.image(create_placeholder_poster(movie['title']), width=200)
                                year, rating, plot = "Unknown", "N/A", "Enter your API key to see description"

                        with col2:
                            st.markdown(f"**#{i + 1}: {movie['title']}**")
                            st.markdown(f"**Year:** {year}")
                            st.markdown(f"**IMDb Rating:** ⭐ {rating}/10")
                            st.markdown(f'<div class="movie-description"> {plot}</div>',
                                        unsafe_allow_html=True)
                            st.markdown(f"**Tags:** {movie['description']}")

                        st.markdown("---")
                else:
                    st.error("❌ Could not find recommendations for this movie.")

    # Information section
    st.markdown("---")
    with st.expander("📊 System Information"):
        st.markdown("### 🔧 How it Works:")
        st.markdown("- **Content-Based Filtering**: Analyzes movie features")
        st.markdown("- **Cosine Similarity**: Mathematical similarity calculation")
        st.markdown("- **5000 Features**: Top keywords, genres, cast, crew")
        st.markdown("- **Real-time**: Pre-computed similarity matrix for speed")

        st.markdown("### 📈 Statistics:")
        st.markdown(f"- **Dataset Size**: {len(movies)} movies")
        st.markdown("- **Features**: Genres, Cast, Crew, Keywords, Overview")
        st.markdown("- **Similarity Algorithm**: Cosine Similarity")
        st.markdown("- **Poster Source**: OMDb API")

    # Footer metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📽️ Total Movies", f"{len(movies):,}")
    with col2:
        st.metric("🎯 Features Used", "5,000")
    with col3:
        st.metric("🔄 Recommendations", "5")
    with col4:
        st.metric("⚡ Algorithm", "Cosine Similarity")


if __name__ == "__main__":
    main()
