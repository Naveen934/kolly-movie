from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from rec_movie import recommend
from supabase import create_client, Client
import uvicorn
import os

app = FastAPI()

# Supabase configuration
# Use environment variables if available (for Vercel/Production)
SUPA_URL = os.environ.get("SUPABASE_URL", "https://uuvkjqcnkgwhagpyfguz.supabase.co")
SUPA_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV1dmtqcWNua2d3aGFncHlmZ3V6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NzYzNTAsImV4cCI6MjA4OTU1MjM1MH0.ew3GkB6uB6egtx5lWYDFdcEKaTtRDMHZYFEXNin6RBg")

supabase: Client = create_client(SUPA_URL, SUPA_KEY)

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/recommend")
async def get_recommendations(movie: str = Query(..., description="The movie name to get recommendations for")):
    print(f"DEBUG: Received request for movie: {movie}") # fallback for quick check
    try:
        results = recommend(movie)
        print(f"DEBUG: Found {len(results)} recommendations")
        
        if not results:
            return {"movie": movie, "recommendations": []}
            
        # Enrich with posters from Supabase efficiently
        rec_names = [res["name"] for res in results]
        
        # Fetch posters only for the recommended movies
        # We use ilike for a more flexible match if needed, but 'in' is faster for exact matches
        response = supabase.table("tamil_movies")\
            .select("movie_name, poster")\
            .in_("movie_name", rec_names)\
            .execute()
            
        # Create a case-insensitive mapping from the fetched results
        poster_map = {item["movie_name"].lower().strip(): item["poster"] for item in response.data if item["movie_name"]}
        
        # If some posters are missing, try a broader search or simple fallback
        missing_names = [name for name in rec_names if name.lower().strip() not in poster_map]
        
        if missing_names:
            # Try to find movies that might have slightly different names (e.g., extra spaces or casing)
            # This is a bit more expensive but only done for missing ones
            for missing_name in missing_names:
                # Simple heuristic: look for movies starting with the name
                broad_res = supabase.table("tamil_movies")\
                    .select("movie_name, poster")\
                    .ilike("movie_name", f"%{missing_name}%")\
                    .execute()
                if broad_res.data:
                    for item in broad_res.data:
                        poster_map[missing_name.lower().strip()] = item["poster"]
                        break # Take the first match
        
        # Add posters to results
        for res in results:
            name_lower = res["name"].lower().strip()
            res["poster"] = poster_map.get(name_lower)
            
            # Final fallback: if still no poster, try fuzzy match in the local map (not database)
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
        
        print(f"DEBUG: Success returning {len(results)} results")
        return {"movie": movie, "recommendations": results}
    except Exception as e:
        print(f"DEBUG: ERROR in /recommend: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
