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
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        supabase = create_client(url, key)
        logger.info("Supabase client initialized")
    else:
        logger.warning("Supabase credentials missing")
except Exception as e:
    logger.error(f"Supabase init failed: {e}")

def refresh_poster_cache():
    global poster_cache, last_cache_refresh
    if not supabase:
        return
    
    try:
        logger.info("Refreshing poster cache...")
        # Fetch all movies to handle naming mismatches robustly
        response = supabase.table("tamil_movies").select("movie_name, poster").execute()
        if response.data:
            # Map normalized name (lower + strip) to poster URL
            new_cache = {}
            for item in response.data:
                name = item.get("movie_name")
                poster = item.get("poster")
                if name:
                    normalized_name = name.lower().strip()
                    new_cache[normalized_name] = poster
            
            poster_cache = new_cache
            last_cache_refresh = datetime.now()
            logger.info(f"Poster cache refreshed: {len(poster_cache)} items")
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
        for res in results:
            name = res["name"]
            normalized_name = name.lower().strip()
            
            # 1. Direct normalized match
            poster = poster_cache.get(normalized_name)
            
            # 2. Advanced match: strip year from name if present and try again
            if not poster:
                clean_name = re.sub(r'\(.*?\)', '', normalized_name).strip()
                clean_name = re.sub(r'\s+\d{4}$', '', clean_name).strip()
                poster = poster_cache.get(clean_name)

            # 3. Fallback: Check if rec name is a substring of any DB name or vice-versa
            if not poster:
                for db_name, poster_url in poster_cache.items():
                    if clean_name in db_name or db_name in clean_name:
                        # 70% overlap threshold simplified
                        if len(clean_name) > 0.7 * len(db_name) or len(db_name) > 0.7 * len(clean_name):
                            poster = poster_url
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
