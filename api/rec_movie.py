from pathlib import Path
import numpy as np
import pickle
import os
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
BASE_DIR = Path(__file__).resolve().parent

# Load once
embeddings_path = BASE_DIR / "temple_tower.npy"
metadata_path = BASE_DIR / "temple_tower_data.pkl"

logger.info(f"Looking for data files in: {BASE_DIR}")

# Global variables
embeddings = None
movie_names = []
movie_years = []
load_error = None

# Check and load data
try:
    if embeddings_path.exists() and metadata_path.exists():
        logger.info("Loading recommendation data files...")
        
        # Load and normalize embeddings for fast dot-product cosine similarity
        raw_embeddings = np.load(str(embeddings_path)).astype('float32')
        norms = np.linalg.norm(raw_embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1.0
        embeddings = raw_embeddings / norms
        logger.info(f"Embeddings loaded and normalized. Shape: {embeddings.shape}")
        
        with open(metadata_path, 'rb') as f:
            meta_data = pickle.load(f)
            _meta = meta_data['df']
        logger.info("Metadata loaded.")
        
        movie_names = _meta['final_name'].tolist()
        
        # Load year column and clean up float/NaN values
        if 'year' in _meta.columns:
            def clean_year(y):
                try:
                    if y is None or (isinstance(y, float) and np.isnan(y)): return None
                    iy = int(float(y))
                    if 1900 < iy < 2027: return str(iy)
                    return None
                except:
                    return None
            movie_years = [clean_year(y) for y in _meta['year']]
        elif 'release_year' in _meta.columns:
            movie_years = [str(int(float(y))) if y is not None and not (isinstance(y, float) and np.isnan(y)) else None for y in _meta['release_year']]
        else:
            movie_years = [None] * len(movie_names)
            
        logger.info(f"Engine initialized with {len(movie_names)} movies.")
    else:
        missing = []
        if not embeddings_path.exists(): missing.append("embeddings")
        if not metadata_path.exists(): missing.append("metadata")
        
        load_error = f"Recommendation data files missing: {', '.join(missing)}"
        logger.warning(load_error)
except Exception as e:
    load_error = f"Error loading recommendation data: {str(e)}"
    logger.error(load_error, exc_info=True)

def get_status():
    """Return the current status of the recommendation engine"""
    return {
        "loaded": embeddings is not None,
        "movies_count": len(movie_names),
        "embeddings_shape": embeddings.shape if embeddings is not None else None,
        "error": load_error,
        "base_dir": str(BASE_DIR),
        "backend": "numpy-ultralight"
    }

def recommend(movie_name, top_k=8):
    """Get recommendations for a movie using NumPy brute-force (instant for 1.6k movies)"""
    logger.info(f"Recommendation requested for: '{movie_name}'")
    
    if embeddings is None:
        logger.error("Recommendation engine is NOT loaded. Returning empty list.")
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
    
    # Search via Dot Product (since vectors are normalized)
    logger.info(f"Found movie '{movie_names[idx]}' at index {idx}. Performing NumPy search...")
    query_vec = embeddings[idx]
    
    # Calculate similarity scores (cosine similarity = dot product of normalized vectors)
    similarities = np.dot(embeddings, query_vec)
    
    # Get top_k + 1 results (to skip self)
    # argsort gives indices from smallest to largest, so we take the end and reverse
    # We take top_k + 5 just in case of duplicates
    top_indices = np.argsort(similarities)[-(top_k + 5):][::-1]
    
    # Return results
    results = []
    seen_names = {movie_names[idx].lower().strip()} # Skip the query movie itself
    
    for rec_idx in top_indices:
        rec_raw = movie_names[rec_idx]
        rec_clean = rec_raw
        if "Movie Name is:" in rec_raw:
            rec_clean = rec_raw.split("Movie Name is:")[1].split("(Genre:")[0].split("(Year:")[0].strip()
        else:
            # Robust cleaning: remove anything in parentheses and extra whitespace
            import re
            rec_clean = re.sub(r'\(.*?\)', '', rec_raw).strip()
            # Also handle common year patterns without parentheses at the end if any
            rec_clean = re.sub(r'\s+\d{4}$', '', rec_clean).strip()
        
        name_lower = rec_clean.lower().strip()

        if name_lower in seen_names:
            continue
            
        score = float(similarities[rec_idx])
        year = movie_years[rec_idx] if rec_idx < len(movie_years) else None
        
        results.append({
            "name": rec_clean, 
            "similarity": score, 
            "year": year
        })
        seen_names.add(name_lower)
        
        if len(results) >= top_k:
            break
    
    return results

# Usage
if __name__ == "__main__":
    movie = "7Aum Arivu" 
    print(f"\n🎬 Recommendations for '{movie}':")
    for i, res in enumerate(recommend(movie, top_k=5), 1):
        print(f"   {i}. {res['name']} (year: {res.get('year')}, similarity: {res['similarity']:.4f})")
