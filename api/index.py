import sys
import os
import traceback
import logging

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
recommend = None
get_status = None
supabase = None
import_error = None

# Try to load engine
try:
    import rec_movie
    recommend = rec_movie.recommend
    get_status = rec_movie.get_status
    logger.info("Recommendation engine loaded successfully")
except Exception as e:
    import_error = str(e)
    logger.error(f"Engine import failed: {e}")
    get_status = lambda: {"loaded": False, "error": import_error}

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
    return {"message": "Movie Recommendation API is running", "engine": "numpy-ultralight"}

@app.get("/health")
@app.get("/api/health")
async def health_check():
    status = get_status() if get_status else {"loaded": False}
    return {
        "status": "online" if recommend else "degraded",
        "engine": status,
        "supabase": supabase is not None
    }

@app.get("/recommend")
@app.get("/api/recommend")
async def get_recommendations(movie: str = Query(..., description="The movie name")):
    if not recommend:
        raise HTTPException(status_code=503, detail="Recommendation engine not available")
    
    try:
        results = recommend(movie)
        if not results:
            return {"movie": movie, "recommendations": []}

        # Enrich with posters if supabase is available
        if supabase:
            try:
                rec_names = [res["name"] for res in results]
                response = supabase.table("tamil_movies").select("movie_name, poster").in_("movie_name", rec_names).execute()
                poster_map = {item["movie_name"].lower().strip(): item["poster"] for item in response.data}
                for res in results:
                    res["poster"] = poster_map.get(res["name"].lower().strip())
            except Exception as e:
                logger.error(f"Poster enrichment failed: {e}")
        
        return {"movie": movie, "recommendations": results}
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("uvicorn not installed, cannot run local server")
