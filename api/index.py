import sys
import os
import traceback

# Add the current directory to sys.path to ensure local imports work on Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
import sys
import logging

try:
    import uvicorn
except ImportError:
    uvicorn = None

# Ensure the 'api' directory is in the path so we can import rec_movie
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.append(api_dir)

try:
    import rec_movie
except ImportError:
    # Handle cases where rec_movie might be in current path instead of api.rec_movie
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import rec_movie

# Try to import recommend, but don't crash if it fails (so we can report the error via /health)
try:
    from rec_movie import recommend, get_status
    import_error = None
# Global engine state and error tracking
recommend_func = None
engine_import_error = None
engine_get_status_func = None

def load_engine():
    global recommend_func, engine_import_error, engine_get_status_func
    if recommend_func and engine_get_status_func: # Already loaded
        return

    try:
        import rec_movie
        recommend_func = rec_movie.recommend
        engine_get_status_func = rec_movie.get_status
        logger.info("Recommendation engine (rec_movie) loaded successfully.")
    except Exception as e:
        engine_import_error = str(e)
        recommend_func = None
        engine_get_status_func = lambda: {"error": f"Engine import failed: {str(e)}", "traceback": traceback.format_exc()}
        logger.error(f"Failed to load rec_movie engine: {e}", exc_info=True)

# Attempt to load the engine at startup
load_engine()

# Initialize Supabase with safety guards
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("SUPABASE_URL or SUPABASE_KEY missing in environment variables. Supabase client not initialized.")

app = FastAPI()

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api")
async def root():
    """Debug root to check if API is reachable"""
    return {"message": "Movie Recommendation API is running", "endpoints": ["/health", "/recommend"]}

@app.get("/health")
@app.get("/api/health")
async def health():
    """Check the status of the API and recommendation engine"""
    status = get_status()
    return {
        "status": "online" if not import_error else "degraded",
        "import_error": import_error,
        "engine": status
    }

@app.get("/recommend")
@app.get("/api/recommend")
async def get_recommendations(movie: str = Query(..., description="The movie name to get recommendations for")):
    print(f"DEBUG: Received request for movie: {movie}")
    
    if recommend is None:
        return {"error": "Recommendation engine failed to load", "details": import_error}
        
    try:
        results = recommend(movie)
        print(f"DEBUG: Found {len(results)} recommendations")
        
        if not results:
            return {"movie": movie, "recommendations": []}
            
        # Enrich with posters from Supabase efficiently
        rec_names = [res["name"] for res in results]
        
        response = supabase.table("tamil_movies")\
            .select("movie_name, poster")\
            .in_("movie_name", rec_names)\
            .execute()
            
        poster_map = {item["movie_name"].lower().strip(): item["poster"] for item in response.data if item["movie_name"]}
        
        # If some posters are missing, try a broader search or simple fallback
        missing_names = [name for name in rec_names if name.lower().strip() not in poster_map]
        
        if missing_names:
            for missing_name in missing_names:
                broad_res = supabase.table("tamil_movies")\
                    .select("movie_name, poster")\
                    .ilike("movie_name", f"%{missing_name}%")\
                    .execute()
                if broad_res.data:
                    for item in broad_res.data:
                        poster_map[missing_name.lower().strip()] = item["poster"]
                        break
        
        # Add posters to results
        for res in results:
            name_lower = res["name"].lower().strip()
            res["poster"] = poster_map.get(name_lower)
            
            if not res["poster"]:
                 best_score = 0
                 best_p = None
                 for m_name, p_url in poster_map.items():
                     if name_lower in m_name or m_name in name_lower:
                         overlap = min(len(name_lower), len(m_name)) / max(len(name_lower), len(m_name))
                         if overlap > best_score:
                             best_score = overlap
                             best_p = p_url
                 
                 if best_score > 0.7:
                     res["poster"] = best_p
        
        return {"movie": movie, "recommendations": results}
    except Exception as e:
        print(f"DEBUG: ERROR in /recommend: {str(e)}")
        return {"error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
