# simple_recommend.py - Minimal version
import numpy as np
import pickle
import faiss
import os
import pandas as pd
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("rec_movie")

# Get the directory of the current script to handle paths on Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load once
embeddings_path = os.path.join(BASE_DIR, "final_movie_embeddings_weighted_average.npy")
metadata_path = os.path.join(BASE_DIR, "final_movie_embeddings_weighted_average_metadata.pkl")
index_path = os.path.join(BASE_DIR, "movie_faiss_index_weighted_average.faiss")

logger.info(f"Looking for data files in: {BASE_DIR}")

# Check and load data
try:
    if os.path.exists(embeddings_path) and os.path.exists(metadata_path) and os.path.exists(index_path):
        logger.info("Loading recommendation data files...")
        
        embeddings = np.load(embeddings_path)
        logger.info(f"Embeddings loaded. Shape: {embeddings.shape}")
        
        with open(metadata_path, 'rb') as f:
            meta_data = pickle.load(f)
            _meta = meta_data['df']
        logger.info("Metadata loaded.")
        
        movie_names = _meta['final_name'].tolist()
        
        # Load year column and clean up float/NaN values
        if 'year' in _meta.columns:
            def clean_year(y):
                try:
                    if pd.isna(y): return None
                    iy = int(float(y))
                    if 1900 < iy < 2027: return str(iy)
                    return None
                except:
                    return None
            movie_years = [clean_year(y) for y in _meta['year']]
        elif 'release_year' in _meta.columns:
            movie_years = [str(int(float(y))) if not pd.isna(y) else None for y in _meta['release_year']]
        else:
            movie_years = [None] * len(movie_names)
            
        index = faiss.read_index(index_path)
        logger.info(f"FAISS index loaded. Count: {index.ntotal}")
    else:
        missing = []
        if not os.path.exists(embeddings_path): missing.append("embeddings")
        if not os.path.exists(metadata_path): missing.append("metadata")
        if not os.path.exists(index_path): missing.append("index")
        
        error_msg = f"Warning: Recommendation data files missing: {', '.join(missing)}"
        logger.warning(error_msg)
        embeddings = np.zeros((1, 10))
        movie_names = []
        movie_years = []
        index = None
except Exception as e:
    logger.error(f"Error loading recommendation data: {str(e)}", exc_info=True)
    embeddings = np.zeros((1, 10))
    movie_names = []
    movie_years = []
    index = None

def recommend(movie_name, top_k=8):
    """Get recommendations for a movie"""
    logger.info(f"Recommendation requested for: '{movie_name}'")
    
    if index is None:
        logger.error("Recommendation index is NOT loaded. Returning empty list.")
        return []

    # Find movie
    idx = None
    movie_name_lower = movie_name.lower().strip()
    for i, name in enumerate(movie_names):
        if movie_name_lower in name.lower():
            idx = i
            break
    
    if idx is None:
        logger.warning(f"Movie '{movie_name}' not found in database for recommendations.")
        return []
    
    # Search
    logger.info(f"Found movie '{movie_names[idx]}' at index {idx}. Performing FAISS search...")
    query = embeddings[idx].reshape(1, -1).astype('float32')
    scores, indices = index.search(query, top_k + 1)
    
    # Return results
    results = []
    for i in range(1, top_k + 1):
        if i >= len(indices[0]):
            break
        rec_idx = indices[0][i]
        if rec_idx >= len(movie_names):
            continue
        rec = movie_names[rec_idx]
        # Clean up name
        if "Movie Name is:" in rec:
            rec = rec.split("Movie Name is:")[1].split("(Genre:")[0].split("(Year:")[0].strip()
        year = movie_years[rec_idx] if rec_idx < len(movie_years) else None
        results.append({"name": rec, "similarity": float(scores[0][i]), "year": year})
    
    return results

# Usage
if __name__ == "__main__":
    movie = "7Aum Arivu" # which movie we click 
    print(f"\n🎬 Recommendations for '{movie}':")
    for i, res in enumerate(recommend(movie, top_k=5), 1):
        print(f"   {i}. {res['name']} (year: {res.get('year')}, similarity: {res['similarity']:.4f})")
