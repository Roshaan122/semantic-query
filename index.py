import json
import chromadb
from tqdm import tqdm

# ----- CONFIGURATION -----
EMBEDDED_DATA_PATH = "embedded_permits_local.json"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "permit_embeddings"

def get_chroma_client():
    """Get ChromaDB client and collection"""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Specify distance function
    )
    return client, collection

def index_embeddings():
    """Index permit embeddings into ChromaDB"""
    print("Starting ChromaDB indexing process...")
    
    # Connect to ChromaDB
    client, collection = get_chroma_client()
    print("Connected to ChromaDB.")
    
    # Load embedded data
    try:
        with open(EMBEDDED_DATA_PATH, 'r') as file:
            embedded_data = json.load(file)
        print(f"Loaded {len(embedded_data)} embedded records.")
    except Exception as e:
        raise RuntimeError(f"Failed to load embedded data: {e}")

    # Filter out incomplete embeddings
    valid_records = []
    for record in embedded_data:
        embedding = record.get("embedding", [])
        if len(embedding) == 384:  # Expected dimension for all-MiniLM-L6-v2
            valid_records.append(record)
        else:
            print(f"Skipping {record.get('permit_number', 'UNKNOWN')} - invalid embedding dimension: {len(embedding)}")
    
    print(f"Indexing {len(valid_records)} valid records into Chroma...")
    
    # Index each record
    for i, record in enumerate(tqdm(valid_records, desc="Indexing")):
        try:
            permit_id = record["permit_number"]
            embedding = record["embedding"]
            metadata = {
                "permit_number": permit_id,
                "permit_type": record.get("permit_type", "Unknown"),
                "calendar_year": int(record.get("calendar_year", 0))
            }

            collection.add(
                ids=[permit_id],
                embeddings=[embedding],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"Error indexing {record.get('permit_number', 'UNKNOWN')}: {e}")
    
    final_count = collection.count()
    print(f"Indexed {final_count} embeddings successfully!")
    
    # Test with a valid embedding
    if valid_records:
        print("\nRunning a test query with first valid embedding:")
        test_embedding = valid_records[0]["embedding"]
        results = collection.query(
            query_embeddings=[test_embedding],
            n_results=3
        )
        print(f"  Result 1: {results['metadatas']}")

def clear_index():
    """Clear all data from the ChromaDB collection"""
    print("Clearing ChromaDB index...")
    client, collection = get_chroma_client()
    
    # Get all IDs and delete them
    all_data = collection.get()
    if all_data['ids']:
        collection.delete(ids=all_data['ids'])
        print(f"Cleared {len(all_data['ids'])} records from ChromaDB.")
    else:
        print("ChromaDB collection was already empty.")

def get_collection_stats():
    """Get statistics about the ChromaDB collection"""
    client, collection = get_chroma_client()
    count = collection.count()
    print(f"📊 ChromaDB Collection Stats:")
    print(f"   - Total records: {count}")
    print(f"   - Collection name: {COLLECTION_NAME}")
    print(f"   - Database path: {CHROMA_DIR}")
    return count

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "clear":
            clear_index()
        elif command == "stats":
            get_collection_stats()
        elif command == "reindex":
            clear_index()
            index_embeddings()
        else:
            print("Usage: python index.py [clear|stats|reindex]")
            print("  clear    - Clear all data from ChromaDB")
            print("  stats    - Show collection statistics")
            print("  reindex  - Clear and rebuild the index")
            print("  (no args) - Just run indexing")
    else:
        index_embeddings()
