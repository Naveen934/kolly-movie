import sys
import os
import traceback
import logging
from datetime import datetime, timedelta
import re
import numpy as np


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to sys.path to ensure local imports work on Vercel
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.append(api_dir)

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Global states
recommend_func = None
get_status_func = None
supabase = None
import_error = None
poster_cache = {}
last_cache_refresh = None
cache_error = None
total_rows_fetched = 0



# Try to load engine
try:
    import rec_movie
    recommend_func = rec_movie.recommend
    get_status_func = rec_movie.get_status
    logger.info("Recommendation engine loaded successfully")
except Exception as e:
    import_error = str(e)
    logger.error(f"Engine import failed: {e}")
    get_status_func = lambda: {"loaded": False, "error": import_error}

# Try to load supabase
try:
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")
    
    if not url or not key:
        # Fallback to hardcoded credentials if env vars are missing
        url = "https://uuvkjqcnkgwhagpyfguz.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV1dmtqcWNua2d3aGFncHlmZ3V6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NzYzNTAsImV4cCI6MjA4OTU1MjM1MH0.ew3GkB6uB6egtx5lWYDFdcEKaTtRDMHZYFEXNin6RBg"
    
    if url and key:
        supabase = create_client(url, key)
        logger.info(f"Supabase client initialized")
    else:
        logger.warning("Supabase credentials missing.")

except Exception as e:
    logger.error(f"Supabase init failed: {e}")



def refresh_poster_cache():
    global poster_cache, last_cache_refresh, cache_error, total_rows_fetched


    if not supabase:
        return
    
    try:
        logger.info("Refreshing poster cache...")
        # Fetch all movies (limit 5000 to cover all 1652+ rows)
        response = supabase.table("tamil_movies").select("movie_name, poster, year").limit(5000).execute()
        total_rows_fetched = len(response.data) if response.data else 0
        if response.data:

            # Map normalized name + year to poster URL
            # Also map normalized name to the LATEST poster for fallback
            new_cache = {}
            for item in response.data:
                name = item.get("movie_name")
                poster = item.get("poster")
                year = item.get("year")
                
                if name and poster:
                    # Robust name normalization: remove any non-alphanumeric, squash spaces, lower case
                    clean_name = re.sub(r'[^a-z0-9]', '', name.lower()).strip()
                    normalized_name = name.lower().strip()

                    # Robust year handling: convert to string, handle float/NaN
                    year_str = ""
                    try:
                        if year is not None:
                            year_int = int(float(year))
                            if 1900 < year_int < 2030:
                                year_str = str(year_int)
                    except:
                        pass
                    
                    # 1. Exact Name + Year match
                    if year_str:
                        new_cache[f"{normalized_name}_{year_str}"] = poster
                    
                    # 2. Cleaned Name match (for robustness against hyphens/spaces)
                    if clean_name and year_str:
                        new_cache[f"{clean_name}_{year_str}"] = poster
                    
                    # 3. Latest/fallback for name-only
                    existing = new_cache.get(normalized_name)
                    if not existing or (year_str and year_str > existing.get("year", "")):
                        new_cache[normalized_name] = {"poster": poster, "year": year_str}
                    
                    # 4. Fallback for clean name-only
                    existing_clean = new_cache.get(f"clean_{clean_name}")
                    if not existing_clean or (year_str and year_str > existing_clean.get("year", "")):
                        new_cache[f"clean_{clean_name}"] = {"poster": poster, "year": year_str}

            
            poster_cache = new_cache
            last_cache_refresh = datetime.now()
            cache_error = None
            logger.info(f"Poster cache refreshed: {len(poster_cache)} entries")
    except Exception as e:
        cache_error = str(e)
        logger.error(f"Failed to refresh poster cache: {e}")


# Initial cache population
refresh_poster_cache()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api")
@app.get("/api/")
async def root():
    # Return some cache samples for debugging
    samples = {}
    if poster_cache:
        samples = {k: v for i, (k, v) in enumerate(poster_cache.items()) if i < 10}
    
    return {
        "message": "Movie Recommendation API is running", 
        "engine": "numpy-ultralight",
        "cache_size": len(poster_cache),
        "last_refresh": str(last_cache_refresh),
        "cache_error": cache_error,
        "rows_fetched": total_rows_fetched,
        "supabase_connected": supabase is not None,

        "cache_samples": samples
    }




@app.get("/health")
@app.get("/api/health")
async def health_check():
    status = get_status_func() if get_status_func else {"loaded": False}
    return {
        "status": "online" if recommend_func else "degraded",
        "engine": status,
        "supabase": supabase is not None,
        "cache_items": len(poster_cache)
    }



@app.get("/recommend")
@app.get("/api/recommend")
async def get_recommendations(movie: str = Query(..., description="The movie name")):
    if not recommend_func:
        raise HTTPException(status_code=503, detail="Recommendation engine not available")
    
    # Reload cache if it's empty
    if not poster_cache and supabase:
        refresh_poster_cache()

    try:
        results = recommend_func(movie)
        if not results:
            return {"movie": movie, "recommendations": []}

        # Enrich with posters using the robust local cache
        for res in results:

            name = res["name"]
            year = res.get("year")
            normalized_name = name.lower().strip()
            year_str = str(year) if year else ""
            
            # 1. Search for direct match in local cache
            poster = None
            if year_str:
                poster = poster_cache.get(f"{normalized_name}_{year_str}")
            
            # 2. Fallback to name-only match
            if not poster:
                entry = poster_cache.get(normalized_name)
                if isinstance(entry, dict):
                    poster = entry.get("poster")
            
            # 3. Clean and try again (Remove extra context and normalize characters)
            if not poster:
                raw_clean = re.sub(r'\(.*?\)', '', normalized_name).strip()
                raw_clean = re.sub(r'\s+\d{4}$', '', raw_clean).strip()
                match_clean = re.sub(r'[^a-z0-9]', '', raw_clean)
                
                if year_str:
                    poster = poster_cache.get(f"{raw_clean}_{year_str}") or poster_cache.get(f"{match_clean}_{year_str}")
                if not poster:
                    entry = poster_cache.get(raw_clean) or poster_cache.get(f"clean_{match_clean}")
                    if isinstance(entry, dict):
                        poster = entry.get("poster")


            # 4. Final: return None if no match. 
            # We removed fuzzy/substring matching because it was causing wrong images (e.g. Uyire Uyire matching Uyire).
            
            res["poster"] = poster


        
        return {"movie": movie, "recommendations": results}
    except Exception as e:
        logger.error(f"Recommendation failed for '{movie}': {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("uvicorn not installed, cannot run local server")
