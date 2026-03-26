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
            
        # Enrich with posters from Supabase (handling 1000-row limit)
        all_posters = []
        page = 0
        chunk_size = 1000
        while True:
            response = supabase.table("tamil_movies")\
                .select("movie_name, poster")\
                .range(page * chunk_size, (page + 1) * chunk_size - 1)\
                .execute()
            if not response.data:
                break
            all_posters.extend(response.data)
            if len(response.data) < chunk_size:
                break
            page += 1
        
        # Create a case-insensitive mapping
        poster_map = {item["movie_name"].lower().strip(): item["poster"] for item in all_posters if item["movie_name"]}
        
        # Add posters to results
        for res in results:
            name_lower = res["name"].lower().strip()
            # 1. Exact case-insensitive match
            res["poster"] = poster_map.get(name_lower)
            
            # 2. Heuristic fallback (only if no exact match)
            if not res["poster"]:
                 best_score = 0
                 best_p = None
                 for m_name, p_url in poster_map.items():
                     # Check if one contains the other
                     if name_lower == m_name: # redundant but safe
                         res["poster"] = p_url
                         break
                     if name_lower in m_name or m_name in name_lower:
                         # Calculate intersection score based on length
                         overlap = min(len(name_lower), len(m_name)) / max(len(name_lower), len(m_name))
                         if overlap > best_score:
                             best_score = overlap
                             best_p = p_url
                 
                 # Only use fallback if it's at least 70% similar in length/title
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
