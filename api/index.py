import sys
import os
import traceback
import logging
from datetime import datetime, timedelta

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
    
    if url and key:
        supabase = create_client(url, key)
        logger.info(f"Supabase client initialized with URL: {url[:20]}...")
    else:
        logger.warning(f"Supabase credentials missing. URL present: {url is not None}, Key present: {key is not None}")
except Exception as e:
    logger.error(f"Supabase init failed: {e}")


def refresh_poster_cache():
    global poster_cache, last_cache_refresh
    if not supabase:
        return
    
    try:
        logger.info("Refreshing poster cache...")
        # Fetch all movies with years to handle duplicates (e.g. Vikram 1986 vs 2022)
        response = supabase.table("tamil_movies").select("movie_name, poster, release_year, year").execute()
        if response.data:
            # Map normalized name + year to poster URL
            # Also map normalized name to the LATEST poster for fallback
            new_cache = {}
            for item in response.data:
                name = item.get("movie_name")
                poster = item.get("poster")
                year = item.get("release_year") or item.get("year")
                
                if name and poster:
                    normalized_name = name.lower().strip()
                    year_str = str(int(float(year))) if year and not (isinstance(year, float) and np.isnan(year)) else ""
                    
                    # 1. Exact Name + Year match
                    if year_str:
                        new_cache[f"{normalized_name}_{year_str}"] = poster
                    
                    # 2. Latest/fallback for name-only
                    existing = new_cache.get(normalized_name)
                    if not existing or (year_str and year_str > existing.get("year", "")):
                        new_cache[normalized_name] = {"poster": poster, "year": year_str}
            
            poster_cache = new_cache
            last_cache_refresh = datetime.now()
            logger.info(f"Poster cache refreshed: {len(poster_cache)} entries")
    except Exception as e:
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
    return {
        "message": "Movie Recommendation API is running", 
        "engine": "numpy-ultralight",
        "cache_size": len(poster_cache),
        "last_refresh": str(last_cache_refresh)
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
        import re
        import numpy as np
        for res in results:
            name = res["name"]
            year = res.get("year")
            normalized_name = name.lower().strip()
            year_str = str(year) if year else ""
            
            # 1. Direct match with Year (Best)
            poster = None
            if year_str:
                poster = poster_cache.get(f"{normalized_name}_{year_str}")
            
            # 2. Direct match with Name only (Fallback to latest)
            if not poster:
                entry = poster_cache.get(normalized_name)
                if isinstance(entry, dict):
                    poster = entry.get("poster")
            
            # 3. Advanced match: strip brackets and try again
            if not poster:
                clean_name = re.sub(r'\(.*?\)', '', normalized_name).strip()
                clean_name = re.sub(r'\s+\d{4}$', '', clean_name).strip()
                
                if year_str:
                    poster = poster_cache.get(f"{clean_name}_{year_str}")
                if not poster:
                    entry = poster_cache.get(clean_name)
                    if isinstance(entry, dict):
                        poster = entry.get("poster")

            # 4. Final Substring fallback
            if not poster:
                clean_name = re.sub(r'\(.*?\)', '', normalized_name).strip()
                for key, val in poster_cache.items():
                    # Only check name-only keys in the cache for substring
                    if "_" not in key and isinstance(val, dict):
                        db_name = key
                        if clean_name in db_name or db_name in clean_name:
                            if len(clean_name) > 0.7 * len(db_name) or len(db_name) > 0.7 * len(clean_name):
                                poster = val.get("poster")
                                break
            
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
