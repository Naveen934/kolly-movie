# simple_recommend.py - Minimal version
import numpy as np
import pickle
import faiss
import os
import pandas as pd

# Load once
embeddings_path = "final_movie_embeddings_weighted_average.npy"
metadata_path = "final_movie_embeddings_weighted_average_metadata.pkl"
index_path = "movie_faiss_index_weighted_average.faiss"

# Check if files exist
if os.path.exists(embeddings_path) and os.path.exists(metadata_path) and os.path.exists(index_path):
    embeddings = np.load(embeddings_path)
    with open(metadata_path, 'rb') as f:
        _meta = pickle.load(f)['df']
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
else:
    print("Warning: Recommendation data files not found. Using dummy data for initialization.")
    embeddings = np.zeros((1, 10))
    movie_names = []
    movie_years = []
    index = None

def recommend(movie_name, top_k=8):
    """Get recommendations for a movie"""
    if index is None:
        return []

    # Find movie
    idx = None
    for i, name in enumerate(movie_names):
        if movie_name.lower() in name.lower():
            idx = i
            break
    
    if idx is None:
        return []
    
    # Search
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
