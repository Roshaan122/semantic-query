import json
import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from sentence_transformers import SentenceTransformer

# ----- CONFIGURATION -----
NORMALIZED_DATA_PATH = "normalized_permits.json"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "permit_embeddings"

# ----- FASTAPI INIT -----
app = FastAPI(
    title="Semantic Permit Search API",
    description="Search public permits semantically using embeddings and filters.",
    version="1.0.0"
)

# ----- LOAD MODEL -----
model = SentenceTransformer("all-MiniLM-L6-v2")
print("SentenceTransformer model loaded.")

# ----- CONNECT TO CHROMA -----
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
print("Connected to ChromaDB.")

# ----- LOAD DESCRIPTION MAPPING -----
def load_description_mapping() -> Dict[str, str]:
    """Load descriptions from normalized data for permit lookup"""
    try:
        with open(NORMALIZED_DATA_PATH, 'r') as file:
            normalized_data = json.load(file)
        mapping = {}
        for record in normalized_data:
            permit_number = record.get("permit_number", "")
            description = record.get("description", "")
            mapping[permit_number] = description
        print(f"Loaded {len(mapping)} permit descriptions.")
        return mapping
    except Exception as e:
        print(f"Could not load descriptions: {e}")
        return {}

# Global description mapping
DESCRIPTION_MAPPING = load_description_mapping()

# ----- Pydantic Schemas -----
class SearchFilters(BaseModel):
    permit_type: Optional[str] = Field(None, description="Type of permit (e.g., 'Plumbing Permit')")
    calendar_year: Optional[int] = Field(None, description="Year the permit was issued")

class SearchRequest(BaseModel):
    query: str
    filters: Optional[SearchFilters] = None

class SearchResult(BaseModel):
    permit_number: str
    permit_type: str
    description: str
    calendar_year: int
    similarity: float

class SearchResponse(BaseModel):
    results: List[SearchResult]

# ----- FastAPI Routes -----
@app.get("/healthz")
def health_check():
    return {"ok": True}

@app.get("/stats")
def collection_stats():
    """Get statistics about the ChromaDB collection"""
    count = collection.count()
    return {
        "total_permits": count,
        "collection_name": COLLECTION_NAME,
        "database_path": CHROMA_DIR
    }

@app.post("/search", response_model=SearchResponse)
def semantic_search(request: SearchRequest):
    """Search permits using semantic similarity"""
    query_embedding = model.encode(request.query).tolist()

    chroma_filters = {}
    if request.filters:
        if request.filters.permit_type:
            chroma_filters["permit_type"] = request.filters.permit_type
        if request.filters.calendar_year:
            chroma_filters["calendar_year"] = request.filters.calendar_year

    chroma_where = None
    if chroma_filters:
        filters_list = [{k: v} for k, v in chroma_filters.items()]
        chroma_where = filters_list[0] if len(filters_list) == 1 else {"$and": filters_list}

    print("\nSemantic Search Debug")
    print("Query:", request.query)
    print("Chroma where filter:", chroma_where)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            where=chroma_where,
            include=["metadatas", "distances"]
        )

        # Fallback: retry without filters if no match
        if not results["metadatas"] or not results["metadatas"][0]:
            print("No results with filters. Retrying without filters...")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["metadatas", "distances"]
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # Parse results
    hits = []
    for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
        permit_number = metadata["permit_number"]
        description = DESCRIPTION_MAPPING.get(permit_number, "No description available")
        
        hits.append(SearchResult(
            permit_number=permit_number,
            permit_type=metadata["permit_type"],
            description=description,
            calendar_year=metadata["calendar_year"],
            similarity=1 - distance
        ))

    return SearchResponse(results=hits)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)