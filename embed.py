import json
from sentence_transformers import SentenceTransformer

# File paths
INPUT_PATH = 'normalized_permits.json'
OUTPUT_PATH = 'embedded_permits_local.json'

# Load embedding model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("Model loaded successfully!")

# Load normalized data
try:
    with open(INPUT_PATH, 'r') as file:
        normalized_data = json.load(file)
    print(f"Loaded {len(normalized_data)} normalized records.")
except Exception as e:
    raise RuntimeError(f"Failed to load normalized data: {e}")

# Function to generate the embedding input string
def generate_embedding(record):
    text = (
        f"This is a {record.get('permit_class', {}).get('mapped', 'Unknown')} class "
        f"{record.get('permit_type', {}).get('description', 'Unknown')} permit for "
        f"{record.get('work_class', 'general')} work, issued in "
        f"{record.get('dates', {}).get('issued', '')[:4]}. "
        f"Location: {record.get('location', {}).get('address', 'unknown address')}, "
        f"{record.get('location', {}).get('city', '')}, {record.get('location', {}).get('state', '')} "
        f"{record.get('location', {}).get('zip', '')}. "
        f"Status: {record.get('status', {}).get('current', 'Unknown')}. "
        f"Description: {record.get('description', 'No description')}"
    )
    return model.encode(text.strip()).tolist()

# Generate embeddings
embedded_data = []
skipped = 0

for record in normalized_data:
    try:
        permit_number = record.get("permit_number")
        permit_type_desc = record.get("permit_type", {}).get("description")
        calendar_year = record.get("dates", {}).get("issued", "")[:4]
        description = record.get("description")

        if not permit_number or not permit_type_desc or not calendar_year or not description:
            print(f"Skipping record (missing fields): {permit_number}")
            skipped += 1
            continue

        embedding = generate_embedding(record)

        embedded_data.append({
            "permit_number": permit_number,
            "embedding": embedding,
            "permit_type": permit_type_desc,
            "calendar_year": int(calendar_year)
        })

    except Exception as e:
        print(f"Error processing record {record.get('permit_number', 'UNKNOWN')}: {e}")
        skipped += 1

# Save embeddings
try:
    with open(OUTPUT_PATH, 'w') as file:
        json.dump(embedded_data, file, indent=4)
    print(f"\nEmbedding complete. {len(embedded_data)} records saved to '{OUTPUT_PATH}'.")
    print(f"Skipped {skipped} record(s) due to missing data or errors.")
except Exception as e:
    raise RuntimeError(f"Failed to write embedded file: {e}")
